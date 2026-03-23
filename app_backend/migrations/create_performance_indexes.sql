
-- 2026-03-23: Additional indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_id ON users(id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_roles_id ON roles(id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_worklogs_status ON worklogs(status);
