"""
Sentinel-2 Modified Notifications - Batch Processing Application (Demo)

This script simulates the batch processing application workflow:
  1. Read all notifications from the Redis notifications cache (db 0)
  2. Filter notifications older than 10 minutes
  3. Check Redis processing status cache (db 1) to see if each product is currently being processed
  4. Send eligible notifications to the queue (simulated with print output)
  5. Remove sent notifications from the Redis notifications cache
"""

import json
import os
from datetime import datetime, timezone, timedelta

import redis

# ---------------------------------------------------------------------------
# Configuration (reads from environment variables, with localhost defaults)
# ---------------------------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

# db 0 = modified notifications cache
REDIS_NOTIFICATIONS_CONFIG = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 0,
}

# db 1 = processing status cache
REDIS_PROCESSING_CONFIG = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": 1,
}

DELAY_MINUTES = 10


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
    # Connect to Redis notifications cache (db 0)
    # -----------------------------------------------------------------------
    print("\n[Redis] Connecting to notifications cache (db 0)...")
    notifications_client = redis.Redis(**REDIS_NOTIFICATIONS_CONFIG, decode_responses=True)
    notifications_client.ping()
    print("[Redis] Notifications cache connected successfully.")

    # -----------------------------------------------------------------------
    # Connect to Redis processing status cache (db 1)
    # -----------------------------------------------------------------------
    print("\n[Redis] Connecting to processing status cache (db 1)...")
    processing_client = redis.Redis(**REDIS_PROCESSING_CONFIG, decode_responses=True)
    processing_client.ping()
    print("[Redis] Processing status cache connected successfully.")

    # -----------------------------------------------------------------------
    # STEP 1: Read all notifications from the notifications cache
    # -----------------------------------------------------------------------
    print_step(1, "Read Notifications from Redis Cache (db 0)")

    print("[Redis] Scanning all keys in notifications cache...")
    print()

    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=DELAY_MINUTES)
    all_notifications = []

    for key in notifications_client.scan_iter("*"):
        raw_value = notifications_client.get(key)
        if raw_value is None:
            continue
        entry = json.loads(raw_value)
        inserted_at = datetime.fromisoformat(entry["inserted_at"])
        all_notifications.append((key, inserted_at, entry))

    if not all_notifications:
        print("[Redis] No notifications found in cache. Nothing to process.")
        return

    print(f"[Redis] Found {len(all_notifications)} notification(s) in cache.\n")

    # -----------------------------------------------------------------------
    # STEP 2: Filter notifications older than 10 minutes
    # -----------------------------------------------------------------------
    print_step(2, f"Filter Notifications Older Than {DELAY_MINUTES} Minutes")

    print(f"    Cutoff time: {cutoff_time.isoformat()}\n")

    pending_notifications = []

    for product_id, inserted_at, entry in all_notifications:
        if inserted_at <= cutoff_time:
            print(f"    [PENDING] {product_id}")
            print(f"              Inserted at: {inserted_at.isoformat()}")
            pending_notifications.append((product_id, inserted_at, entry))
        else:
            print(f"    [TOO NEW] {product_id}")
            print(f"              Inserted at: {inserted_at.isoformat()} → not yet eligible")

    print(f"\n    {len(pending_notifications)} notification(s) eligible for processing.\n")

    if not pending_notifications:
        print("[Batch] No notifications old enough. Nothing to process.")
        return

    # -----------------------------------------------------------------------
    # STEP 3: Check Redis processing status cache for conflicts
    # -----------------------------------------------------------------------
    print_step(3, "Check Redis Processing Status Cache (db 1)")

    eligible = []
    skipped = []

    for product_id, inserted_at, entry in pending_notifications:
        is_processing = processing_client.exists(product_id)

        if is_processing:
            status = processing_client.get(product_id)
            print(f"    [SKIP] {product_id}")
            print(f"           Processing status key EXISTS with status '{status}' → product is being processed.")
            skipped.append((product_id, inserted_at, entry))
        else:
            print(f"    [OK]   {product_id}")
            print(f"           Processing status key NOT FOUND → product is available.")
            eligible.append((product_id, inserted_at, entry))

    print(f"\n    Summary: {len(eligible)} eligible, {len(skipped)} skipped.\n")

    if not eligible:
        print("[Batch] All pending products are currently being processed. Nothing to send.")
        return

    # -----------------------------------------------------------------------
    # STEP 4: Send eligible notifications to Service Bus Queue
    # -----------------------------------------------------------------------
    print_step(4, "Send Notifications to Service Bus Queue")

    sent_count = 0
    for product_id, inserted_at, entry in eligible:
        notification_data = json.dumps(entry["notification"], indent=6, default=str)

        print(f"    [SEND] Sending to Service Bus Queue:")
        print(f"           Product ID  : {product_id}")
        print(f"           Inserted at : {inserted_at.isoformat()}")
        print(f"           Payload     : {notification_data[:200]}...")
        print()

        # Remove from notifications cache (replaces the old PostgreSQL UPDATE processed=TRUE)
        notifications_client.delete(product_id)
        print(f"    [CACHE] Removed from notifications cache (db 0).\n")

        sent_count += 1

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print_step("✓", "Batch Processing Complete")

    print(f"    Notifications found in cache       : {len(all_notifications)}")
    print(f"    Too new (< {DELAY_MINUTES} min)               : {len(all_notifications) - len(pending_notifications)}")
    print(f"    Skipped (being processed in db 1)  : {len(skipped)}")
    print(f"    Sent to Service Bus Queue           : {sent_count}")
    print()

    if skipped:
        print("    Skipped products (currently processing):")
        for product_id, _, _ in skipped:
            print(f"      - {product_id}")
        print()

    print("[Redis] Done.")
    print()
    print_separator()
    print("  BATCH PROCESSING FINISHED")
    print_separator()
    print()


if __name__ == "__main__":
    run_batch()
