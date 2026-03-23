# Sentinel-2 Modified Notifications Reprocessing System

A production-ready batch processing system that automatically detects, locks, and requeues Sentinel-2 modified product notifications for reprocessing in the Copernicus Data Space Ecosystem.

**Key Characteristics:**
- Processes ~35 modified notifications per hour globally
- Runs batch job every 10 minutes with automatic conflict prevention
- Prevents duplicate processing through Redis-based distributed locks
- Audit trail preserved via PostgreSQL historical records
- Production-ready Docker deployment

> **📋 For detailed architecture, workflow, and system design, see [SENTINEL2_MODIFIED_NOTIFICATIONS.md](SENTINEL2_MODIFIED_NOTIFICATIONS.md)**


---

## Quick Start

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
├── SENTINEL2_MODIFIED_NOTIFICATIONS.md  # ⭐ Architecture & Workflow
├── docker-compose.yml
├── Dockerfile
├── requirements_batch.txt
└── README.md
```

---

**System Status:** ✅ Production-Ready
