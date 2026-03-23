# Simulation Instructions

This guide walks you through running the end-to-end simulation of the Sentinel-2 Modified Notifications Batch Processing Application.

Everything runs inside Docker — no local Python installation required.

## Prerequisites

- **Docker Desktop** installed and running

## Architecture

The simulation uses the following Docker containers:

| Container | Image | Description | Port |
|---|---|---|---|
| `sentinel2_postgres` | PostgreSQL 16 | Stores modified notifications | 5432 |
| `sentinel2_redis` | Redis 7 | Tracks products currently being processed | 6379 |
| `sentinel2_seed_redis` | Python 3.11 | Seeds Redis with test data (runs once) | — |
| `sentinel2_batch` | Python 3.11 | Batch processing application | — |

---

## Step 1: Start PostgreSQL and Redis

From the project root directory, start the infrastructure containers:

```powershell
docker compose up -d postgres redis
```

Wait for both containers to be healthy:

```powershell
docker compose ps
```

You should see both `sentinel2_postgres` and `sentinel2_redis` with a status of `healthy`.

> **Note:** The PostgreSQL container automatically runs `init_test_data.sql` on first startup, creating the schema, table, and 6 test notifications.

> **Port:** PostgreSQL is exposed on port **5433** externally (to avoid conflicts with any local PostgreSQL instance). Internal Docker communication uses the default port 5432.

---

## Step 2: Seed Redis with Test Data

Run the Redis seed container to simulate one product being currently processed:

```powershell
docker compose run --rm seed-redis
```

**Expected output:** One product (`b7c3d4e5-6f89-...`) is marked as `processing` in Redis.

---

## Step 3: Run the Batch Processing Application

```powershell
docker compose run --rm batch
```

The script will walk through the full batch workflow with detailed output:

1. **Step 1** — Queries PostgreSQL and finds all unprocessed notifications older than 10 minutes
2. **Step 2** — Checks Redis for each product to see if it is currently being processed
3. **Step 3** — Sends eligible notifications to the Service Bus Queue (simulated)

### Expected Results

Given the test data provided:

| Product | Product ID | Age | Processed | In Redis | Batch Result |
|---|---|---|---|---|---|
| Product 1 | `0d2e6901-b963-...` | 25 min | No | No | **Sent to queue** |
| Product 2 | `a1f4c832-5e7d-...` | 18 min | No | No | **Sent to queue** |
| Product 3 | `b7c3d4e5-6f89-...` | 15 min | No | **Yes** | **Skipped** (being processed) |
| Product 4 | `c8d9e0f1-2a3b-...` | 30 min | **Yes** | No | Not queried (already processed) |
| Product 5 | `d9e0f1a2-3b4c-...` | 3 min | No | No | Not queried (too recent) |
| Product 6 | `e0f1a2b3-4c5d-...` | 12 min | No | No | **Sent to queue** |

**Summary:** 4 notifications queried, 1 skipped, 3 sent to queue.

---

## Step 4: Verify Results

After running the batch, you can verify the changes in PostgreSQL:

```powershell
docker exec -it sentinel2_postgres psql -U sentinel -d sentinel_events -c "SELECT product_id, processed FROM events.modified_notifications ORDER BY notification_timestamp;"
```

Products 1, 2, and 6 should now show `processed = true`.

---

## Step 5: Run Again (Idempotency Check)

Run the batch container a second time:

```powershell
docker compose run --rm batch
```

This time, only Product 3 would be eligible but it is still locked in Redis, so **zero notifications should be sent**. This confirms the batch application is idempotent.

---

## Cleanup

To stop and remove the Docker containers and their data:

```powershell
docker compose down -v
```

---

## Quick Reference (All Commands)

```powershell
# 1. Start infrastructure
docker compose up -d postgres redis

# 2. Seed Redis test data
docker compose run --rm seed-redis

# 3. Run batch processing
docker compose run --rm batch

# 4. Verify results in PostgreSQL
docker exec sentinel2_postgres psql -U sentinel -d sentinel_events -c "SELECT product_id, processed FROM events.modified_notifications ORDER BY notification_timestamp;"

# 5. Run again (idempotency check)
docker compose run --rm batch

# Cleanup
docker compose down -v
```

---

## File Overview

| File | Description |
|---|---|
| `docker-compose.yml` | Docker Compose configuration for all services |
| `Dockerfile` | Container image for the Python batch application |
| `init_test_data.sql` | SQL script to create schema, table, and insert test data |
| `seed_redis.py` | Python script to seed Redis with simulated processing entries |
| `batch_processing.py` | Python batch processing application (demo) |
| `requirements_batch.txt` | Python dependencies for the batch script |
| `SIMULATION_INSTRUCTIONS.md` | This file |
