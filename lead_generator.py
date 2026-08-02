import os
import re
import sys
import json
import time
import gc
import shutil
import random
import urllib.parse
from urllib.parse import urlparse
from datetime import datetime
import requests
import urllib3
from bs4 import BeautifulSoup
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import config
import logger
import validator
import database.db as db
import dashboard
import antidetect

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Disable SSL verification warnings for legacy/untrusted business websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ==========================================
# CONFIGURATION LOADERS
# ==========================================
def load_list_from_file(filename, default_list):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                items = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                if items:
                    return items
        except Exception:
            pass
    return default_list

CATEGORIES = load_list_from_file(config.CATEGORIES_FILE, ["Furniture Store", "Gift Shop", "Sports Store", "Hotel"])
LOCATIONS = load_list_from_file(config.LOCATIONS_FILE, ["Chennai, Tamil Nadu", "Hyderabad, Telangana", "Bengaluru, Karnataka"])


# ==========================================
# ATOMIC WRITING & AUTO BACKUP
# ==========================================
def atomic_write_json(filepath, data):
    tmp_path = filepath + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, filepath)

def atomic_write_excel(df, filepath):
    tmp_path = filepath + ".tmp.xlsx"
    df.to_excel(tmp_path, index=False)
    os.replace(tmp_path, filepath)

def create_auto_backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        if os.path.exists(config.PROGRESS_FILE):
            shutil.copy2(config.PROGRESS_FILE, os.path.join(config.BACKUPS_DIR, f"progress_{ts}.json"))
        if os.path.exists(config.EXCEL_ALL):
            shutil.copy2(config.EXCEL_ALL, os.path.join(config.BACKUPS_DIR, f"all_leads_{ts}.xlsx"))

        # Prune old backups keeping latest 10 sets
        prog_backups = sorted([os.path.join(config.BACKUPS_DIR, f) for f in os.listdir(config.BACKUPS_DIR) if f.startswith("progress_")], reverse=True)
        for old_b in prog_backups[10:]:
            try:
                os.remove(old_b)
                excel_b = old_b.replace("progress_", "all_leads_").replace(".json", ".xlsx")
                if os.path.exists(excel_b):
                    os.remove(excel_b)
            except Exception:
                pass
    except Exception as e:
        print(f"Backup Notice: {e}", flush=True)


# ==========================================
# STRICT EMAIL FILTER & VALIDATOR
# ==========================================
def is_valid_business_email(email):
    if not email or '@' not in email:
        return False
    em = email.lower().strip()

    rejected_domains = [
        "example.com", "example.org", "domain.com", "email.com", "sample.com",
        "sentry.io", "wixpress.com", "bugsnag.com", "rollbar.com", "schema.org",
        "gravatar.com", "wordpress.org", "w.org", "jquery.com", "bootstrap.com"
    ]
    rejected_prefixes = [
        "example@", "test@", "placeholder@", "yourname@", "username@",
        "admin@example", "info@example", "user@", "name@"
    ]

    if any(em.endswith("@" + d) or ("@" + d) in em for d in rejected_domains):
        return False
    if any(em.startswith(p) for p in rejected_prefixes):
        return False

    if any(bad in em for bad in ["u003e", "u0026", "%", "\\", "..", "http", "www", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js"]):
        return False

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', em):
        return False

    return True


def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)[:50]

def is_matching_domain(email, website_url, business_name):
    if not email or '@' not in email:
        return True
    email_domain = email.split('@')[-1].lower()
    if not website_url:
        return False
    web_domain = urlparse(website_url).netloc.lower().replace('www.', '')
    
    if email_domain == web_domain or email_domain.endswith('.' + web_domain) or web_domain.endswith('.' + email_domain):
        return True
    
    if any(pub in email_domain for pub in ['gmail.com', 'yahoo.', 'hotmail.com', 'outlook.com', 'icloud.com', 'zoho.com']):
        return True
        
    return False

def classify_business_type(name, website, notes):
    text = f"{name} {website} {notes}".lower()
    chains = [
        "pepperfry", "home centre", "nilkamal", "godrej interio", "wooden street", "royaloak",
        "urban ladder", "durian", "featherlite", "damro", "stanley", "sleepwell", "wakefit", "kurlon",
        "apollo pharmacy", "medplus", "dominos", "pizza hut", "mcdonalds", "kfc", "starbucks", "saravana stores"
    ]
    corporates = ["godrej", "tata", "reliance", "birlacorp", "wipro", "infosys", "mahindra", "l&t", "aditya birla"]
    franchises = ["franchise", "outlet", "authorized dealer", "authorised dealer", "exclusive store", "experience centre", "experience center"]

    if any(c in text for c in chains):
        return "Chain Store"
    elif any(c in text for c in corporates):
        return "Corporate"
    elif any(f in text for f in franchises):
        return "Franchise"
    elif name and name != "Unknown Business":
        return "Local Shop"
    return "Unknown"

def validate_lead(lead):
    name = lead.get("Business Name", "").strip()
    link = lead.get("Google Maps Link", "").strip()
    notes = lead.get("Notes", "")

    if not name or name == "Unknown Business" or "Extraction failed" in notes:
        return False
    if not link or not (link.startswith("http://") or link.startswith("https://")):
        return False
    return True

def restore_from_backup():
    try:
        prog_backups = sorted([os.path.join(config.BACKUPS_DIR, f) for f in os.listdir(config.BACKUPS_DIR) if f.startswith("progress_")], reverse=True)
        if prog_backups:
            latest_prog = prog_backups[0]
            latest_excel = latest_prog.replace("progress_", "all_leads_").replace(".json", ".xlsx")
            print(f"Restoring progress from backup: {latest_prog}", flush=True)
            shutil.copy2(latest_prog, config.PROGRESS_FILE)
            if os.path.exists(latest_excel):
                shutil.copy2(latest_excel, config.EXCEL_ALL)
            with open(config.PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error restoring backup: {e}", flush=True)
    return None

def load_progress():
    state = None
    if os.path.exists(config.PROGRESS_FILE):
        try:
            with open(config.PROGRESS_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except Exception:
            print("WARNING: Checkpoint mismatch or corruption detected. Using latest valid backup.", flush=True)
            state = restore_from_backup()

    if not state:
        state = {
            "searches_completed": 0,
            "current_category": "",
            "current_location": "",
            "current_business_index": 0,
            "processed_urls": [],
            "completed_batches": [],
            "runtime_started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_checkpoint": "",
            "total_businesses_seen": 0,
            "total_exported": 0,
            "duplicates_skipped": 0,
            "runtime_today_seconds": 0,
            "runtime_total_seconds": 0,
            "avg_businesses_per_hour": 0.0,
            "avg_contacts_per_hour": 0.0,
            "all_leads": [],
            "failed_leads": [],
            "duplicates": [],
            "summary_records": []
        }
    else:
        # Guarantee every statistics key exists for backward compatibility with older progress.json files
        state.setdefault("searches_completed", len(state.get("completed_batches", [])))
        state.setdefault("current_category", "")
        state.setdefault("current_location", "")
        state.setdefault("current_business_index", 0)
        state.setdefault("processed_urls", [])
        state.setdefault("completed_batches", [])
        state.setdefault("runtime_started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        state.setdefault("last_checkpoint", "")
        state.setdefault("total_businesses_seen", 0)
        state.setdefault("total_exported", 0)
        state.setdefault("duplicates_skipped", 0)
        state.setdefault("runtime_today_seconds", 0)
        state.setdefault("runtime_total_seconds", 0)
        state.setdefault("avg_businesses_per_hour", 0.0)
        state.setdefault("avg_contacts_per_hour", 0.0)
        state.setdefault("all_leads", [])
        state.setdefault("failed_leads", [])
        state.setdefault("duplicates", [])
        state.setdefault("summary_records", [])

        # Sync loaded progress leads into SQLite Master DB
        for lead in state.get("all_leads", []):
            if validate_lead(lead):
                cleaned = validator.process_raw_lead(lead)
                db.save_business_to_db(cleaned)

    return state

def save_progress(state, current_cat="", current_loc="", business_index=0, session_runtime_sec=0):
    if current_cat:
        state["current_category"] = current_cat
    if current_loc:
        state["current_location"] = current_loc
    if business_index:
        state["current_business_index"] = business_index

    state["last_checkpoint"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["total_exported"] = len(state.get("all_leads", []))
    state["duplicates_skipped"] = len(state.get("duplicates", []))
    state["total_businesses_seen"] = state["total_exported"] + state["duplicates_skipped"] + len(state.get("failed_leads", []))

    state["runtime_today_seconds"] = state.get("runtime_today_seconds", 0) + session_runtime_sec
    state["runtime_total_seconds"] = state.get("runtime_total_seconds", 0) + session_runtime_sec

    hours = max(state["runtime_total_seconds"] / 3600.0, 0.01)
    state["avg_businesses_per_hour"] = round(state["total_businesses_seen"] / hours, 1)

    contacts_found = sum(1 for lead in state.get("all_leads", []) if lead.get("Phone") or lead.get("Email"))
    state["avg_contacts_per_hour"] = round(contacts_found / hours, 1)

    atomic_write_json(config.PROGRESS_FILE, state)

def export_results(state):
    columns = [
        "Business Name", "Source Category", "Category", "Search Location", "Location", "Address", "Phone",
        "Website", "Email", "WhatsApp", "Facebook", "Instagram",
        "LinkedIn", "Twitter/X", "Contact Form", "Rating", "Reviews",
        "Opening Hours", "Google Maps Link", "Website Status", "Business Type", "Notes",
        "Priority", "Last Verified", "Contacted", "Contact Date", "Response", "Remarks"
    ]

    try:
        # Save all_leads.xlsx (Only valid leads)
        valid_leads = [lead for lead in state["all_leads"] if validate_lead(lead)]
        df_all = pd.DataFrame(valid_leads)
        if not df_all.empty:
            for col in columns:
                if col not in df_all.columns:
                    df_all[col] = ""
            df_all = df_all[columns]
        else:
            df_all = pd.DataFrame(columns=columns)
        atomic_write_excel(df_all, config.EXCEL_ALL)

        # Save failed_leads.xlsx
        failed_list = state["failed_leads"] + [lead for lead in state["all_leads"] if not validate_lead(lead) and lead not in state["failed_leads"]]
        df_failed = pd.DataFrame(failed_list)
        if not df_failed.empty:
            for col in columns:
                if col not in df_failed.columns:
                    df_failed[col] = ""
            df_failed = df_failed[columns]
        else:
            df_failed = pd.DataFrame(columns=columns)
        atomic_write_excel(df_failed, config.EXCEL_FAILED)

        # Save duplicates.xlsx
        df_dup = pd.DataFrame(state["duplicates"])
        if not df_dup.empty:
            for col in columns:
                if col not in df_dup.columns:
                    df_dup[col] = ""
            df_dup = df_dup[columns]
        else:
            df_dup = pd.DataFrame(columns=columns)
        atomic_write_excel(df_dup, config.EXCEL_DUPLICATES)

        # Save summary.xlsx dynamically grouped from all_leads
        summary_rows = []
        if state["all_leads"]:
            df_leads = pd.DataFrame(state["all_leads"])
            if "Source Category" in df_leads.columns and "Search Location" in df_leads.columns:
                grouped = df_leads.groupby(["Source Category", "Search Location"])
                for (cat, loc), group in grouped:
                    valid_count = sum(1 for _, r in group.iterrows() if validate_lead(r))
                    summary_rows.append({
                        "Category": cat,
                        "Location": loc,
                        "Businesses Found": len(group),
                        "Successful": valid_count,
                        "Failed": len(group) - valid_count,
                        "Websites": sum(1 for _, r in group.iterrows() if r.get("Website")),
                        "Phones": sum(1 for _, r in group.iterrows() if r.get("Phone")),
                        "Emails": sum(1 for _, r in group.iterrows() if r.get("Email")),
                        "WhatsApp": sum(1 for _, r in group.iterrows() if r.get("WhatsApp")),
                        "Facebook": sum(1 for _, r in group.iterrows() if r.get("Facebook")),
                        "Instagram": sum(1 for _, r in group.iterrows() if r.get("Instagram")),
                        "LinkedIn": sum(1 for _, r in group.iterrows() if r.get("LinkedIn")),
                        "Manual Review": sum(1 for _, r in group.iterrows() if "Manual review" in str(r.get("Notes", "")))
                    })
        sum_cols = ["Category", "Location", "Businesses Found", "Successful", "Failed", "Websites", "Phones", "Emails", "WhatsApp", "Facebook", "Instagram", "LinkedIn", "Manual Review"]
        df_sum = pd.DataFrame(summary_rows)
        if not df_sum.empty:
            for col in sum_cols:
                if col not in df_sum.columns:
                    df_sum[col] = 0
            df_sum = df_sum[sum_cols]
        else:
            df_sum = pd.DataFrame(columns=sum_cols)
        atomic_write_excel(df_sum, config.EXCEL_SUMMARY)

        create_auto_backup()
        db.create_db_snapshot()
        dashboard.generate_all_dashboards()

    except Exception as e:
        print(f"Warning: Could not write Excel files: {e}", flush=True)

    # Save leads.txt
    try:
        txt_tmp = config.TXT_LEADS + ".tmp"
        with open(txt_tmp, 'w', encoding='utf-8') as f:
            for lead in state["all_leads"]:
                if not validate_lead(lead):
                    f.write(f"{lead.get('Business Name', '')}\n")
                    f.write(f"{lead.get('Google Maps Link', '')}\n")
                    f.write("Extraction Failed\n")
                    f.write("----------------------------------------\n\n")
                else:
                    f.write(f"{lead.get('Business Name', '')}\n\n")
                    f.write(f"{lead.get('Address', '')}\n\n")
                    f.write(f"{lead.get('Google Maps Link', '')}\n\n")
                    f.write(f"{lead.get('Phone', '')}\n\n")
                    f.write(f"{lead.get('Website', '')}\n\n")
                    f.write(f"{lead.get('Email', '')}\n\n")
                    f.write("----------------------------------------\n\n")
        os.replace(txt_tmp, config.TXT_LEADS)
    except Exception as e:
        print(f"Warning: Could not write txt file: {e}", flush=True)


# ==========================================
# WEBSITE ENRICHMENT WITH SUBPAGE CRAWL
# ==========================================
def enrich_website_data(website_url, business_name):
    result = {
        "Website Status": "No Website",
        "Email": "",
        "WhatsApp": "",
        "Facebook": "",
        "Instagram": "",
        "LinkedIn": "",
        "Twitter/X": "",
        "Contact Form": "",
        "Third Party Email": False
    }

    if not website_url or website_url.strip() == "":
        return result

    url = website_url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    subpages_to_check = ["/contact", "/contact-us", "/about", "/about-us", "/privacy"]

    try:
        resp = requests.get(url, headers=headers, timeout=8, verify=False)
        if resp.status_code == 200:
            result["Website Status"] = "Working"
            html_content = resp.text

            # Cache HTML
            safe_domain = sanitize_filename(urlparse(url).netloc or business_name)
            cache_filepath = os.path.join(config.CACHE_DIR, f"{safe_domain}.html")
            try:
                with open(cache_filepath, 'w', encoding='utf-8', errors='ignore') as cf:
                    cf.write(html_content)
            except Exception:
                pass

            soup = BeautifulSoup(html_content, 'html.parser')

            def extract_emails(sp, text):
                found = set()
                for mailto in sp.select('a[href^="mailto:"]'):
                    href = mailto.get('href', '')
                    clean_email = href.replace('mailto:', '').split('?')[0].strip()
                    if clean_email and is_valid_business_email(clean_email):
                        found.add(clean_email)
                if not found:
                    raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                    for em in raw_emails:
                        if is_valid_business_email(em):
                            found.add(em)
                return list(found)

            emails = extract_emails(soup, html_content)

            # Extract Social & Contact Links
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                href_lower = href.lower()

                if 'wa.me' in href_lower or 'api.whatsapp.com' in href_lower or 'whatsapp:' in href_lower:
                    if not result["WhatsApp"]:
                        result["WhatsApp"] = href

                if 'facebook.com' in href_lower and 'sharer' not in href_lower:
                    if not result["Facebook"]:
                        result["Facebook"] = href

                if 'instagram.com' in href_lower:
                    if not result["Instagram"]:
                        result["Instagram"] = href

                if 'linkedin.com' in href_lower:
                    if not result["LinkedIn"]:
                        result["LinkedIn"] = href

                if ('twitter.com' in href_lower or 'x.com' in href_lower) and 'intent' not in href_lower:
                    if not result["Twitter/X"]:
                        result["Twitter/X"] = href

                if any(k in href_lower for k in ['/contact', 'contact-us', 'get-in-touch', 'reach-us']):
                    if not result["Contact Form"]:
                        result["Contact Form"] = href if href.startswith('http') else urllib.parse.urljoin(url, href)

            if not result["Contact Form"]:
                if soup.find('form', attrs={'action': re.compile(r'contact', re.I)}) or soup.find('input', attrs={'type': 'email'}):
                    result["Contact Form"] = url

            # Subpage email crawl fallback
            if not emails:
                for subp in subpages_to_check:
                    sub_url = urllib.parse.urljoin(url, subp)
                    try:
                        sub_resp = requests.get(sub_url, headers=headers, timeout=5, verify=False)
                        if sub_resp.status_code == 200:
                            sub_soup = BeautifulSoup(sub_resp.text, 'html.parser')
                            sub_emails = extract_emails(sub_soup, sub_resp.text)
                            if sub_emails:
                                emails = sub_emails
                                break
                    except Exception:
                        pass

            if emails:
                chosen_email = emails[0]
                result["Email"] = chosen_email
                if not is_matching_domain(chosen_email, url, business_name):
                    result["Third Party Email"] = True

        else:
            result["Website Status"] = f"Broken ({resp.status_code})"

    except requests.exceptions.SSLError:
        result["Website Status"] = "SSL Error"
    except requests.exceptions.Timeout:
        result["Website Status"] = "Timeout"
    except Exception:
        result["Website Status"] = "Broken"

    return result


# ==========================================
# PLACE DETAILS DOM EXTRACTOR
# ==========================================
def extract_place_details(page, default_category):
    try:
        page.wait_for_selector("h1, div[role='main']", timeout=10000)
    except Exception:
        pass

    # 1. Business Name
    name = ""
    for sel in ["h1.DUwDvf", "h1.fontHeadlineLarge", "h1", "div.fontHeadlineLarge"]:
        el = page.query_selector(sel)
        if el and el.inner_text().strip():
            name = el.inner_text().strip()
            break
    if not name:
        try:
            title = page.title()
            name = title.split(" - ")[0].strip() if title else "Unknown Business"
        except Exception:
            name = "Unknown Business"

    # 2. Category
    cat_val = default_category
    for sel in ["button[jsaction*='category']", "button.Dkftq", "span.fontBodyMedium button"]:
        el = page.query_selector(sel)
        if el and el.inner_text().strip():
            cat_val = el.inner_text().strip()
            break

    # 3. Address
    address = ""
    for sel in ["button[data-item-id='address']", "button[aria-label*='Address:']", "div[aria-label*='Address:']", "button[aria-label*='address']"]:
        el = page.query_selector(sel)
        if el:
            txt = el.get_attribute("aria-label") or el.inner_text()
            if txt:
                address = txt.replace("Address:", "").replace('\ue0c8', '').strip()
                break

    # 4. Phone
    phone = ""
    for sel in ["button[data-item-id^='phone:tel:']", "button[aria-label*='Phone:']", "div[aria-label*='Phone:']", "a[href^='tel:']"]:
        el = page.query_selector(sel)
        if el:
            txt = el.get_attribute("aria-label") or el.get_attribute("href") or el.inner_text()
            if txt:
                phone = txt.replace("Phone:", "").replace("tel:", "").replace('\ue0cd', '').strip()
                break

    # 5. Website
    website = ""
    for sel in ["a[data-item-id='authority']", "a[aria-label*='Website:']", "a[aria-label*='website']", "a[data-tooltip*='website']"]:
        el = page.query_selector(sel)
        if el:
            website = el.get_attribute("href") or ""
            if website:
                break

    # 6. Rating & Reviews
    rating = ""
    for sel in ["div.F7L825", "span.ceNzR", "span[aria-label*='stars']", "div[role='img'][aria-label*='stars']", "span.MW4350"]:
        el = page.query_selector(sel)
        if el:
            txt = el.get_attribute("aria-label") or el.inner_text().strip()
            match = re.search(r'([\d\.]+)', txt)
            if match and float(match.group(1)) <= 5.0:
                rating = match.group(1)
                break

    reviews = ""
    for sel in ["button[aria-label*='reviews']", "span[aria-label*='reviews']", "button[jsaction*='review']"]:
        el = page.query_selector(sel)
        if el:
            txt = el.get_attribute("aria-label") or el.inner_text().strip()
            match = re.search(r'([\d,]+)', txt)
            if match:
                reviews = match.group(1).replace(',', '')
                break

    # Nudge Rating if reviews exist but rating is blank
    if reviews and not rating:
        try:
            r_el = page.query_selector("div.fontBodyMedium span[aria-hidden='true']")
            if r_el:
                txt = r_el.inner_text().strip()
                match = re.search(r'([\d\.]+)', txt)
                if match and float(match.group(1)) <= 5.0:
                    rating = match.group(1)
        except Exception:
            pass

    # 7. Opening Hours
    hours = ""
    for sel in ["button[data-item-id='oh']", "div[aria-label*='Hours']", "button[aria-label*='Open']", "button[aria-label*='Closed']", "div.t33v2"]:
        el = page.query_selector(sel)
        if el:
            hours = el.get_attribute("aria-label") or el.inner_text().strip()
            if hours:
                break

    return {
        "name": name,
        "category": cat_val,
        "address": address,
        "phone": phone,
        "website": website,
        "rating": rating,
        "reviews": reviews,
        "hours": hours
    }


# ==========================================
# MAIN SCRAPING LOGIC WITH TIMED CHECKPOINT
# ==========================================
def scrape_google_maps():
    db.init_db()
    logger.info("scraper", "Starting Google Maps lead generator session...")
    state = load_progress()
    processed_urls_set = set(state.get("processed_urls", []))
    completed_batches_set = set(state.get("completed_batches", []))
    today_date = datetime.now().strftime("%Y-%m-%d")
    start_time = time.time()

    category_stats = {}

    # Map existing records to check for duplicates
    existing_links = set(lead.get("Google Maps Link", "") for lead in state.get("all_leads", []) if lead.get("Google Maps Link"))
    existing_phones = set(lead.get("Phone", "") for lead in state.get("all_leads", []) if lead.get("Phone"))
    existing_names_addresses = set(f"{lead.get('Business Name', '')}|{lead.get('Address', '')}" for lead in state.get("all_leads", []))

    time_limit_hit = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.HEADLESS, args=["--start-maximized"])
            vp = antidetect.get_random_viewport()
            ua = antidetect.get_random_user_agent()
            context = browser.new_context(viewport=vp, user_agent=ua)
            page = context.new_page()
            pacing_engine = antidetect.AdaptivePacingEngine()

            total_counter = len(state.get("all_leads", [])) + len(state.get("failed_leads", []))

            for category in CATEGORIES:
                if time_limit_hit:
                    break

                for location in LOCATIONS:
                    if time_limit_hit:
                        break

                    batch_key = f"{category}|{location}"
                    if batch_key in completed_batches_set:
                        continue

                    query = f"{category} in {location}"
                    print(f"\n========================================", flush=True)
                    print(f"SEARCHING: {query}", flush=True)
                    print(f"========================================", flush=True)

                    search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
                    try:
                        page.goto(search_url, timeout=35000)
                        page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"Failed to load search page for {query}: {e}", flush=True)
                        continue

                    # Dismiss consent dialogs if present
                    for consent_btn in ["button:has-text('Accept all')", "button:has-text('I agree')", "form[action*='consent'] button"]:
                        try:
                            if page.is_visible(consent_btn):
                                page.click(consent_btn, timeout=2000)
                                page.wait_for_timeout(1000)
                        except Exception:
                            pass

                    # Verify feed or search input
                    try:
                        page.wait_for_selector("a[href*='/maps/place/'], div[role='feed']", timeout=12000)
                    except PlaywrightTimeoutError:
                        print(f"Checking search input for {query}...", flush=True)
                        try:
                            search_input = page.query_selector("input#searchboxinput")
                            if search_input:
                                search_input.fill(query)
                                page.keyboard.press("Enter")
                                page.wait_for_timeout(4000)
                        except Exception:
                            pass

                    try:
                        page.wait_for_selector("a[href*='/maps/place/'], div[role='feed']", timeout=10000)
                    except PlaywrightTimeoutError:
                        print(f"No result feed found for query: {query}", flush=True)
                        state["searches_completed"] = state.get("searches_completed", 0) + 1
                        completed_batches_set.add(batch_key)
                        state["completed_batches"] = list(completed_batches_set)
                        save_progress(state, category, location, total_counter, int(time.time() - start_time))
                        continue

                    collected_place_urls = []
                    last_count = 0
                    same_count_retries = 0

                    print("Scrolling for results...", flush=True)
                    while len(collected_place_urls) < config.MAX_LEADS_PER_LOCATION and same_count_retries < 5:
                        anchors = page.query_selector_all("a[href*='/maps/place/']")
                        for a in anchors:
                            href = a.get_attribute("href")
                            if href and href not in collected_place_urls:
                                collected_place_urls.append(href)
                                if len(collected_place_urls) >= config.MAX_LEADS_PER_LOCATION:
                                    break

                        print(f"  --> Found {len(collected_place_urls)} links so far...", flush=True)

                        page.evaluate("""
                            const feed = document.querySelector("div[role='feed']");
                            if (feed) {
                                feed.scrollBy(0, 1000);
                            } else {
                                window.scrollBy(0, 1000);
                            }
                        """)
                        page.wait_for_timeout(1500)

                        if len(collected_place_urls) == last_count:
                            same_count_retries += 1
                        else:
                            same_count_retries = 0
                            last_count = len(collected_place_urls)

                    print(f"Found {len(collected_place_urls)} place links for {query}.", flush=True)

                    batch_successful = 0
                    batch_duplicates = 0
                    batch_failed = 0
                    batch_websites = 0
                    batch_phones = 0
                    batch_emails = 0
                    batch_whatsapp = 0
                    batch_facebook = 0
                    batch_instagram = 0
                    batch_linkedin = 0
                    batch_manual_review = 0

                    # Process place links with item-level granular resume
                    last_idx = db.get_last_resume_index(category, location)
                    if last_idx > 0:
                        logger.info("scraper", f"[RESUME] Batch '{category} in {location}' resuming after business item #{last_idx}")

                    for place_idx, place_url in enumerate(collected_place_urls):
                        if place_url in processed_urls_set or db.is_url_processed_in_db(place_url):
                            continue

                        total_counter += 1
                        random_delay = random.uniform(config.RANDOM_DELAY_MIN, config.RANDOM_DELAY_MAX)
                        time.sleep(random_delay)

                        # Garbage collection & RAM cleanup every 50 items
                        if total_counter % 50 == 0:
                            gc.collect()

                        # Navigate directly to place URL
                        try:
                            page.goto(place_url, timeout=25000)
                            page.wait_for_timeout(2000)
                        except Exception:
                            pass

                        # Extract Business Details
                        try:
                            extracted = extract_place_details(page, category)
                            name = extracted["name"]
                            print(f"\n[{total_counter}] {name}", flush=True)

                            raw_web = extracted["website"]
                            is_social = False
                            social_detected_url = ""
                            social_detected_key = ""

                            for s_dom, s_key in [("instagram.com", "Instagram"), ("facebook.com", "Facebook"), ("twitter.com", "Twitter/X"), ("x.com", "Twitter/X"), ("linkedin.com", "LinkedIn")]:
                                if s_dom in raw_web.lower():
                                    is_social = True
                                    social_detected_url = raw_web
                                    social_detected_key = s_key
                                    break

                            if is_social:
                                official_website = ""
                                web_status = "No Website"
                            else:
                                official_website = raw_web

                            print(f"Phone {'[YES]' if extracted['phone'] else '[NO]'}", flush=True)
                            print(f"Website {'[YES]' if official_website else '[NO]'}", flush=True)

                            # Website Enrichment
                            enriched = enrich_website_data(official_website, name)
                            print(f"Email {'[YES]' if enriched['Email'] else '[NO]'}", flush=True)

                            if is_social:
                                enriched["Website Status"] = "No Website"
                                if social_detected_key and not enriched[social_detected_key]:
                                    enriched[social_detected_key] = social_detected_url

                            # Classify Business Type
                            biz_type = classify_business_type(name, official_website, "")

                            # Priority Scoring
                            phone_val = extracted["phone"]
                            email_val = enriched["Email"]

                            if phone_val and official_website and email_val:
                                priority = "High"
                            elif phone_val and (official_website or email_val):
                                priority = "Medium"
                            elif phone_val:
                                priority = "Medium"
                            else:
                                priority = "Low"

                            # Build Granular Notes
                            notes_list = []
                            if is_social:
                                notes_list.append("No official website; social profile available")
                            elif not official_website:
                                notes_list.append("Website unavailable")
                            elif enriched["Website Status"] == "Timeout":
                                notes_list.append("Website timeout")
                            elif enriched["Website Status"] != "Working":
                                notes_list.append(f"Website {enriched['Website Status'].lower()}")
                            
                            if not phone_val:
                                notes_list.append("Phone unavailable")
                            
                            if official_website and enriched["Website Status"] == "Working" and not email_val:
                                notes_list.append("Email not found")
                            
                            if enriched.get("Third Party Email"):
                                notes_list.append("Possible Third-Party Email")

                            if not official_website and not phone_val and not is_social:
                                notes_list.append("Only Google Maps listing available")

                            if enriched["Facebook"]:
                                notes_list.append("Facebook found")
                            if enriched["Instagram"]:
                                notes_list.append("Instagram found")
                            if enriched["WhatsApp"]:
                                notes_list.append("WhatsApp available")

                            notes_str = ", ".join(notes_list) if notes_list else "All details collected"

                            lead_record = {
                                "Business Name": name,
                                "Source Category": category,
                                "Category": extracted["category"],
                                "Search Location": location,
                                "Location": location,
                                "Address": extracted["address"],
                                "Phone": phone_val,
                                "Website": official_website,
                                "Email": email_val,
                                "WhatsApp": enriched["WhatsApp"],
                                "Facebook": enriched["Facebook"],
                                "Instagram": enriched["Instagram"],
                                "LinkedIn": enriched["LinkedIn"],
                                "Twitter/X": enriched["Twitter/X"],
                                "Contact Form": enriched["Contact Form"],
                                "Rating": extracted["rating"],
                                "Reviews": extracted["reviews"],
                                "Opening Hours": extracted["hours"],
                                "Google Maps Link": place_url,
                                "Website Status": enriched["Website Status"],
                                "Business Type": biz_type,
                                "Notes": notes_str,
                                "Priority": priority,
                                "Last Verified": today_date,
                                "Contacted": "No",
                                "Contact Date": "",
                                "Response": "",
                                "Remarks": ""
                            }

                            # Check Duplicate
                            name_addr_key = f"{name}|{extracted['address']}"
                            is_dup = (place_url in existing_links) or (phone_val and phone_val in existing_phones) or (name_addr_key in existing_names_addresses)

                            if is_dup:
                                lead_record["Notes"] = f"Duplicate removed ({notes_str})"
                                state["duplicates"].append(lead_record)
                                batch_duplicates += 1
                                print("Duplicate [YES] (Moved to duplicates)", flush=True)
                            else:
                                state["all_leads"].append(lead_record)
                                existing_links.add(place_url)
                                if phone_val:
                                    existing_phones.add(phone_val)
                                existing_names_addresses.add(name_addr_key)
                                batch_successful += 1
                                print("Done", flush=True)

                            # Process lead through validator layer & save to SQLite DB
                            cleaned_record = validator.process_raw_lead(lead_record)
                            db.save_business_to_db(cleaned_record)
                            db.update_queue_item(place_url, category, location, "completed")
                            db.update_resume_item(category, location, total_counter, place_url, "completed")
                            logger.info("scraper", f"Saved business [{total_counter}]: {name}")

                            if official_website: batch_websites += 1
                            if phone_val: batch_phones += 1
                            if email_val: batch_emails += 1
                            if enriched["WhatsApp"]: batch_whatsapp += 1
                            if enriched["Facebook"]: batch_facebook += 1
                            if enriched["Instagram"]: batch_instagram += 1
                            if enriched["LinkedIn"]: batch_linkedin += 1

                            print("------------------------", flush=True)

                        except Exception as ex:
                            print(f"Extraction Error: {ex}", flush=True)
                            screenshot_path = os.path.join(config.SCREENSHOTS_DIR, f"error_{total_counter}.png")
                            try:
                                page.screenshot(path=screenshot_path)
                            except Exception:
                                pass

                            fallback_record = {
                                "Business Name": "Place Lead " + str(total_counter),
                                "Source Category": category,
                                "Category": category,
                                "Search Location": location,
                                "Location": location,
                                "Address": "",
                                "Phone": "",
                                "Website": "",
                                "Email": "",
                                "WhatsApp": "",
                                "Facebook": "",
                                "Instagram": "",
                                "LinkedIn": "",
                                "Twitter/X": "",
                                "Contact Form": "",
                                "Rating": "",
                                "Reviews": "",
                                "Opening Hours": "",
                                "Google Maps Link": place_url,
                                "Website Status": "Failed",
                                "Business Type": "Unknown",
                                "Notes": "Extraction failed - Manual review required",
                                "Priority": "Low",
                                "Last Verified": today_date,
                                "Contacted": "No",
                                "Contact Date": "",
                                "Response": "",
                                "Remarks": ""
                            }
                            state["failed_leads"].append(fallback_record)
                            state["all_leads"].append(fallback_record)
                            batch_failed += 1
                            batch_manual_review += 1

                        # IMMEDATE SAVE & ATOMIC WRITE AFTER EVERY BUSINESS
                        processed_urls_set.add(place_url)
                        state["processed_urls"] = list(processed_urls_set)
                        sess_sec = int(time.time() - start_time)
                        save_progress(state, category, location, total_counter, sess_sec)
                        export_results(state)

                        # LIVE ETA & SPEED MONITOR LOG
                        elapsed_min = sess_sec / 60.0
                        speed_bpm = round((place_idx + 1) / max(elapsed_min, 0.01), 1)
                        rem_in_batch = len(collected_place_urls) - (place_idx + 1)
                        eta_min = round(rem_in_batch / max(speed_bpm, 0.1), 1)
                        print(f"[Speed: {speed_bpm} biz/min | ETA: {eta_min}m | Processed: {place_idx+1}/{len(collected_place_urls)}]", flush=True)

                        # CHECK RUNTIME EXPIRY
                        if config.RUN_MODE == "timed" and elapsed_min >= config.MAX_RUNTIME_MINUTES:
                            print("\n" + "="*40, flush=True)
                            print("SAFE CHECKPOINT CREATED", flush=True)
                            print(f"Runtime limit reached ({config.MAX_RUNTIME_MINUTES} minutes).", flush=True)
                            print(f"Processed: {len(state['all_leads'])} businesses", flush=True)
                            print(f"Current Category: {category}", flush=True)
                            print(f"Current Location: {location}", flush=True)
                            print("Next Resume Point Saved", flush=True)
                            print("="*40, flush=True)

                            save_progress(state, category, location, total_counter, sess_sec)
                            export_results(state)
                            time_limit_hit = True
                            break

                    print(f"\n{category} - {location}", flush=True)
                    print(f"Businesses Found : {len(collected_place_urls)}", flush=True)
                    print(f"  ├─ Successful  : {batch_successful}", flush=True)
                    print(f"  ├─ Duplicates  : {batch_duplicates}", flush=True)
                    print(f"  └─ Failed      : {batch_failed}", flush=True)
                    print("-----------------------", flush=True)

                    category_stats[category] = category_stats.get(category, 0) + batch_successful

                    state["searches_completed"] = state.get("searches_completed", 0) + 1
                    completed_batches_set.add(batch_key)
                    state["completed_batches"] = list(completed_batches_set)
                    save_progress(state, category, location, total_counter, int(time.time() - start_time))
                    export_results(state)

            # Save final run screenshot
            try:
                page.screenshot(path=os.path.join(config.SCREENSHOTS_DIR, "browser_validation.png"))
            except Exception:
                pass

            browser.close()

    except Exception as fatal_ex:
        print(f"\nEMERGENCY CHECKPOINT TRIGGERED: {fatal_ex}", flush=True)
        save_progress(state, session_runtime_sec=int(time.time() - start_time))
        export_results(state)

    # Calculate final stats summary
    all_leads = state.get("all_leads", [])
    failed_leads = state.get("failed_leads", [])
    duplicates = state.get("duplicates", [])

    businesses_found = len(all_leads) + len(duplicates)
    valid_leads = [lead for lead in all_leads if validate_lead(lead)]
    successful_extractions = len(valid_leads)
    failed_extractions = len(failed_leads) + (len(all_leads) - len(valid_leads))

    phones_found = sum(1 for lead in valid_leads if lead.get("Phone"))
    websites_found = sum(1 for lead in valid_leads if lead.get("Website"))
    emails_found = sum(1 for lead in valid_leads if lead.get("Email"))
    whatsapp_found = sum(1 for lead in valid_leads if lead.get("WhatsApp"))
    facebook_found = sum(1 for lead in valid_leads if lead.get("Facebook"))
    instagram_found = sum(1 for lead in valid_leads if lead.get("Instagram"))
    linkedin_found = sum(1 for lead in valid_leads if lead.get("LinkedIn"))
    duplicates_removed = len(duplicates)
    manual_review = failed_extractions + sum(1 for lead in valid_leads if "Manual review" in str(lead.get("Notes", "")))

    print("\n" + "="*40, flush=True)
    print("CATEGORY SUMMARY BREAKDOWN", flush=True)
    print("="*40, flush=True)
    for cat, count in category_stats.items():
        print(f"{cat:<25} : {count} leads", flush=True)

    searches_comp = state.get("searches_completed", len(state.get("completed_batches", [])))
    print("\n" + "="*40, flush=True)
    print("FINAL SUMMARY", flush=True)
    print("="*40, flush=True)
    print(f"Searches Completed     : {searches_comp}", flush=True)
    print(f"Businesses Found       : {businesses_found}", flush=True)
    print(f"  ├─ Successful        : {successful_extractions}", flush=True)
    print(f"  ├─ Duplicates        : {duplicates_removed}", flush=True)
    print(f"  └─ Failed            : {failed_extractions}", flush=True)
    print(f"Phone Numbers          : {phones_found}", flush=True)
    print(f"Websites               : {websites_found}", flush=True)
    print(f"Emails                 : {emails_found}", flush=True)
    print(f"WhatsApp               : {whatsapp_found}", flush=True)
    print(f"Facebook               : {facebook_found}", flush=True)
    print(f"Instagram              : {instagram_found}", flush=True)
    print(f"LinkedIn               : {linkedin_found}", flush=True)
    print(f"Manual Review Required : {manual_review}", flush=True)
    print("\nOutput:", flush=True)
    print(f"  {config.EXCEL_ALL}", flush=True)
    print(f"  {config.EXCEL_FAILED}", flush=True)
    print(f"  {config.EXCEL_DUPLICATES}", flush=True)
    print(f"  {config.EXCEL_SUMMARY}", flush=True)
    print(f"  {config.TXT_LEADS}", flush=True)
    print("="*40, flush=True)

    # Safe Independent Post-Processing Step: Automatic Lead Prioritization
    try:
        import prioritizer
        prioritizer.process_lead_prioritization()
    except Exception as p_err:
        print(f"Prioritization Notice: {p_err}", flush=True)


if __name__ == "__main__":
    scrape_google_maps()
