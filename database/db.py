"""
Master SQLite Database Module (database/db.py)
Handles schema migrations, transactional saves, queues, history snapshots, and DB backups.
"""

import os
import sqlite3
import shutil
from datetime import datetime
import logger

DB_DIR = "database"
DB_FILE = os.path.join(DB_DIR, "db.sqlite3")
SCHEMA_FILE = os.path.join(DB_DIR, "schema.sql")
MIGRATIONS_DIR = os.path.join(DB_DIR, "migrations")
BACKUPS_DIR = os.path.join(DB_DIR, "backups")

for folder in [DB_DIR, MIGRATIONS_DIR, BACKUPS_DIR]:
    os.makedirs(folder, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes SQLite Master Database and applies schema and migrations if needed.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Apply DDL Schema
        if os.path.exists(SCHEMA_FILE):
            with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())

        # Apply Migrations
        if os.path.exists(MIGRATIONS_DIR):
            migration_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])
            for m_file in migration_files:
                m_path = os.path.join(MIGRATIONS_DIR, m_file)
                with open(m_path, 'r', encoding='utf-8') as f:
                    cursor.executescript(f.read())

        conn.commit()
        conn.close()
        logger.info("database", f"SQLite Master DB initialized: {DB_FILE}")
        cleanup_stale_locks()
    except Exception as e:
        logger.error("database", f"SQLite init error: {e}")


def create_db_snapshot():
    """
    Creates a timestamped snapshot backup of db.sqlite3 in database/backups/
    """
    if not os.path.exists(DB_FILE):
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUPS_DIR, f"db_{ts}.sqlite")
    try:
        shutil.copy2(DB_FILE, backup_path)
        logger.info("database", f"Created SQLite database snapshot: {backup_path}")

        # Keep 10 latest snapshots
        snapshots = sorted([os.path.join(BACKUPS_DIR, f) for f in os.listdir(BACKUPS_DIR) if f.startswith("db_")], reverse=True)
        for old_s in snapshots[10:]:
            try:
                os.remove(old_s)
            except Exception:
                pass
    except Exception as e:
        logger.warning("database", f"SQLite snapshot notice: {e}")


def save_business_to_db(lead):
    """
    Saves or updates a processed business lead in SQLite Master DB.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        maps_link = lead.get("Google Maps Link", "")
        if not maps_link:
            conn.close()
            return

        cursor.execute("""
            INSERT INTO businesses (
                name, source_category, category, search_location, location, address, phone,
                website, email, whatsapp, facebook, instagram, linkedin, twitter, contact_form,
                rating, reviews, hours, google_maps_link, website_status, business_type, notes,
                priority_score, priority_level, rank, next_action, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(google_maps_link) DO UPDATE SET
                name=excluded.name,
                address=excluded.address,
                phone=excluded.phone,
                website=excluded.website,
                email=excluded.email,
                whatsapp=excluded.whatsapp,
                facebook=excluded.facebook,
                instagram=excluded.instagram,
                linkedin=excluded.linkedin,
                rating=excluded.rating,
                reviews=excluded.reviews,
                website_status=excluded.website_status,
                notes=excluded.notes,
                priority_score=excluded.priority_score,
                priority_level=excluded.priority_level,
                rank=excluded.rank,
                next_action=excluded.next_action,
                updated_at=CURRENT_TIMESTAMP;
        """, (
            lead.get("Business Name", ""), lead.get("Source Category", ""), lead.get("Category", ""),
            lead.get("Search Location", ""), lead.get("Location", ""), lead.get("Address", ""),
            lead.get("Phone", ""), lead.get("Website", ""), lead.get("Email", ""),
            lead.get("WhatsApp", ""), lead.get("Facebook", ""), lead.get("Instagram", ""),
            lead.get("LinkedIn", ""), lead.get("Twitter/X", ""), lead.get("Contact Form", ""),
            lead.get("Rating", 0), lead.get("Reviews", 0), lead.get("Opening Hours", ""),
            maps_link, lead.get("Website Status", ""), lead.get("Business Type", ""),
            lead.get("Notes", ""), lead.get("Priority Score", 0), lead.get("Priority Level", "D"),
            lead.get("Rank", None), lead.get("Next Action", "")
        ))

        # Insert history record for trend tracking
        cursor.execute("SELECT id FROM businesses WHERE google_maps_link = ?", (maps_link,))
        row = cursor.fetchone()
        if row:
            b_id = row["id"]
            cursor.execute("""
                INSERT INTO business_history (business_id, rating, reviews, phone, website, website_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (b_id, lead.get("Rating", 0), lead.get("Reviews", 0), lead.get("Phone", ""), lead.get("Website", ""), lead.get("Website Status", "")))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("database", f"Save business SQLite error: {e}")


def get_all_businesses_from_db():
    """
    Returns all processed business leads from SQLite Master DB as a list of dictionaries.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM businesses ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()

        leads = []
        for r in rows:
            lead_dict = {
                "Business Name": r["name"],
                "Source Category": r["source_category"],
                "Category": r["category"],
                "Search Location": r["search_location"],
                "Location": r["location"],
                "Address": r["address"],
                "Phone": r["phone"],
                "Website": r["website"],
                "Email": r["email"],
                "WhatsApp": r["whatsapp"],
                "Facebook": r["facebook"],
                "Instagram": r["instagram"],
                "LinkedIn": r["linkedin"],
                "Twitter/X": r["twitter"],
                "Contact Form": r["contact_form"],
                "Rating": r["rating"],
                "Reviews": r["reviews"],
                "Opening Hours": r["hours"],
                "Google Maps Link": r["google_maps_link"],
                "Website Status": r["website_status"],
                "Business Type": r["business_type"],
                "Notes": r["notes"],
                "Priority Score": r["priority_score"],
                "Priority Level": r["priority_level"],
                "Rank": r["rank"],
                "Next Action": r["next_action"]
            }
            leads.append(lead_dict)
        return leads
    except Exception as e:
        logger.error("database", f"Get businesses SQLite error: {e}")
        return []


def save_urls_to_queue(urls, category, location):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for url in urls:
            cursor.execute("""
                INSERT INTO queue (maps_url, category, location, status, updated_at)
                VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                ON CONFLICT(maps_url) DO NOTHING;
            """, (url, category, location))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("database", f"Save URLs to queue SQLite error: {e}")


def get_pending_queue_items(category, location, limit=50):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT maps_url FROM queue
            WHERE category = ? AND location = ? AND status = 'pending'
            ORDER BY id ASC
            LIMIT ?;
        """, (category, location, limit))
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows if r[0] and r[0].startswith("http")]
    except Exception as e:
        logger.error("database", f"Get pending queue items SQLite error: {e}")
        return []


def update_queue_item(maps_url, category, location, status="completed"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO queue (maps_url, category, location, status, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(maps_url) DO UPDATE SET
                status=excluded.status,
                updated_at=CURRENT_TIMESTAMP;
        """, (maps_url, category, location, status))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("database", f"Update queue SQLite error: {e}")


def update_resume_item(category, location, index, maps_url, status="completed", worker_id=None, attempt_count=1, last_error=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resume_state (category, location, business_index, maps_url, status, worker_id, attempt_count, last_error, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(maps_url) DO UPDATE SET
                business_index=excluded.business_index,
                status=excluded.status,
                worker_id=excluded.worker_id,
                attempt_count=excluded.attempt_count,
                last_error=excluded.last_error,
                updated_at=CURRENT_TIMESTAMP;
        """, (category, location, index, maps_url, status, worker_id, attempt_count, last_error))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("database", f"Update resume SQLite error: {e}")


def is_url_processed_in_db(maps_url):
    """
    Checks if a Google Maps place URL is already saved in businesses or resume_state as completed/skipped.
    """
    if not maps_url:
        return False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM businesses WHERE google_maps_link = ?", (maps_url,))
        if cursor.fetchone():
            conn.close()
            return True
        cursor.execute("SELECT 1 FROM resume_state WHERE maps_url = ? AND status IN ('completed', 'skipped')", (maps_url,))
        res = cursor.fetchone()
        conn.close()
        return bool(res)
    except Exception as e:
        logger.error("database", f"Check URL processed error: {e}")
        return False


def get_last_resume_index(category, location):
    """
    Returns the highest processed business_index for a category and location batch.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(business_index) FROM resume_state WHERE category = ? AND location = ? AND status = 'completed'", (category, location))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] is not None:
            return row[0]
    except Exception as e:
        logger.error("database", f"Get resume index error: {e}")
    return 0


def cleanup_stale_locks():
    """
    Resets any 'running' queue or resume state items back to 'pending' on startup
    to ensure worker crash recovery.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE queue SET status = 'pending' WHERE status = 'running';")
        cursor.execute("UPDATE resume_state SET status = 'pending' WHERE status = 'running';")
        conn.commit()
        conn.close()
        logger.info("database", "Cleaned up stale locks in queue and resume_state tables on startup.")
    except Exception as e:
        logger.error("database", f"Cleanup stale locks error: {e}")
