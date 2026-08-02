"""
Google Maps Scraper Selectors Registry (providers/google_maps/selectors.py)
Centralized dictionary of DOM selectors for Google Maps automation.
"""

NAME_SELECTORS = [
    "h1.DUwif", "h1.fontHeadlineLarge", "div.lMbz3e h1",
    "h1[aria-label]", "div.section-hero-header-title"
]

PHONE_SELECTORS = [
    "button[data-item-id*='phone:tel:']", "button[aria-label*='Phone:']",
    "button[data-tooltip*='phone']", "div.QS375b button[aria-label*='Phone']"
]

WEBSITE_SELECTORS = [
    "a[data-item-id='authority']", "a[aria-label*='Website:']",
    "a[aria-label*='website']", "a[data-tooltip*='website']"
]

RATING_SELECTORS = [
    "div.F7L825", "span.ceNzR", "span[aria-label*='stars']",
    "div[role='img'][aria-label*='stars']", "span.MW4350"
]

REVIEWS_SELECTORS = [
    "button[aria-label*='reviews']", "span[aria-label*='reviews']",
    "button[jsaction*='review']"
]

HOURS_SELECTORS = [
    "button[data-item-id='oh']", "div[aria-label*='Hours']",
    "button[aria-label*='Open']", "button[aria-label*='Closed']"
]
