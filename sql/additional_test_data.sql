-- =============================================================================
-- Additional Test Data - 20 more products for extended testing
-- Add these to your PostgreSQL database after the initial 6 products
-- =============================================================================

-- ============================================================================
-- CATEGORY 1: Already Processed (5 products)
-- These should NOT be picked up - processed = TRUE
-- ============================================================================

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '45 minutes',
    'f1a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c',
    '{"product_id": "f1a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    TRUE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '50 minutes',
    'a2b3c4d5-e6f7-4a8b-9c0d-1e2f3a4b5c6d',
    '{"product_id": "a2b3c4d5-e6f7-4a8b-9c0d-1e2f3a4b5c6d", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    TRUE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '60 minutes',
    'b3c4d5e6-f7a8-4b9c-0d1e-2f3a4b5c6d7e',
    '{"product_id": "b3c4d5e6-f7a8-4b9c-0d1e-2f3a4b5c6d7e", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    TRUE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '70 minutes',
    'c4d5e6f7-a8b9-4c0d-1e2f-3a4b5c6d7e8f',
    '{"product_id": "c4d5e6f7-a8b9-4c0d-1e2f-3a4b5c6d7e8f", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    TRUE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '80 minutes',
    'd5e6f7a8-b9c0-4d1e-2f3a-4b5c6d7e8f9a',
    '{"product_id": "d5e6f7a8-b9c0-4d1e-2f3a-4b5c6d7e8f9a", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    TRUE
);

-- ============================================================================
-- CATEGORY 2: Too Recent (5 products)
-- These should NOT be picked up - within 10 minute window (processed = FALSE)
-- ============================================================================

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '1 minute',
    'e6f7a8b9-c0d1-4e2f-3a4b-5c6d7e8f9a0b',
    '{"product_id": "e6f7a8b9-c0d1-4e2f-3a4b-5c6d7e8f9a0b", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '2 minutes',
    'f7a8b9c0-d1e2-4f3a-4b5c-6d7e8f9a0b1c',
    '{"product_id": "f7a8b9c0-d1e2-4f3a-4b5c-6d7e8f9a0b1c", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '4 minutes',
    'a8b9c0d1-e2f3-4a4b-5c6d-7e8f9a0b1c2d',
    '{"product_id": "a8b9c0d1-e2f3-4a4b-5c6d-7e8f9a0b1c2d", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '6 minutes',
    'b9c0d1e2-f3a4-4b5c-6d7e-8f9a0b1c2d3e',
    '{"product_id": "b9c0d1e2-f3a4-4b5c-6d7e-8f9a0b1c2d3e", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '8 minutes',
    'c0d1e2f3-a4b5-4c6d-7e8f-9a0b1c2d3e4f',
    '{"product_id": "c0d1e2f3-a4b5-4c6d-7e8f-9a0b1c2d3e4f", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

-- ============================================================================
-- CATEGORY 3: Marked as Processing in Redis (5 products)
-- These should be SKIPPED by batch - in Redis as processing (processed = FALSE, 10+ min old)
-- ============================================================================

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '22 minutes',
    'd1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a',
    '{"product_id": "d1e2f3a4-b5c6-4d7e-8f9a-0b1c2d3e4f5a", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '24 minutes',
    'e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b',
    '{"product_id": "e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '26 minutes',
    'f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c',
    '{"product_id": "f3a4b5c6-d7e8-4f9a-0b1c-2d3e4f5a6b7c", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '28 minutes',
    'a4b5c6d7-e8f9-4a0b-1c2d-3e4f5a6b7c8d',
    '{"product_id": "a4b5c6d7-e8f9-4a0b-1c2d-3e4f5a6b7c8d", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '32 minutes',
    'b5c6d7e8-f9a0-4b1c-2d3e-4f5a6b7c8d9e',
    '{"product_id": "b5c6d7e8-f9a0-4b1c-2d3e-4f5a6b7c8d9e", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

-- ============================================================================
-- CATEGORY 4: Eligible for Queue (5 products)
-- These SHOULD be sent to queue - 10+ min old, not in Redis (processed = FALSE)
-- ============================================================================

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '16 minutes',
    'c6d7e8f9-a0b1-4c2d-3e4f-5a6b7c8d9e0f',
    '{"product_id": "c6d7e8f9-a0b1-4c2d-3e4f-5a6b7c8d9e0f", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '19 minutes',
    'd7e8f9a0-b1c2-4d3e-4f5a-6b7c8d9e0f1a',
    '{"product_id": "d7e8f9a0-b1c2-4d3e-4f5a-6b7c8d9e0f1a", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '21 minutes',
    'e8f9a0b1-c2d3-4e4f-5a6b-7c8d9e0f1a2b',
    '{"product_id": "e8f9a0b1-c2d3-4e4f-5a6b-7c8d9e0f1a2b", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '27 minutes',
    'f9a0b1c2-d3e4-4f5a-6b7c-8d9e0f1a2b3c',
    '{"product_id": "f9a0b1c2-d3e4-4f5a-6b7c-8d9e0f1a2b3c", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);

INSERT INTO events.modified_notifications (notification_timestamp, product_id, notification, processed)
VALUES (
    NOW() - INTERVAL '35 minutes',
    'a0b1c2d3-e4f5-4a6b-7c8d-9e0f1a2b3c4d',
    '{"product_id": "a0b1c2d3-e4f5-4a6b-7c8d-9e0f1a2b3c4d", "status": "modified", "collection": "SENTINEL-2"}'::jsonb,
    FALSE
);
