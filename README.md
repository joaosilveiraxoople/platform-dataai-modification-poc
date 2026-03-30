# Sentinel-2 Modified Notifications Reprocessing System

## Overview

For Sentinel-2 data in the Copernicus Data Space Ecosystem Catalogue, notifications about updated products can be received as "modified" events. When these notifications are received, the corresponding Sentinel Product must be updated on the STAC Catalog and its files overwritten.

This system handles the workflow for reprocessing Sentinel-2 products when "modified" notifications are received. It maintains data consistency through distributed locking (Redis) and uses Redis as the storage backend for both notifications and processing status.

**Key Characteristics:**
- Processes ~35 modified notifications per hour globally
- Runs batch job every 10 minutes with automatic conflict prevention
- Prevents duplicate processing through Redis-based distributed locks
- Fully Redis-based architecture — no SQL database required

## System Architecture

### System Components Overview

The modified notifications reprocessing system consists of three main components:

1. **Redis Notifications Cache** - Stores notifications awaiting reprocessing
2. **Redis Processing Status Cache** - Tracks the processing status of each product to prevent conflicts
3. **Batch Application** - Sends the modified events to the queue for processing

Redis cache can be the same and the new modifications and status of each product processing can be isolated at redis database level.

### System Workflow

```
1. Notification Received
   ↓
2. Stored in Redis Notifications Cache (db 0)
   Key = product_id, Value = JSON {inserted_at, notification}
   ↓
3. Batch Job Runs Every 10 Minutes
   ├─ Scan: all keys in notifications cache (db 0)
   ├─ Filter: only entries older than 10 minutes
   ├─ Check: Is product in processing status cache (db 1)?
   ├─ If not processing: Send to Service Bus Queue
   └─ Remove entry from notifications cache (db 0)
   ↓
4. Processors Handle Event
   ├─ Update STAC Catalog
   ├─ Overwrite product files
   └─ Delete processing status key from db 1 (marks complete)
```

---

## Redis Notifications Cache (db 0)

The notifications cache stores modified notifications awaiting reprocessing:
- When a "modified" notification is received, it is written to Redis db 0
- The batch application reads from this cache and removes entries after sending them to the queue
- If the same product_id is received again, the entry is overwritten with the latest notification

### Entry Format

Each notification is stored as:
- **Key**: `{product_id}` (e.g., `0d2e6901-b963-4718-a96e-17e8b0834b6b`)
- **Value**: JSON string containing:
  - `inserted_at` — ISO 8601 timestamp when the notification was inserted
  - `notification` — Complete notification payload to be resent to the queue

Example value:
```json
{
  "inserted_at": "2026-03-27T10:15:00+00:00",
  "notification": {
    "product_id": "0d2e6901-b963-4718-a96e-17e8b0834b6b",
    "timestamp": "2026-03-27T10:15:00+00:00",
    "status": "modified",
    "collection": "SENTINEL-2",
    "processingLevel": "L2A"
  }
}
```

---

## Redis Processing Status Cache (db 1)

The processing status cache maintains a record of products currently being processed:
- When processing of a product begins, an entry is written to Redis db 1 with the **Product ID as the key** and **"processing" as the value**
- Once sentinel product is uploaded to STAC Catalog, the corresponding entry is deleted from Redis
- Entries serve as locks to prevent concurrent processing of the same product

### Entry Format

Each product being processed is stored in Redis as:
- **Key**: `{product_id}` (e.g., `0d2e6901-b963-4718-a96e-17e8b0834b6b`)
- **Value**: Status message (e.g., `processing`, or other status values for future extension)
- **TTL**: 1 day (86400 seconds) — keys auto-expire as a safety net to prevent orphaned locks from permanently blocking reprocessing in case a processor crashes or gets stuck without cleaning up its entry

---

## Batch Processing Application Workflow

Every 10 minutes, the batch processing application executes the following steps:

### Step 1: Read All Notifications from Redis Cache (db 0)

Scan all keys in the notifications cache and parse each entry's `inserted_at` timestamp.

### Step 2: Filter Notifications Older Than 10 Minutes

Only notifications with an `inserted_at` timestamp older than 10 minutes are considered eligible. This delay ensures stability and prevents conflicts with in-flight operations.

### Step 3: Check Redis Processing Status Cache (db 1)

For each eligible notification, check if the product is already being processed:
- Query Redis db 1 using the `product_id`
- If an entry exists, the product is currently being processed → skip this notification
- If no entry exists, the product is not being processed → proceed to Step 4

### Step 4: Send Notifications to Service Bus Queue and Remove from Cache

For products that are not currently being processed:
- Send the modified notification to the Service Bus Queue
- Remove the entry from the notifications cache (db 0)
- The queue will pass the notification to processors for reprocessing
- Processors will update the STAC catalog and overwrite previous product files
- Once processing completes, the Redis entry in db 1 for that product is deleted

This workflow ensures no product is reprocessed multiple times simultaneously, maintaining data consistency.

---

## End-to-end Diagram

![alt text](<docs/Data Architecture - Page 13 (2).png>)

---

## Directory Structure

```
sandbox/
├── app/                              # Application code
│   ├── batch_processing.py           # Main batch job (reads from db 0, checks db 1)
│   ├── sample_insert_notification.py # Reference script for inserting notifications
│   ├── seed_redis.py                 # Seeds test data into both Redis caches
│   └── seed_redis_extended.py        # Extended test data seeding
│
├── docs/                             # Additional documentation
│   ├── SIMULATION_INSTRUCTIONS.md
│   └── EXTENDED_TESTING.md
│
├── docker-compose.yml
├── Dockerfile
├── README.md                         # This file
└── .gitignore
```

---

## Demo

### Prerequisites
- Docker & Docker Compose
- PowerShell 5.1+ (Windows) or bash (Linux/Mac)

### 1. Start the System

```powershell
docker compose up -d
```

This starts two services: redis and seed-redis (which populates test data).

### 2. Verify Services Are Healthy

```powershell
docker compose ps
```

All services should show status `healthy` or `running`.

### 3. Run the Batch Processing Job

```powershell
docker compose run --rm batch
```

### 4. Verify Results

```powershell
# Check notifications cache (db 0) — processed entries should be removed
docker compose exec redis redis-cli -n 0 KEYS '*'

# Check processing status cache (db 1)
docker compose exec redis redis-cli -n 1 KEYS '*'

# Inspect a specific notification entry
docker compose exec redis redis-cli -n 0 GET "<product_id>"
```

---

## Additional Documentation

- **[Simulation Instructions](docs/SIMULATION_INSTRUCTIONS.md)** — Step-by-step demo walkthrough
- **[Extended Testing Scenarios](docs/EXTENDED_TESTING.md)** — Advanced test cases with additional products
