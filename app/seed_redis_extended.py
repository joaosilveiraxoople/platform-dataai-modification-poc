"""
Extended Redis seeding for testing - adds additional notifications and
processing status entries for more comprehensive test scenarios.

Run after seed_redis.py to add more data without clearing existing entries.
"""

import json
import os
from datetime import datetime, timezone, timedelta

import redis


def seed_additional_redis():
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    # Connect to notifications cache (db 0)
    notifications_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    notifications_client.ping()

    # Connect to processing status cache (db 1)
    processing_client = redis.Redis(host=redis_host, port=redis_port, db=1, decode_responses=True)
    processing_client.ping()

    print("[Redis] Connected to both caches.\n")

    now = datetime.now(timezone.utc)

    # -----------------------------------------------------------------------
    # Additional notifications (db 0)
    # -----------------------------------------------------------------------
    print("--- Seeding Additional Notifications (db 0) ---\n")

    additional_notifications = [
        {
            "product_id": "d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a",
            "inserted_at": (now - timedelta(minutes=45)).isoformat(),
            "notification": {
                "product_id": "d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a",
                "timestamp": (now - timedelta(minutes=45)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
        {
            "product_id": "e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b",
            "inserted_at": (now - timedelta(minutes=40)).isoformat(),
            "notification": {
                "product_id": "e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b",
                "timestamp": (now - timedelta(minutes=40)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L1C",
            },
        },
        {
            "product_id": "f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c",
            "inserted_at": (now - timedelta(minutes=35)).isoformat(),
            "notification": {
                "product_id": "f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c",
                "timestamp": (now - timedelta(minutes=35)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
        {
            "product_id": "a4b5c6d7-e8f9-4a0b-1c2d-3e4f5a6b7c8d",
            "inserted_at": (now - timedelta(minutes=22)).isoformat(),
            "notification": {
                "product_id": "a4b5c6d7-e8f9-4a0b-1c2d-3e4f5a6b7c8d",
                "timestamp": (now - timedelta(minutes=22)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
        {
            "product_id": "b5c6d7e8-f9a0-4b1c-2d3e-4f5a6b7c8d9e",
            "inserted_at": (now - timedelta(minutes=18)).isoformat(),
            "notification": {
                "product_id": "b5c6d7e8-f9a0-4b1c-2d3e-4f5a6b7c8d9e",
                "timestamp": (now - timedelta(minutes=18)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L1C",
            },
        },
        # Recent notification — should NOT be picked up by batch
        {
            "product_id": "c6d7e8f9-a0b1-4c2d-3e4f-5a6b7c8d9e0f",
            "inserted_at": (now - timedelta(minutes=3)).isoformat(),
            "notification": {
                "product_id": "c6d7e8f9-a0b1-4c2d-3e4f-5a6b7c8d9e0f",
                "timestamp": (now - timedelta(minutes=3)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
    ]

    pipe = notifications_client.pipeline()
    for item in additional_notifications:
        entry = {
            "inserted_at": item["inserted_at"],
            "notification": item["notification"],
        }
        pipe.set(item["product_id"], json.dumps(entry))
        print(f"  SET {item['product_id']}")
        print(f"      inserted_at: {item['inserted_at']}")
    pipe.execute()

    print(f"\n[Redis] Seeded {len(additional_notifications)} additional notification(s) in db 0.\n")

    # -----------------------------------------------------------------------
    # Additional processing status entries (db 1)
    # -----------------------------------------------------------------------
    print("--- Seeding Additional Processing Status (db 1) ---\n")

    additional_processing = [
        {"product_id": "d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a", "status": "processing"},
        {"product_id": "e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b", "status": "processing"},
        {"product_id": "f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c", "status": "processing"},
    ]

    for product in additional_processing:
        key = product["product_id"]
        processing_client.set(key, product["status"], ex=604800)
        print(f"  SET {key} = {product['status']} (TTL: 1 day)")

    print(f"\n[Redis] Seeded {len(additional_processing)} additional processing status entries in db 1.\n")

    # -----------------------------------------------------------------------
    # Verify totals
    # -----------------------------------------------------------------------
    print("--- Verification ---\n")

    print(f"[db 0] Notifications cache: {notifications_client.dbsize()} total keys")
    for key in sorted(notifications_client.keys("*")):
        value = notifications_client.get(key)
        print(f"  {key} = {value[:100]}...")

    print(f"\n[db 1] Processing status cache: {processing_client.dbsize()} total keys")
    for key in sorted(processing_client.keys("*")):
        value = processing_client.get(key)
        print(f"  {key} = {value}")

    print(f"\n[Redis] Done.\n")


if __name__ == "__main__":
    seed_additional_redis()
