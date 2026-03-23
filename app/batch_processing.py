"""
Sentinel-2 Modified Notifications - Batch Processing Application (Demo)

This script simulates the batch processing application workflow:
  1. Query PostgreSQL for unprocessed notifications older than 10 minutes
  2. Check Redis to see if each product is currently being processed
  3. Send eligible notifications to the queue (simulated with print output)
  4. Mark sent notifications as processed in PostgreSQL
"""

import json
import os

import psycopg2
import redis

# ---------------------------------------------------------------------------
# Configuration (reads from environment variables, with localhost defaults)
# ---------------------------------------------------------------------------
POSTGRES_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    "dbname": os.environ.get("POSTGRES_DB", "sentinel_events"),
    "user": os.environ.get("POSTGRES_USER", "sentinel"),
    "password": os.environ.get("POSTGRES_PASSWORD", "sentinel_pass"),
}

REDIS_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "localhost"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
}

BATCH_QUERY = """
    SELECT
        notification_timestamp,
        product_id,
        notification
    FROM events.modified_notifications
    WHERE processed = FALSE
      AND notification_timestamp <= NOW() - INTERVAL '10 minutes'
    ORDER BY notification_timestamp;
"""

MARK_PROCESSED_QUERY = """
    UPDATE events.modified_notifications
    SET processed = TRUE
    WHERE product_id = %s;
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def print_separator():
    print("=" * 80)


def print_step(step_number, title):
    print()
    print_separator()
    print(f"  STEP {step_number}: {title}")
    print_separator()
    print()


# ---------------------------------------------------------------------------
# Main batch processing workflow
# ---------------------------------------------------------------------------
def run_batch():
    print()
    print_separator()
    print("  SENTINEL-2 MODIFIED NOTIFICATIONS - BATCH PROCESSING APPLICATION")
    print_separator()

    # -----------------------------------------------------------------------
    # Connect to PostgreSQL
    # -----------------------------------------------------------------------
    print("\n[Postgres] Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cursor = pg_conn.cursor()
    print("[Postgres] Connected successfully.")

    # -----------------------------------------------------------------------
    # Connect to Redis
    # -----------------------------------------------------------------------
    print("\n[Redis] Connecting to Redis...")
    redis_client = redis.Redis(**REDIS_CONFIG, decode_responses=True)
    redis_client.ping()
    print("[Redis] Connected successfully.")

    # -----------------------------------------------------------------------
    # STEP 1: Query PostgreSQL for pending notifications
    # -----------------------------------------------------------------------
    print_step(1, "Query PostgreSQL for Pending Notifications")

    print("[Postgres] Executing batch query:")
    print("    SELECT product_id, notification_timestamp")
    print("    FROM events.modified_notifications")
    print("    WHERE processed = FALSE")
    print("      AND notification_timestamp <= NOW() - INTERVAL '10 minutes'")
    print()

    pg_cursor.execute(BATCH_QUERY)
    pending_notifications = pg_cursor.fetchall()

    if not pending_notifications:
        print("[Postgres] No pending notifications found. Nothing to process.")
        pg_cursor.close()
        pg_conn.close()
        return

    print(f"[Postgres] Found {len(pending_notifications)} pending notification(s):\n")
    for row in pending_notifications:
        ts, product_id, _ = row
        print(f"    - {product_id}")
        print(f"      Notification timestamp: {ts}")
    print()

    # -----------------------------------------------------------------------
    # STEP 2: Check Redis for products currently being processed
    # -----------------------------------------------------------------------
    print_step(2, "Check Redis Cache for Product Processing Status")

    eligible = []
    skipped = []

    for row in pending_notifications:
        ts, product_id, notification = row
        redis_key = product_id
        is_processing = redis_client.exists(redis_key)

        if is_processing:
            status = redis_client.get(redis_key)
            print(f"    [SKIP] {product_id}")
            print(f"           Redis key '{redis_key}' EXISTS with status '{status}' → product is being processed.")
            skipped.append(row)
        else:
            print(f"    [OK]   {product_id}")
            print(f"           Redis key '{redis_key}' NOT FOUND → product is available.")
            eligible.append(row)

    print(f"\n    Summary: {len(eligible)} eligible, {len(skipped)} skipped.\n")

    if not eligible:
        print("[Batch] All pending products are currently being processed. Nothing to send.")
        pg_cursor.close()
        pg_conn.close()
        return

    # -----------------------------------------------------------------------
    # STEP 3: Send eligible notifications to Service Bus Queue
    # -----------------------------------------------------------------------
    print_step(3, "Send Notifications to Service Bus Queue")

    sent_count = 0
    for row in eligible:
        ts, product_id, notification = row

        # In production, this would send to Azure Service Bus.
        # For this demo, we simulate the send with print output.
        notification_data = json.dumps(notification, indent=6, default=str)

        print(f"    [SEND] Sending to Service Bus Queue:")
        print(f"           Product ID : {product_id}")
        print(f"           Timestamp  : {ts}")
        print(f"           Payload    : {notification_data[:200]}...")
        print()

        # Mark as processed in PostgreSQL
        pg_cursor.execute(MARK_PROCESSED_QUERY, (product_id,))
        pg_conn.commit()
        print(f"    [DB]   Marked as processed in PostgreSQL.\n")

        sent_count += 1

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print_step("✓", "Batch Processing Complete")

    print(f"    Notifications found in PostgreSQL : {len(pending_notifications)}")
    print(f"    Skipped (being processed in Redis): {len(skipped)}")
    print(f"    Sent to Service Bus Queue         : {sent_count}")
    print()

    if skipped:
        print("    Skipped products (currently processing):")
        for row in skipped:
            print(f"      - {row[1]}")
        print()

    # -----------------------------------------------------------------------
    # Cleanup connections
    # -----------------------------------------------------------------------
    pg_cursor.close()
    pg_conn.close()
    print("[Postgres] Connection closed.")
    print("[Redis] Connection closed.")
    print()
    print_separator()
    print("  BATCH PROCESSING FINISHED")
    print_separator()
    print()


if __name__ == "__main__":
    run_batch()
