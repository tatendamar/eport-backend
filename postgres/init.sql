-- PostgreSQL Initialization Script
-- =============================================================================
-- This script runs when the database container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Grant permissions for pg_stat_statements
GRANT pg_read_all_stats TO warranty_user;

-- Create indexes for better query performance (will be created after tables)
-- The FastAPI app creates tables on startup

-- Example of creating additional indexes after tables exist:
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_warranties_asset_id ON warranties(asset_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_warranties_status ON warranties(warranty_status);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_warranties_registered_at ON warranties(registered_at);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);

-- Performance tuning queries to run manually:
-- ANALYZE; -- Update statistics for query planner
-- VACUUM ANALYZE; -- Clean up and update statistics
