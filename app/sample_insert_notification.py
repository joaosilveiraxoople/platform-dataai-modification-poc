"""
Sample script demonstrating how to insert or update modified notifications
into the Redis notifications cache (db 0).

This script is intended as a reference for external applications that need to
write notifications to the modified notifications Redis cache.

Each notification is stored as:
  - Key: product_id
  - Value: JSON string containing the notification payload and insertion timestamp
"""

import json
import os
from datetime import datetime, timezone

import redis

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REDIS_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "localhost"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
    "db": 0,  # db 0 = modified notifications cache
}


def upsert_notification(r, product_id: str, notification: dict):
    """
    Insert or update a single notification in the Redis notifications cache.

    If a key with the same product_id already exists, it is overwritten
    with the new notification payload and a fresh timestamp.
    """
    entry = {
        "inserted_at": datetime.now(timezone.utc).isoformat(),
        "notification": notification,
    }
    r.set(product_id, json.dumps(entry))
    print(f"[OK] Upserted notification for product: {product_id}")


def upsert_batch(r, notifications: list[dict]):
    """
    Insert or update multiple notifications using a Redis pipeline.
    """
    pipe = r.pipeline()
    for notif in notifications:
        entry = {
            "inserted_at": datetime.now(timezone.utc).isoformat(),
            "notification": notif,
        }
        pipe.set(notif["product_id"], json.dumps(entry))
    pipe.execute()
    print(f"[OK] Batch upserted {len(notifications)} notification(s)")


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("  Sample: Insert/Update Notifications (Redis Notifications Cache)")
    print("=" * 70)

    r = redis.Redis(**REDIS_CONFIG, decode_responses=True)
    r.ping()
    print("\n[Redis] Connected to notifications cache (db 0).\n")

    # --- Example 1: Single upsert ---
    print("--- Single Upsert ---")
    sample_notification = {
        "product_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "timestamp": "2026-03-23T12:00:00Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A",
    }
    upsert_notification(r, sample_notification["product_id"], sample_notification)

    # --- Example 2: Batch upsert (multiple notifications via pipeline) ---
    print("\n--- Batch Upsert (pipeline) ---")
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
    upsert_batch(r, batch_notifications)

    # --- Example 3: Update existing product (same product_id, new payload) ---
    print("\n--- Update Existing Product ---")
    updated_notification = {
        "product_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "timestamp": "2026-03-23T14:00:00Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A",
        "note": "Updated notification - overwrites previous entry",
    }
    upsert_notification(r, updated_notification["product_id"], updated_notification)

    print("\n[Redis] All operations completed successfully.")

    # Verify
    print("\n--- Verification ---")
    for key in sorted(r.keys("*")):
        value = r.get(key)
        print(f"  {key} = {value[:120]}...")
    print(f"\nTotal keys in notifications cache: {r.dbsize()}")
    print("[Redis] Done.\n")
