"""
Extended Redis seeding for testing - adds 5 products as "processing"
These correspond to Category 3 from additional_test_data.sql
"""

import os
import redis


def seed_additional_redis():
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    print("[Redis] Connecting to Redis...")
    r.ping()
    print("[Redis] Connected successfully.\n")

    # 5 products marked as currently processing
    processing_products = [
        {"product_id": "d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a", "status": "processing"},
        {"product_id": "e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b", "status": "processing"},
        {"product_id": "f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c", "status": "processing"},
        {"product_id": "a4b5c6d7-e8f9-4a0b-1c2d-3e4f5a6b7c8d", "status": "processing"},
        {"product_id": "b5c6d7e8-f9a0-4b1c-2d3e-4f5a6b7c8d9e", "status": "processing"},
    ]

    print(f"[Redis] Seeding {len(processing_products)} products as processing:\n")

    for product in processing_products:
        key = product['product_id']
        r.set(key, product["status"], ex=86400)
        print(f"  SET {key} = {product['status']} (TTL: 1 day)")

    print(f"\n[Redis] Done seeding.\n")

    # Verify
    print("[Redis] Current product keys in Redis:")
    count = 0
    for key in sorted(r.keys("")):
        if key:  # Skip empty keys
            value = r.get(key)
            print(f"  - {key} = {value}")
            count += 1
    print(f"\nTotal: {count} products\n")


if __name__ == "__main__":
    seed_additional_redis()
