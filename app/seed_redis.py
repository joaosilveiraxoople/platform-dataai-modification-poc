"""
Seed Redis with test data to simulate products currently being processed.

This script adds one entry to Redis to represent a product that is
currently being processed. The batch application should detect this
entry and skip that product.
"""

import os

import redis


def seed_redis():
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    r.flushdb()
    print("[Redis] Cleared existing test data.\n")

    # Product 3 from the SQL init data is "currently being processed"
    processing_products = [
        {
            "product_id": "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0",
            "status": "processing",
        },
    ]

    for product in processing_products:
        key = product['product_id']
        r.set(key, product["status"], ex=86400)
        print(f"[Redis] SET {key} = {product['status']} (TTL: 1 day)")

    print(f"\n[Redis] Seeded {len(processing_products)} product(s) as currently processing.")
    print("[Redis] Done.\n")

    # Verify
    print("[Redis] Current keys in Redis:")
    for key in sorted(r.keys("")):
        if key:  # Skip empty keys
            print(f"  - {key} = {r.get(key)}")


if __name__ == "__main__":
    seed_redis()
