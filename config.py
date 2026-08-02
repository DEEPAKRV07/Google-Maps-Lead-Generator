"""
Google Maps Lead Generator - Configuration File
"""

import os

# ==========================================
# FILE PATHS & DIRECTORIES
# ==========================================
CATEGORIES_FILE = "categories.txt"
LOCATIONS_FILE = "locations.txt"

CACHE_DIR = "cache"
SCREENSHOTS_DIR = "screenshots"
BACKUPS_DIR = "backups"
OUTPUTS_DIR = "outputs"

PROGRESS_FILE = "progress.json"

EXCEL_ALL = os.path.join(OUTPUTS_DIR, "all_leads.xlsx")
EXCEL_FAILED = os.path.join(OUTPUTS_DIR, "failed_leads.xlsx")
EXCEL_DUPLICATES = os.path.join(OUTPUTS_DIR, "duplicates.xlsx")
EXCEL_SUMMARY = os.path.join(OUTPUTS_DIR, "summary.xlsx")
TXT_LEADS = os.path.join(OUTPUTS_DIR, "leads.txt")

# Ensure required directories exist
for folder in [CACHE_DIR, SCREENSHOTS_DIR, BACKUPS_DIR, OUTPUTS_DIR]:
    os.makedirs(folder, exist_ok=True)

# ==========================================
# SCRAPER SETTINGS
# ==========================================
MAX_LEADS_PER_LOCATION = 200
HEADLESS = False  # Set to True for background execution

# ==========================================
# WORKER POOL & MULTITHREADING
# ==========================================
MAX_WORKERS = min(4, os.cpu_count() or 4)
PROXY_ENABLED = False  # Set to True to enable proxy rotation from proxies.txt

# ==========================================
# TIMED SESSION & CHECKPOINT SETTINGS
# ==========================================
RUN_MODE = "timed"  # Options: "timed" or "continuous"
MAX_RUNTIME_MINUTES = 15  # Run in controlled sessions of 45 minutes

RANDOM_DELAY_MIN = 1.0
RANDOM_DELAY_MAX = 2.5
