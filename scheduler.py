"""
Deterministic Round-Robin Task Scheduler (scheduler.py)
Interleaves (category, location) tasks to ensure diverse lead collection across industries.
Integrates with SQLite queue table for item-level resume.
"""

import logger
import database.db as db


def generate_round_robin_tasks(categories, locations):
    """
    Generates a deterministic round-robin list of (category, location) tuples.
    Round 1: Cat 1 x Loc 1, Cat 2 x Loc 1, Cat 3 x Loc 1...
    Round 2: Cat 1 x Loc 2, Cat 2 x Loc 2, Cat 3 x Loc 2...
    """
    tasks = []
    if not categories or not locations:
        return tasks

    for loc in locations:
        for cat in categories:
            tasks.append((cat, loc))

    return tasks


def sync_tasks_to_db(tasks):
    """
    Synchronizes (category, location) task sequence into SQLite queue table.
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        for idx, (cat, loc) in enumerate(tasks):
            task_key = f"{cat}|{loc}"
            cursor.execute("""
                INSERT INTO queue (maps_url, category, location, status, updated_at)
                VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                ON CONFLICT(maps_url) DO NOTHING;
            """, (task_key, cat, loc))

        conn.commit()
        conn.close()
        logger.info("database", f"Synchronized {len(tasks)} round-robin tasks into SQLite queue.")
    except Exception as e:
        logger.error("database", f"Sync tasks SQLite error: {e}")


def get_task_sequence(categories, locations):
    """
    Main entry point for lead_generator.py to get task sequence.
    """
    tasks = generate_round_robin_tasks(categories, locations)
    sync_tasks_to_db(tasks)
    return tasks
