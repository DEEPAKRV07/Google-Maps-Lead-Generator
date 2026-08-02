"""
Business Data Validator & Normalization Engine
Normalizes phones, emails, ratings, reviews, and URLs before SQLite persistence.
"""

import re
import urllib.parse
from urllib.parse import urlparse


def normalize_phone(phone_str):
    if not phone_str:
        return ""
    phone = str(phone_str).strip()
    if not phone or phone.lower() in ["none", "n/a", "null", "-", "no phone"]:
        return ""
    
    # Extract digits and optional leading plus
    clean_digits = re.sub(r'[^\d+]', '', phone)
    if len(clean_digits) >= 7:
        return clean_digits
    return phone


def parse_reviews_count(reviews_val):
    if not reviews_val:
        return 0
    r_str = str(reviews_val).strip().upper().replace(',', '')
    if not r_str or r_str in ["NONE", "N/A", "NULL", "-"]:
        return 0

    try:
        if 'K' in r_str:
            num = float(r_str.replace('K', '').strip())
            return int(num * 1000)
        elif 'M' in r_str:
            num = float(r_str.replace('M', '').strip())
            return int(num * 1000000)
        else:
            match = re.search(r'(\d+)', r_str)
            if match:
                return int(match.group(1))
    except Exception:
        pass
    return 0


def parse_rating_val(rating_val):
    if not rating_val:
        return 0.0
    try:
        r_float = float(str(rating_val).strip())
        if 0.0 <= r_float <= 5.0:
            return round(r_float, 1)
    except Exception:
        pass
    return 0.0


def normalize_url(url_str):
    if not url_str:
        return ""
    u = str(url_str).strip()
    if not u or u.lower() in ["none", "n/a", "null", "-", "no website"]:
        return ""
    if not u.startswith("http://") and not u.startswith("https://"):
        u = "https://" + u
    return u


def validate_email_address(email_str):
    if not email_str or '@' not in str(email_str):
        return ""
    em = str(email_str).lower().strip()

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
        return ""
    if any(em.startswith(p) for p in rejected_prefixes):
        return ""

    if any(bad in em for bad in ["u003e", "u0026", "%", "\\", "..", "http", "www", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js"]):
        return ""

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', em):
        return ""

    return em


def process_raw_lead(raw_lead):
    """
    Normalizes a raw extracted business dictionary.
    Returns a cleaned, validated dictionary ready for SQLite Master DB insertion.
    """
    cleaned = dict(raw_lead)

    cleaned["Phone"] = normalize_phone(raw_lead.get("Phone", ""))
    cleaned["Website"] = normalize_url(raw_lead.get("Website", ""))
    cleaned["Email"] = validate_email_address(raw_lead.get("Email", ""))
    cleaned["Rating"] = parse_rating_val(raw_lead.get("Rating", 0))
    cleaned["Reviews"] = parse_reviews_count(raw_lead.get("Reviews", 0))

    return cleaned
