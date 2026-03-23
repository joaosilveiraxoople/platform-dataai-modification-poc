"""
Sample script demonstrating how to insert or update modified notifications
into PostgreSQL using a single connection with batch transactions.

This script is intended as a reference for external applications that need to
write notifications to the modified_notifications table.

Since this is a short-lived batch script (runs, inserts, exits), a single
connection with all operations in one transaction is the most efficient
approach — no connection pooling overhead needed.
"""

import json
import os
from datetime import datetime, timezone

import psycopg2

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
POSTGRES_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5433)),
    "dbname": os.environ.get("POSTGRES_DB", "sentinel_events"),
    "user": os.environ.get("POSTGRES_USER", "sentinel"),
    "password": os.environ.get("POSTGRES_PASSWORD", "sentinel_pass"),
}

# ---------------------------------------------------------------------------
# Upsert query: inserts a new row or updates if product_id already exists
# ---------------------------------------------------------------------------
UPSERT_QUERY = """
    INSERT INTO events.modified_notifications
        (notification_timestamp, product_id, notification, processed)
    VALUES (%s, %s, %s, FALSE)
    ON CONFLICT (product_id)
    DO UPDATE SET
        notification_timestamp = EXCLUDED.notification_timestamp,
        notification           = EXCLUDED.notification,
        processed              = FALSE;
"""


def upsert_notification(cursor, product_id: str, notification: dict):
    """
    Insert or update a single notification.

    If a row with the same product_id already exists, it updates the
    notification_timestamp, notification payload, and resets processed to FALSE.
    """
    cursor.execute(UPSERT_QUERY, (
        datetime.now(timezone.utc),
        product_id,
        json.dumps(notification),
    ))
    print(f"[OK] Upserted notification for product: {product_id}")


def upsert_batch(cursor, notifications: list[dict]):
    """
    Insert or update multiple notifications.
    All operations use the same cursor within a single transaction.
    """
    for notif in notifications:
        cursor.execute(UPSERT_QUERY, (
            datetime.now(timezone.utc),
            notif["product_id"],
            json.dumps(notif),
        ))
    print(f"[OK] Batch upserted {len(notifications)} notification(s)")


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("  Sample: Insert/Update Notifications (Single Connection)")
    print("=" * 70)

    # Open a single connection for the entire script execution
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    print("\n[Postgres] Connected.\n")

    try:
        # --- Example 1: Single upsert ---
        print("--- Single Upsert ---")
        sample_notification = {
            "product_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "timestamp": "2026-03-23T12:00:00Z",
            "status": "modified",
            "collection": "SENTINEL-2",
            "processingLevel": "L2A",
        }
        upsert_notification(cursor, sample_notification["product_id"], sample_notification)

        # --- Example 2: Batch upsert (multiple notifications in one transaction) ---
        print("\n--- Batch Upsert (single transaction) ---")
        batch_notifications = [
            {
                "product_id": "11111111-2222-3333-4444-555555555555",
                "timestamp": "2026-03-23T12:01:00Z",
                "status": "modified",
                "collection": "SENTINEL-2",
            },
            {
                "product_id": "66666666-7777-8888-9999-aaaaaaaaaaaa",
                "timestamp": "2026-03-23T12:02:00Z",
                "status": "modified",
                "collection": "SENTINEL-2",
            },
        ]
        upsert_batch(cursor, batch_notifications)

        # --- Example 3: Update existing product (same product_id, new payload) ---
        print("\n--- Update Existing Product ---")
        updated_notification = {
            "product_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "timestamp": "2026-03-23T14:00:00Z",
            "status": "modified",
            "collection": "SENTINEL-2",
            "processingLevel": "L2A",
            "note": "Updated notification - will reset processed to FALSE",
        }
        upsert_notification(cursor, updated_notification["product_id"], updated_notification)

        # Commit all operations in one transaction
        conn.commit()
        print("\n[Postgres] All operations committed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Transaction rolled back: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
        print("[Postgres] Connection closed. Done.\n")
