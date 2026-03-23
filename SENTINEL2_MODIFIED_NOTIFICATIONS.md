# Sentinel-2 Modified Notifications Process

For Sentinel-2 data in the Copernicus Data Space Ecosystem Catalogue, notifications about updated products can be received as "modified" events. When these notifications are received, the corresponding Sentinel Product must be updated on the STAC Catalog and its files overwritten.

To handle this process, a separate Copernicus Subscription will be created to capture only "modified" notifications.

This subscription will be defined like the existing subscription for "created" notifications with the same type and Area of Interest (AOI) defined, but configured to process "modified" notifications instead.

The subscription will push new events through a Python function to a PostgreSQL table.

The system will insert a new row for products with no existing notification, or update an existing row if a notification for that product already exists.

## System Components Overview

The modified notifications reprocessing system  of three main components:

1. **PostgreSQL Table** - Stores notifications awaiting reprocessing
2. **Redis Cache** - Tracks the processing status of each product to prevent conflicts
3. **Batch application** - Batch application that sends the modified events to the queue for processing

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
![alt text](<Data Architecture - Page 13 (2).png>)