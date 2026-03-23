-- 2026-03-23 DB Data Fixes
-- Link equipment_types to equipment_categories by name
UPDATE equipment_types et SET category_id = ec.id
FROM equipment_categories ec WHERE ec.name = et.name AND et.category_id IS NULL;

-- Add supplier_rotations for unregistered active suppliers
INSERT INTO supplier_rotations (supplier_id, total_assignments, rejection_count, rotation_position, is_active, is_available, priority_score, created_at, updated_at)
SELECT s.id, 0, 0, 1, true, true, 100.0, NOW(), NOW() FROM suppliers s
LEFT JOIN supplier_rotations sr ON sr.supplier_id = s.id WHERE sr.id IS NULL AND s.is_active = true;

-- Delete junk permissions
DELETE FROM permissions WHERE code LIKE 'filter_resource_%' OR code LIKE '%_test_%';

-- Delete test users
DELETE FROM notifications WHERE user_id IN (92, 93);
DELETE FROM users WHERE id IN (92, 93);

-- Fix tamari region
UPDATE users SET region_id = 1 WHERE id = 91 AND region_id IS NULL;

-- Clean expired tokens/sessions
DELETE FROM otp_tokens WHERE expires_at < NOW();
DELETE FROM sessions WHERE expires_at < NOW();
