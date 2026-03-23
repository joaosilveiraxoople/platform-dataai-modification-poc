# Extended Testing with 20 Additional Products

This guide walks you through adding 20 more test products to your database for comprehensive batch processing testing.

## Test Data Summary

| Category | Count | Processed | Age | Redis Lock | Result |
|---|---|---|---|---|---|
| Already Processed | 5 | YES | 45-80 min | No | **Not queried** |
| Too Recent | 5 | NO | 1-8 min | No | **Not queried** |
| In Redis (Locked) | 5 | NO | 22-32 min | YES | **Skipped** |
| Eligible for Queue | 5 | NO | 16-35 min | No | **Sent to queue** |
| **Original Products** | **6** | Mixed | Mixed | 1 | **Results vary** |
| **TOTAL** | **26** | — | — | — | — |

## Step-by-Step Instructions

### Step 1: Clean Slate (Optional)

If you've already run tests, reset everything:

```powershell
docker compose down -v
docker image rm sandbox-seed-redis sandbox-batch 2>$null
docker compose up -d postgres redis
```

### Step 2: Add Initial 6 Products + 20 Extended Products

The database is automatically seeded with the initial 6 products. Now add the 20 additional products:

```powershell
docker exec sentinel2_postgres psql -U sentinel -d sentinel_events < sql/additional_test_data.sql
```

### Step 3: Verify the Data

Check all 26 products are in the database:

```powershell
docker exec sentinel2_postgres psql -U sentinel -d sentinel_events -c "SELECT COUNT(*) as total_products FROM events.modified_notifications;"
```

Should show: `26`

### Step 4: Seed Extended Redis Data

Mark the 5 Category 3 products (locked in Redis):

**Option A: Using Docker Compose**

First, update `docker-compose.yml` to add the extended seed service in the services section:

```yaml
  seed-redis-extended:
    build: .
    container_name: sentinel2_seed_redis_extended
    command: python seed_redis_extended.py
    environment:
      REDIS_HOST: redis
    depends_on:
      redis:
        condition: service_healthy
```

Then run:

```powershell
docker compose build --no-cache
docker compose run --rm seed-redis-extended
```

**Option B: Using Direct Redis Commands**

Or manually add them to Redis:

```powershell
docker exec sentinel2_redis redis-cli SET "processing:d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a" "processing"
docker exec sentinel2_redis redis-cli SET "processing:e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b" "processing"
docker exec sentinel2_redis redis-cli SET "processing:f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c" "processing"
docker exec sentinel2_redis redis-cli SET "processing:a4b5c6d7-e8f9-4a0b-1c2d-3e4f5a6b7c8d" "processing"
docker exec sentinel2_redis redis-cli SET "processing:b5c6d7e8-f9a0-4b1c-2d3e-4f5a6b7c8d9e" "processing"
```

### Step 5: Verify Redis Data

```powershell
docker exec sentinel2_redis redis-cli KEYS "processing:*" | Measure-Object
```

Should show `6` keys total (1 original + 5 new).

### Step 6: Run the Batch Processing

```powershell
docker compose run --rm batch
```

### Expected Results

**Summary from batch output:**
- **Total queried:** 11 (original 4 + extended 5 eligible + extended others that qualify)
- **Skipped (in Redis):** 6 (1 original + 5 extended)
- **Sent to queue:** 5 (5 eligible from extended category)
- **Not queried:** 10 (5 already processed + 5 too recent)

### Step 7: Verify Results in PostgreSQL

```powershell
docker exec sentinel2_postgres psql -U sentinel -d sentinel_events -c "SELECT COUNT(*) as processed_true FROM events.modified_notifications WHERE processed = TRUE;"
```

Should show more than the initial 1 (the 5 eligible will be marked as processed).

### Step 8: Run Idempotency Check

```powershell
docker compose run --rm batch
```

Second run should find no eligible products (all new ones are either processed, too recent, or locked).

## File Reference

| File | Purpose |
|---|---|
| `sql/additional_test_data.sql` | 20 new products for extended testing |
| `seed_redis_extended.py` | Seeds 5 products as "processing" in Redis |
| `EXTENDED_TESTING.md` | This file |

## Cleanup

To reset and start over:

```powershell
docker compose down -v
docker image rm sandbox-seed-redis sandbox-batch 2>$null
```
