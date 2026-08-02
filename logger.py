"""
Structured Sub-Categorized Logging Framework
Writes logs to logs/scraper/, logs/website/, logs/database/, logs/errors/
with daily rotation (YYYY-MM-DD.log).
"""

import os
import sys
from datetime import datetime

LOGS_DIR = "logs"
MODULES = ["scraper", "website", "database", "errors"]

for mod in MODULES:
    os.makedirs(os.path.join(LOGS_DIR, mod), exist_ok=True)


def log_event(module, level, message):
    """
    Logs an event to console and sub-categorized daily log file.
    module: 'scraper', 'website', 'database', 'errors'
    level: 'INFO', 'WARNING', 'ERROR', 'CHECKPOINT', 'SEARCH'
    """
    if module not in MODULES:
        module = "scraper"

    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = f"[{timestamp_str}] [{level.upper()}] {message}\n"

    # Write to specific module log file
    mod_file = os.path.join(LOGS_DIR, module, f"{today_str}.log")
    try:
        with open(mod_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass

    # Duplicate errors to logs/errors/YYYY-MM-DD.log if level is ERROR
    if level.upper() == "ERROR" and module != "errors":
        err_file = os.path.join(LOGS_DIR, "errors", f"{today_str}.log")
        try:
            with open(err_file, "a", encoding="utf-8") as f:
                f.write(f"[{module.upper()}] {log_line}")
        except Exception:
            pass


def info(module, message):
    log_event(module, "INFO", message)

def warning(module, message):
    log_event(module, "WARNING", message)

def error(module, message):
    log_event(module, "ERROR", message)

def checkpoint(module, message):
    log_event(module, "CHECKPOINT", message)
