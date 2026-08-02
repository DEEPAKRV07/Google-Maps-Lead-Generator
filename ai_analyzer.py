"""
FORCRUX AI Website Need & Pitch Analysis Engine (ai_analyzer.py)
Analyzes scraped website features, contact availability, and digital presence to produce
explainable digital agency pitches for FORCRUX with confidence ratings and gap reasons.
"""

import os
import pandas as pd
import config
import logger
import database.db as db

AI_EXPORT_FILE = os.path.join(config.OUTPUTS_DIR, "ai_lead_pitches.xlsx")


def analyze_lead_needs(lead):
    """
    Analyzes a single lead and returns explainable digital agency pitch details.
    """
    website = lead.get("Website", "")
    email = lead.get("Email", "")
    phone = lead.get("Phone", "")
    rating = float(lead.get("Rating", 0) or 0)
    reviews = int(lead.get("Reviews", 0) or 0)
    instagram = lead.get("Instagram", "")
    facebook = lead.get("Facebook", "")

    gaps = []
    confidence = 85
    recommended_pitch = "Website Redesign & SEO"

    # Gap 1: No Website
    if not website or website.lower() in ["none", "n/a", "no website"]:
        gaps.append("No Official Business Website")
        confidence += 10
        recommended_pitch = "Custom Website Design & Setup"
    elif website.startswith("http://"):
        gaps.append("Insecure HTTP Website (Missing SSL Certificate)")
        confidence += 5

    # Gap 2: Email Availability
    if not email:
        gaps.append("Missing Direct Customer Contact Email")

    # Gap 3: Social Media Presence
    if not instagram and not facebook:
        gaps.append("Missing Active Social Media Channels (Instagram/Facebook)")
        if "Website" in recommended_pitch:
            recommended_pitch += " + Social Growth Package"

    # Gap 4: Reputation & Review Count
    if reviews < 10 or rating < 4.0:
        gaps.append(f"Low Online Reputation ({rating} stars across {reviews} reviews)")
        recommended_pitch += " + Reputation Management & AI Review Bot"

    confidence = min(98, max(60, confidence))
    gaps_str = " | ".join(gaps) if gaps else "Strong Digital Presence - Standard Retainer Offer"

    return {
        "Business Name": lead.get("Business Name", ""),
        "Phone": phone,
        "Website": website,
        "Confidence Score": f"{confidence}%",
        "Identified Digital Gaps": gaps_str,
        "Recommended FORCRUX Pitch": recommended_pitch,
        "Priority Level": lead.get("Priority Level", "D"),
        "Next Action": lead.get("Next Action", "")
    }


def analyze_all_leads():
    """
    Queries SQLite Master DB, runs AI analysis on all leads, and exports outputs/ai_lead_pitches.xlsx.
    """
    leads = db.get_all_businesses_from_db()
    if not leads:
        return

    analyzed = [analyze_lead_needs(l) for l in leads]
    df = pd.DataFrame(analyzed)

    try:
        df.to_excel(AI_EXPORT_FILE, index=False)
        logger.info("database", f"Generated FORCRUX AI Need Analysis report: {AI_EXPORT_FILE}")
    except Exception as e:
        logger.error("database", f"Generate AI analysis report error: {e}")
