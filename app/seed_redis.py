"""
Seed Redis with test data for both caches:
  - db 0: Modified notifications cache (notifications awaiting reprocessing)
  - db 1: Processing status cache (products currently being processed)

This script populates test data to simulate a realistic batch processing scenario.
"""

import json
import os
from datetime import datetime, timezone, timedelta

import redis


def seed_redis():
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    # Connect to notifications cache (db 0)
    notifications_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    notifications_client.ping()

    # Connect to processing status cache (db 1)
    processing_client = redis.Redis(host=redis_host, port=redis_port, db=1, decode_responses=True)
    processing_client.ping()

    notifications_client.flushdb()
    processing_client.flushdb()
    print("[Redis] Cleared existing test data from db 0 and db 1.\n")

    now = datetime.now(timezone.utc)

    # -----------------------------------------------------------------------
    # Seed notifications cache (db 0)
    # -----------------------------------------------------------------------
    print("--- Seeding Notifications Cache (db 0) ---\n")

    notifications = [
        # Product 1: Inserted 25 minutes ago → should be picked up by batch
        {
            "product_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            "inserted_at": (now - timedelta(minutes=25)).isoformat(),
            "notification": {
                "product_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
                "timestamp": (now - timedelta(minutes=25)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
        # Product 2: Inserted 15 minutes ago → should be picked up by batch
        {
            "product_id": "c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
            "inserted_at": (now - timedelta(minutes=15)).isoformat(),
            "notification": {
                "product_id": "c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
                "timestamp": (now - timedelta(minutes=15)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L1C",
            },
        },
        # Product 3: Inserted 20 minutes ago → eligible but will be skipped (processing in db 1)
        {
            "product_id": "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0",
            "inserted_at": (now - timedelta(minutes=20)).isoformat(),
            "notification": {
                "product_id": "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0",
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
        # Product 4: Inserted 5 minutes ago → too recent, should NOT be picked up
        {
            "product_id": "d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
            "inserted_at": (now - timedelta(minutes=5)).isoformat(),
            "notification": {
                "product_id": "d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
                "timestamp": (now - timedelta(minutes=5)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L2A",
            },
        },
        # Product 5: Inserted 30 minutes ago → should be picked up by batch
        {
            "product_id": "e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b",
            "inserted_at": (now - timedelta(minutes=30)).isoformat(),
            "notification": {
                "product_id": "e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b",
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "status": "modified",
                "collection": "SENTINEL-2",
                "processingLevel": "L1C",
            },
        },
    ]

    for item in notifications:
        entry = {
            "inserted_at": item["inserted_at"],
            "notification": item["notification"],
        }
        notifications_client.set(item["product_id"], json.dumps(entry))
        print(f"  SET {item['product_id']}")
        print(f"      inserted_at: {item['inserted_at']}")

    print(f"\n[Redis] Seeded {len(notifications)} notification(s) in db 0.\n")

    # -----------------------------------------------------------------------
    # Seed processing status cache (db 1)
    # -----------------------------------------------------------------------
    print("--- Seeding Processing Status Cache (db 1) ---\n")

    processing_products = [
        {
            "product_id": "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0",
            "status": "processing",
        },
    ]

    for product in processing_products:
        key = product["product_id"]
        processing_client.set(key, product["status"], ex=604800)
        print(f"  SET {key} = {product['status']} (TTL: 1 week)")

    print(f"\n[Redis] Seeded {len(processing_products)} product(s) as currently processing in db 1.\n")

    # -----------------------------------------------------------------------
    # Verify
    # -----------------------------------------------------------------------
    print("--- Verification ---\n")

    print("[db 0] Notifications cache:")
    for key in sorted(notifications_client.keys("*")):
        value = notifications_client.get(key)
        print(f"  {key} = {value[:100]}...")
    print(f"  Total: {notifications_client.dbsize()} keys\n")

    print("[db 1] Processing status cache:")
    for key in sorted(processing_client.keys("*")):
        value = processing_client.get(key)
        print(f"  {key} = {value}")
    print(f"  Total: {processing_client.dbsize()} keys\n")

    print("[Redis] Done.\n")


if __name__ == "__main__":
    seed_redis()
