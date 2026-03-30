# Simulation Instructions

This guide walks you through running the end-to-end simulation of the Sentinel-2 Modified Notifications Batch Processing Application.

Everything runs inside Docker — no local Python installation required.

## Prerequisites

- **Docker Desktop** installed and running

## Architecture

The simulation uses the following Docker containers:

| Container | Image | Description | Port |
|---|---|---|---|
| `sentinel2_redis` | Redis 7 | Notifications cache (db 0) + Processing status cache (db 1) | 6379 |
| `sentinel2_seed_redis` | Python 3.11 | Seeds both Redis databases with test data (runs once) | — |
| `sentinel2_batch` | Python 3.11 | Batch processing application | — |

### Redis Database Layout

A single Redis instance is used with two logical databases:

| Database | Purpose | Key | Value |
|---|---|---|---|
| `db 0` | Notifications cache | `{product_id}` | JSON: `inserted_at` + notification payload |
| `db 1` | Processing status cache | `{product_id}` | Status string (e.g. `"processing"`) with TTL |

---

## Step 1: Start Redis

From the project root directory, start the Redis container:

```powershell
docker compose up -d redis
```

Wait for the container to be healthy:

```powershell
docker compose ps
```

You should see `sentinel2_redis` with a status of `healthy`.

---

## Step 2: Seed Redis with Test Data

Run the seed container to populate both Redis databases:

```powershell
docker compose run --rm seed-redis
```

This seeds:
- **db 0** — 5 notifications with varying ages (5, 15, 20, 25, 30 minutes old)
- **db 1** — 1 product (`b7c3d4e5-6f89-...`) marked as `processing`

---

## Step 3: Inspect Redis — Verify Seed Data

Before running the batch, verify the data was seeded correctly.

### Check db 0 (Notifications Cache)

Count all keys in db 0:

```powershell
docker exec sentinel2_redis redis-cli -n 0 DBSIZE
```

Expected: `(integer) 5`

List all notification keys:

```powershell
docker exec sentinel2_redis redis-cli -n 0 KEYS "*"
```

Inspect a specific notification entry:

```powershell
docker exec sentinel2_redis redis-cli -n 0 GET "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
```

### Check db 1 (Processing Status Cache)

Count all keys in db 1:

```powershell
docker exec sentinel2_redis redis-cli -n 1 DBSIZE
```

Expected: `(integer) 1`

List all processing status keys:

```powershell
docker exec sentinel2_redis redis-cli -n 1 KEYS "*"
```

Check if a specific product is being processed:

```powershell
docker exec sentinel2_redis redis-cli -n 1 GET "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0"
```

Expected: `"processing"`

Check remaining TTL on a processing key:

```powershell
docker exec sentinel2_redis redis-cli -n 1 TTL "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0"
```

---

## Step 4: Run the Batch Processing Application

```powershell
docker compose run --rm batch
```

The script walks through the full workflow with detailed output:

1. **Step 1** — Reads all notifications from Redis db 0
2. **Step 2** — Filters notifications older than 10 minutes
3. **Step 3** — Checks Redis db 1 to see if each product is currently being processed
4. **Step 4** — Sends eligible notifications to the Service Bus Queue (simulated) and removes them from db 0

### Expected Results

Given the seeded test data:

| Product ID | Age | In db 1 (Processing) | Batch Result |
|---|---|---|---|
| `a1b2c3d4-e5f6-...` | 25 min | No | **Sent to queue** |
| `c3d4e5f6-a7b8-...` | 15 min | No | **Sent to queue** |
| `b7c3d4e5-6f89-...` | 20 min | **Yes** | **Skipped** (being processed) |
| `d4e5f6a7-b8c9-...` | 5 min | No | **Too recent** (< 10 min) |
| `e5f6a7b8-c9d0-...` | 30 min | No | **Sent to queue** |

**Summary:** 3 sent to queue, 1 skipped (processing), 1 too recent.

---

## Step 5: Inspect Redis — Verify Batch Results

After the batch runs, verify that processed notifications were removed from db 0.

### Check db 0 — notifications should be reduced

```powershell
docker exec sentinel2_redis redis-cli -n 0 DBSIZE
```

Expected: `(integer) 2` (only the too-recent and the skipped product remain)

List remaining keys:

```powershell
docker exec sentinel2_redis redis-cli -n 0 KEYS "*"
```

You should see only:
- `d4e5f6a7-b8c9-...` (too recent — was not eligible)
- `b7c3d4e5-6f89-...` (was skipped because it is being processed in db 1)

### Check db 1 — processing status should be unchanged

```powershell
docker exec sentinel2_redis redis-cli -n 1 DBSIZE
```

Expected: `(integer) 1` — the batch does not modify db 1.

---

## Step 6: Run Again (Idempotency Check)

Run the batch a second time:

```powershell
docker compose run --rm batch
```

This time, `b7c3d4e5-6f89-...` is still old enough but still locked in db 1, and `d4e5f6a7-b8c9-...` is still too recent. **Zero notifications should be sent.** This confirms the batch application is idempotent.

Verify nothing changed:

```powershell
docker exec sentinel2_redis redis-cli -n 0 DBSIZE
```

Expected: `(integer) 2` (unchanged)

---

## Redis Inspection Quick Reference

All commands below run against the `sentinel2_redis` container.

```powershell
# --- db 0: Notifications Cache ---
docker exec sentinel2_redis redis-cli -n 0 DBSIZE                              # Count keys
docker exec sentinel2_redis redis-cli -n 0 KEYS "*"                            # List all keys
docker exec sentinel2_redis redis-cli -n 0 GET "<product_id>"                  # Get a specific entry
docker exec sentinel2_redis redis-cli -n 0 SCAN 0 COUNT 100                    # Scan keys in batches
docker exec sentinel2_redis redis-cli -n 0 TTL "<product_id>"                  # Check TTL (-1 = no expiry)

# --- db 1: Processing Status Cache ---
docker exec sentinel2_redis redis-cli -n 1 DBSIZE                              # Count keys
docker exec sentinel2_redis redis-cli -n 1 KEYS "*"                            # List all keys
docker exec sentinel2_redis redis-cli -n 1 GET "<product_id>"                  # Get status value
docker exec sentinel2_redis redis-cli -n 1 TTL "<product_id>"                  # Check remaining TTL
docker exec sentinel2_redis redis-cli -n 1 EXISTS "<product_id>"               # Check if key exists (1/0)

# --- General ---
docker exec sentinel2_redis redis-cli INFO keyspace                             # Overview of all dbs with key counts
docker exec sentinel2_redis redis-cli PING                                      # Health check
```

> **Tip:** The `-n <db>` flag selects the database number. Without it, Redis defaults to db 0.

---

## Cleanup

To stop and remove the Docker containers and their data:

```powershell
docker compose down -v
```

---

## Quick Reference (All Commands)

```powershell
# 1. Start Redis
docker compose up -d redis

# 2. Seed Redis test data (db 0 + db 1)
docker compose run --rm seed-redis

# 3. Inspect seeded data
docker exec sentinel2_redis redis-cli -n 0 DBSIZE
docker exec sentinel2_redis redis-cli -n 1 DBSIZE

# 4. Run batch processing
docker compose run --rm batch

# 5. Verify batch results
docker exec sentinel2_redis redis-cli -n 0 DBSIZE
docker exec sentinel2_redis redis-cli -n 0 KEYS "*"

# 6. Run again (idempotency check)
docker compose run --rm batch

# 7. Full keyspace overview
docker exec sentinel2_redis redis-cli INFO keyspace

# Cleanup
docker compose down -v
```

---

## File Overview

| File | Description |
|---|---|
| `docker-compose.yml` | Docker Compose configuration for all services |
| `Dockerfile` | Container image for the Python batch application |
| `seed_redis.py` | Seeds Redis db 0 (notifications) and db 1 (processing status) |
| `seed_redis_extended.py` | Adds additional test data for extended testing |
| `batch_processing.py` | Batch processing application (demo) |
| `SIMULATION_INSTRUCTIONS.md` | This file |
