-- =============================================================================
-- Sentinel-2 Modified Notifications - Test Data Initialization
-- This file is automatically executed when the PostgreSQL container starts.
-- =============================================================================

-- 1. Create schema
CREATE SCHEMA IF NOT EXISTS events;

-- 2. Create table
CREATE TABLE IF NOT EXISTS events.modified_notifications (
    notification_timestamp TIMESTAMPTZ NOT NULL,
    product_id             TEXT        NOT NULL UNIQUE,
    notification           JSONB       NOT NULL,
    processed              BOOLEAN     NOT NULL DEFAULT FALSE
);

-- 3. Create partial index for batch query performance
-- Only indexes unprocessed rows, keeping the index small and efficient
CREATE INDEX IF NOT EXISTS idx_modified_notifications_pending
ON events.modified_notifications (notification_timestamp)
WHERE processed = FALSE;

-- 4. Configure autovacuum for this table (frequent updates from processed=FALSE→TRUE)
ALTER TABLE events.modified_notifications SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- 5. Create cleanup function to delete processed rows older than 1 week
CREATE OR REPLACE FUNCTION events.cleanup_processed_notifications()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM events.modified_notifications
    WHERE processed = TRUE
      AND notification_timestamp < NOW() - INTERVAL '1 week';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 6. Schedule automatic cleanup using pg_cron (if available) or trigger via external cron
-- To run manually: SELECT events.cleanup_processed_notifications();

-- 7. Insert test data with a variety of scenarios

-- Product 1: Unprocessed, 25 minutes ago → should be picked up by batch
INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '25 minutes',
    '0d2e6901-b963-4718-a96e-17e8b0834b6b',
    '{
        "product_id": "0d2e6901-b963-4718-a96e-17e8b0834b6b",
        "timestamp": "2023-03-15T10:10:31Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A"
    }'::jsonb,
    FALSE
);

-- Product 2: Unprocessed, 18 minutes ago → should be picked up by batch
INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '18 minutes',
    'a1f4c832-5e7d-4a19-b3c1-9d8e2f6a7b50',
    '{
        "product_id": "a1f4c832-5e7d-4a19-b3c1-9d8e2f6a7b50",
        "timestamp": "2023-03-16T10:20:32Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A"
    }'::jsonb,
    FALSE
);

-- Product 3: Unprocessed, 15 minutes ago, but currently being processed (has Redis entry)
-- → should be SKIPPED because Redis shows it is in progress
INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '15 minutes',
    'b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0',
    '{
        "product_id": "b7c3d4e5-6f89-4a2b-c1d3-e5f6a7b8c9d0",
        "timestamp": "2023-03-17T10:10:31Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A"
    }'::jsonb,
    FALSE
);

-- Product 4: Already processed, 30 minutes ago → should NOT be picked up
INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '30 minutes',
    'c8d9e0f1-2a3b-4c5d-6e7f-8a9b0c1d2e3f',
    '{
        "product_id": "c8d9e0f1-2a3b-4c5d-6e7f-8a9b0c1d2e3f",
        "timestamp": "2023-03-14T10:10:31Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A"
    }'::jsonb,
    TRUE
);

-- Product 5: Unprocessed, only 3 minutes ago → should NOT be picked up (too recent)
INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '3 minutes',
    'd9e0f1a2-3b4c-5d6e-7f8a-9b0c1d2e3f4a',
    '{
        "product_id": "d9e0f1a2-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
        "timestamp": "2023-03-18T10:20:32Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A"
    }'::jsonb,
    FALSE
);

-- Product 6: Unprocessed, 12 minutes ago → should be picked up by batch
INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '12 minutes',
    'e0f1a2b3-4c5d-6e7f-8a9b-0c1d2e3f4a5b',
    '{
        "product_id": "e0f1a2b3-4c5d-6e7f-8a9b-0c1d2e3f4a5b",
        "timestamp": "2023-03-19T10:10:31Z",
        "status": "modified",
        "collection": "SENTINEL-2",
        "processingLevel": "L2A"
    }'::jsonb,
    FALSE
);
