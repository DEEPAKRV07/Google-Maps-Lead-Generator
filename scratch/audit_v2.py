"""
Production Verification Audit Script for v2.0.0 Enterprise Release
"""

import os
import sqlite3
import pandas as pd

print("=== 1. VERIFYING OUTPUT FILES ===")
expected_files = [
    "outputs/all_leads.xlsx",
    "outputs/all_leads_prioritized.xlsx",
    "outputs/top_25_leads.xlsx",
    "outputs/top_50_leads.xlsx",
    "outputs/top_100_leads.xlsx",
    "outputs/summary.xlsx",
    "outputs/Dashboard.xlsx",
    "outputs/dashboard.html",
    "outputs/duplicates.xlsx",
    "outputs/failed_leads.xlsx",
    "outputs/leads.txt",
    "outputs/ai_lead_pitches.xlsx",
    "outputs/CRM_Exports/hubspot_import.csv",
    "outputs/CRM_Exports/zoho_import.csv",
    "outputs/CRM_Exports/salesforce_import.csv"
]
for f in expected_files:
    status = "OK" if os.path.exists(f) else "MISSING"
    print(f"[{status}] {f}")

print("\n=== 2. VERIFYING SQLITE DATABASE TABLES & INTEGRITY ===")
conn = sqlite3.connect("database/db.sqlite3")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cur.fetchall()]
for t in ["version", "settings", "raw_businesses", "businesses", "business_history", "queue", "sessions", "resume_state", "contacts", "social_links", "logs"]:
    status = "OK" if t in tables else "MISSING"
    print(f"[{status}] Table: {t}")

cur.execute("SELECT COUNT(*) FROM businesses")
b_cnt = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT google_maps_link) FROM businesses")
u_cnt = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM business_history")
h_cnt = cur.fetchone()[0]
print(f"Businesses Count : {b_cnt}")
print(f"Unique Maps URLs : {u_cnt}")
print(f"History Entries  : {h_cnt}")
conn.close()

print("\n=== 3. VERIFYING LOG DIRECTORIES & BACKUPS ===")
for d in ["logs/scraper", "logs/website", "logs/database", "logs/errors", "database/backups"]:
    status = "OK" if os.path.exists(d) else "MISSING"
    print(f"[{status}] Directory: {d}")
