# Sentinel-2 Modified Notifications Reprocessing System

## Overview

For Sentinel-2 data in the Copernicus Data Space Ecosystem Catalogue, notifications about updated products can be received as "modified" events. When these notifications are received, the corresponding Sentinel Product must be updated on the STAC Catalog and its files overwritten.

This system handles the workflow for reprocessing Sentinel-2 products when "modified" notifications are received. It maintains data consistency through distributed locking (Redis) and provides reliable event tracking via PostgreSQL.

**Key Characteristics:**
- Processes ~35 modified notifications per hour globally
- Runs batch job every 10 minutes with automatic conflict prevention
- Prevents duplicate processing through Redis-based distributed locks
- Audit trail preserved via PostgreSQL historical records

## System Architecture

### System Components Overview

The modified notifications reprocessing system consists of three main components:

1. **PostgreSQL Table** - Stores notifications awaiting reprocessing
2. **Redis Cache** - Tracks the processing status of each product to prevent conflicts
3. **Batch application** - Sends the modified events to the queue for processing

### System Workflow

```
1. Notification Received
   ↓
2. Stored in PostgreSQL (events.modified_notifications table)
   ↓
3. Batch Job Runs Every 10 Minutes
   ├─ Query: unprocessed events older than 10 minutes
   ├─ Check: Is product locked in Redis? (processing lock = product_id key)
   ├─ If unlocked: Send to Service Bus Queue
   └─ Mark as processed in PostgreSQL
   ↓
4. Processors Handle Event
   ├─ Update STAC Catalog
   ├─ Overwrite product files
   └─ Delete Redis lock (marks complete)
```

---

## PostgreSQL Notifications Table

PostgreSQL is used for the following reasons:
- Efficient querying and batch operations
- Scalability is not a concern (average of 35 modifications per hour globally; PostgreSQL supports 100+ connections by default)
- Historical record tracking for audit and debugging purposes

**Postgres instance**: TBD with Infra team

**Database Name**: TBD depending on Postgres instance

**Schema Name**: events

**Table Name**: modified_notifications

### Table Schema

| Column Name | Data Type | Description |
|---|---|---|
| notification_timestamp | TIMESTAMPTZ | Timestamp when the notification was received |
| product_id | TEXT | Sentinel-2 product identifier to be reprocessed |
| notification | JSONB | Complete JSON notification payload to be resent to the queue |
| processed | BOOLEAN | Processing status: True if sent to queue, False if pending |

This table maintains both historical records and notifications pending reprocessing.

### DDL Create Table Statement

```sql
CREATE TABLE events.modified_notifications (
    notification_timestamp TIMESTAMPTZ NOT NULL,
    product_id             TEXT        NOT NULL UNIQUE,
    notification           JSONB       NOT NULL,
    processed              BOOLEAN     NOT NULL DEFAULT FALSE
);
```

---

## Redis Cache for Processing Status

The Redis cache maintains a record of products currently being processed:
- When processing of a product begins, an entry is written to Redis with the **Product ID as the key** and **"processing" as the value**
- Once sentinel product is uploaded to STAC Catalog, the corresponding entry is deleted from Redis
- Entries serve as locks to prevent concurrent processing of the same product

### Redis Entry Format

Each product being processed is stored in Redis as:
- **Key**: `{product_id}` (e.g., `0d2e6901-b963-4718-a96e-17e8b0834b6b`)
- **Value**: Status message (e.g., `processing`, or other status values for future extension)
- **TTL**: 1 day (86400 seconds) — keys auto-expire as a safety net to prevent orphaned locks from permanently blocking reprocessing in case a processor crashes or gets stuck without cleaning up its entry

---

## Batch Processing Application Workflow

Every 10 minutes, the batch processing application executes the following steps:

### Step 1: Query PostgreSQL for Pending Notifications

Retrieve all unprocessed notifications that are older than 10 minutes (this delay ensures stability and prevents conflicts):

```sql
SELECT
    notification_timestamp,
    product_id,
    notification
FROM notifications
WHERE processed = FALSE
  AND notification_timestamp <= NOW() - INTERVAL '10 minutes'
ORDER BY notification_timestamp;
```

### Step 2: Check Redis Cache for Product Processing Status

For each notification retrieved from PostgreSQL, check if the product is already being processed:
- Query Redis cache using the `product_id`
- If an entry exists in Redis, the product is currently being processed → skip this notification
- If no entry exists in Redis, the product is not being processed → proceed to Step 3

### Step 3: Send Notifications to Service Bus Queue for processing

For products that are not currently being processed (not found in Redis cache):
- Send the modified notification to the Service Bus Queue
- The queue will pass the notification to processors for reprocessing
- Processors will update the STAC catalog and overwrite previous product files
- Once processing completes, the Redis entry for that product is deleted

This workflow ensures no product is reprocessed multiple times simultaneously, maintaining data consistency.

---

## End-to-end Diagram

![alt text](<docs/Data Architecture - Page 13 (2).png>)

---

## Directory Structure

```
sandbox/
├── app/                          # Application code
│   ├── batch_processing.py       # Main batch job
│   ├── sample_insert_notification.py
│   ├── seed_redis.py
│   └── seed_redis_extended.py
│
├── docs/                         # Additional documentation
│   ├── SIMULATION_INSTRUCTIONS.md
│   ├── EXTENDED_TESTING.md
│   └── Data Architecture Lucid Chart.png
│
├── sql/                          # Database initialization files
│   ├── init_test_data.sql
│   └── additional_test_data.sql
│
├── docker-compose.yml
├── Dockerfile
├── requirements_batch.txt
├── README.md                     # This file
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

This starts three services: postgres, redis, and seed-redis.

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
# Check PostgreSQL for processed events
docker compose exec postgres psql -U sentinel -d sentinel_events -c "SELECT product_id, processed FROM events.modified_notifications;"

# Check Redis locks
docker compose exec redis redis-cli KEYS '*'
```

---



## Additional Documentation

- **[Simulation Instructions](docs/SIMULATION_INSTRUCTIONS.md)** — Step-by-step demo walkthrough
- **[Extended Testing Scenarios](docs/EXTENDED_TESTING.md)** — Advanced test cases with 20 products
