"""
Multithreaded Website Enrichment & Worker Queue Module (website_crawler.py)
Crawls business websites concurrently using ThreadPoolExecutor(max_workers=MAX_WORKERS)
without blocking the main Google Maps scraper.
"""

import re
import time
import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import config
import logger
import validator
import database.db as db

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def extract_contacts_from_html(html_text):
    """
    Extracts emails, social links, and WhatsApp from raw HTML.
    """
    contacts = {
        "Email": "",
        "WhatsApp": "",
        "Facebook": "",
        "Instagram": "",
        "LinkedIn": "",
        "Twitter/X": "",
        "Contact Form": ""
    }
    if not html_text:
        return contacts

    soup = BeautifulSoup(html_text, "html.parser")

    # Email extraction
    emails = set()
    for mailto in soup.select('a[href^="mailto:"]'):
        href = mailto.get('href', '')
        e = href.replace('mailto:', '').split('?')[0].strip()
        v_e = validator.validate_email_address(e)
        if v_e:
            emails.add(v_e)

    text_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_text)
    for e in text_emails:
        v_e = validator.validate_email_address(e)
        if v_e:
            emails.add(v_e)

    if emails:
        contacts["Email"] = list(emails)[0]

    # Social links & WhatsApp extraction
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        h_lower = href.lower()

        if "wa.me/" in h_lower or "api.whatsapp.com/send" in h_lower or "whatsapp:" in h_lower:
            contacts["WhatsApp"] = href
        elif "facebook.com/" in h_lower and not any(x in h_lower for x in ["sharer", "share.php"]):
            contacts["Facebook"] = href
        elif "instagram.com/" in h_lower:
            contacts["Instagram"] = href
        elif "linkedin.com/" in h_lower:
            contacts["LinkedIn"] = href
        elif "twitter.com/" in h_lower or "x.com/" in h_lower:
            contacts["Twitter/X"] = href
        elif "contact" in h_lower or "contact-us" in h_lower:
            if not contacts["Contact Form"]:
                contacts["Contact Form"] = href

    return contacts


def crawl_single_website(website_url, timeout=10):
    """
    Crawls home page and contact pages for a single website.
    """
    url = validator.normalize_url(website_url)
    if not url:
        return {"Email": "", "WhatsApp": "", "Facebook": "", "Instagram": "", "LinkedIn": "", "Twitter/X": "", "Contact Form": "", "Status": "No Website"}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, verify=False)
        if resp.status_code == 200:
            contacts = extract_contacts_from_html(resp.text)
            contacts["Status"] = "Success"
            return contacts
    except Exception as e:
        logger.warning("website", f"Timeout or error crawling {url}: {e}")

    return {"Email": "", "WhatsApp": "", "Facebook": "", "Instagram": "", "LinkedIn": "", "Twitter/X": "", "Contact Form": "", "Status": "Failed"}


def worker_task(lead_item, worker_id):
    """
    Worker task executed in thread pool.
    """
    website = lead_item.get("Website", "")
    maps_link = lead_item.get("Google Maps Link", "")

    if not website:
        return lead_item

    contacts = crawl_single_website(website)
    for k in ["Email", "WhatsApp", "Facebook", "Instagram", "LinkedIn", "Twitter/X", "Contact Form"]:
        if contacts.get(k) and not lead_item.get(k):
            lead_item[k] = contacts[k]

    lead_item["Website Status"] = contacts.get("Status", "Checked")

    # Update in SQLite Master DB
    cleaned = validator.process_raw_lead(lead_item)
    db.save_business_to_db(cleaned)
    db.update_queue_item(maps_link, lead_item.get("Category", ""), lead_item.get("Location", ""), "completed")

    logger.info("website", f"[{worker_id}] Enriched website for {lead_item.get('Business Name')}")
    return lead_item


def enrich_leads_multithreaded(leads_list, max_workers=None):
    """
    Enriches a batch of leads concurrently using ThreadPoolExecutor.
    """
    if not max_workers:
        max_workers = getattr(config, "MAX_WORKERS", 4)

    logger.info("website", f"Starting multithreaded website enrichment with MAX_WORKERS={max_workers}...")
    enriched_leads = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {}
        for idx, lead in enumerate(leads_list):
            w_id = f"Worker-{(idx % max_workers) + 1}"
            future = executor.submit(worker_task, lead, w_id)
            future_map[future] = lead

        for future in as_completed(future_map):
            try:
                res = future.result()
                enriched_leads.append(res)
            except Exception as e:
                logger.error("website", f"Worker execution error: {e}")

    return enriched_leads
