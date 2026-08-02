"""
Multi-CRM Exporter Module (crm_exporter.py)
Exports master leads from database/db.sqlite3 into HubSpot, Zoho CRM, and Salesforce schemas.
"""

import os
import pandas as pd
import config
import logger
import database.db as db

CRM_DIR = os.path.join(config.OUTPUTS_DIR, "CRM_Exports")
os.makedirs(CRM_DIR, exist_ok=True)


def export_to_hubspot(leads):
    """
    Exports leads to HubSpot Contacts CSV schema.
    """
    rows = []
    for l in leads:
        name = l.get("Business Name", "")
        rows.append({
            "Company Name": name,
            "Phone Number": l.get("Phone", ""),
            "Website URL": l.get("Website", ""),
            "Email": l.get("Email", ""),
            "Street Address": l.get("Address", ""),
            "City": l.get("Location", ""),
            "Lead Status": "NEW",
            "Lifecycle Stage": "Lead"
        })

    df = pd.DataFrame(rows)
    out_path = os.path.join(CRM_DIR, "hubspot_import.csv")
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("database", f"Exported {len(df)} leads to HubSpot schema: {out_path}")


def export_to_zoho(leads):
    """
    Exports leads to Zoho CRM Leads CSV schema.
    """
    rows = []
    for l in leads:
        rows.append({
            "Company": l.get("Business Name", ""),
            "Phone": l.get("Phone", ""),
            "Website": l.get("Website", ""),
            "Email": l.get("Email", ""),
            "Street": l.get("Address", ""),
            "City": l.get("Location", ""),
            "Lead Source": "Google Maps Lead Generator",
            "Rating": l.get("Priority Level", "D")
        })

    df = pd.DataFrame(rows)
    out_path = os.path.join(CRM_DIR, "zoho_import.csv")
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("database", f"Exported {len(df)} leads to Zoho CRM schema: {out_path}")


def export_to_salesforce(leads):
    """
    Exports leads to Salesforce Lead Import CSV schema.
    """
    rows = []
    for l in leads:
        rows.append({
            "Company": l.get("Business Name", ""),
            "Phone": l.get("Phone", ""),
            "Website": l.get("Website", ""),
            "Email": l.get("Email", ""),
            "Street": l.get("Address", ""),
            "Status": "Open - Not Contacted",
            "Rating": l.get("Priority Level", "D")
        })

    df = pd.DataFrame(rows)
    out_path = os.path.join(CRM_DIR, "salesforce_import.csv")
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("database", f"Exported {len(df)} leads to Salesforce schema: {out_path}")


def export_all_crms():
    """
    Queries SQLite Master DB and exports to all CRM schemas.
    """
    leads = db.get_all_businesses_from_db()
    if not leads:
        return

    export_to_hubspot(leads)
    export_to_zoho(leads)
    export_to_salesforce(leads)
