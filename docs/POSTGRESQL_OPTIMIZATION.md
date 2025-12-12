# PostgreSQL Performance Optimization

## Overview

The PostgreSQL configuration has been optimized for a low-memory VPS (512MB RAM). This document explains each optimization and its rationale.

## Memory Configuration

### shared_buffers = 64MB

**What**: Main memory pool for caching database blocks.

**Why**: 25% of total RAM is the recommended starting point. For a 512MB server, 64MB provides adequate cache hit rates without starving the OS.

**Impact**: Faster reads for frequently accessed data.

### effective_cache_size = 128MB

**What**: Estimate of memory available for disk caching by the OS.

**Why**: Helps the query planner decide whether to use sequential scans or index scans. Set conservatively for low-memory environments.

**Impact**: Better query planning decisions.

### work_mem = 2MB

**What**: Memory for sort operations, hash joins, etc.

**Why**: Each operation can use this much memory. Set very conservatively because it multiplies with concurrent operations. Critical for low-memory servers.

**Impact**: Prevents memory exhaustion during complex queries.

### maintenance_work_mem = 32MB

**What**: Memory for maintenance operations (VACUUM, CREATE INDEX, ALTER TABLE).

**Why**: Moderate value balances maintenance speed with memory constraints.

**Impact**: Reasonable index creation and vacuum performance.

## Write-Ahead Log (WAL)

### wal_buffers = 4MB

**What**: Memory for WAL data before writing to disk.

**Why**: Modest buffer appropriate for low-memory environment while still reducing disk I/O during writes.

**Impact**: Better write performance without excessive memory use.

### checkpoint_completion_target = 0.9

**What**: Percentage of checkpoint interval to spread I/O.

**Why**: Spreads checkpoint writes over time to reduce I/O spikes.

**Impact**: More consistent performance.

### max_wal_size = 256MB

**What**: Maximum WAL size before triggering checkpoint.

**Why**: Conservative size appropriate for small disk environments, balancing performance with disk usage.

**Impact**: Reasonable write performance with manageable recovery time.

## Query Planner

### random_page_cost = 1.1

**What**: Relative cost of random disk access vs sequential.

**Why**: SSDs have nearly equal random and sequential access times. Default (4.0) is for HDDs.

**Impact**: Query planner correctly prefers index scans on SSDs.

### effective_io_concurrency = 50

**What**: Number of concurrent I/O operations expected.

**Why**: Moderate value for typical VPS SSD performance. Higher than HDD default (1) but conservative for shared environments.

**Impact**: Better bitmap heap scan performance.

### default_statistics_target = 100

**What**: Amount of statistics collected for query planning.

**Why**: Default (100) is good for most cases. Higher values improve plans but increase ANALYZE time.

**Impact**: More accurate query plans.

## Parallel Query

### max_parallel_workers_per_gather = 2

**What**: Maximum workers for a single parallel query.

**Why**: Limited to avoid overwhelming 2-CPU server.

**Impact**: Faster analytical queries.

### max_parallel_workers = 4

**What**: Total parallel workers available.

**Why**: Allows multiple parallel queries to run concurrently.

**Impact**: Better throughput for complex workloads.

## Auto-vacuum

### autovacuum_vacuum_scale_factor = 0.02

**What**: Fraction of table to trigger vacuum (default 0.2 = 20%).

**Why**: Lower value triggers vacuum more frequently, preventing table bloat.

**Impact**: Smaller tables, more consistent performance.

### autovacuum_analyze_scale_factor = 0.01

**What**: Fraction of table to trigger analyze (default 0.1 = 10%).

**Why**: More frequent statistics updates improve query planning.

**Impact**: Better query plans.

## Connection Settings

### max_connections = 20

**What**: Maximum simultaneous connections.

**Why**: Each connection uses memory (~5-10MB). Limited to 20 for low-memory environments to prevent OOM conditions.

**Impact**: Adequate concurrency for small applications without memory exhaustion.

## Logging (Performance Monitoring)

### log_min_duration_statement = 1000

**What**: Log queries taking longer than 1 second.

**Why**: Identifies slow queries for optimization.

**Impact**: Easy performance troubleshooting.

### log_checkpoints = on

**What**: Log checkpoint information.

**Why**: Helps identify checkpoint-related performance issues.

**Impact**: Better visibility into WAL behavior.

## How to Adjust

For different server specifications:

### 512MB RAM Server (Current)

```
shared_buffers = 64MB
effective_cache_size = 128MB
work_mem = 2MB
maintenance_work_mem = 32MB
max_connections = 20
wal_buffers = 4MB
max_wal_size = 256MB
```

### 1GB RAM Server

```
shared_buffers = 256MB
effective_cache_size = 512MB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 50
wal_buffers = 16MB
max_wal_size = 512MB
```

### 2GB RAM Server

```
shared_buffers = 512MB
effective_cache_size = 1536MB
work_mem = 8MB
maintenance_work_mem = 128MB
max_connections = 100
wal_buffers = 32MB
max_wal_size = 1GB
```

### 4GB RAM Server

```
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB
max_connections = 100
wal_buffers = 64MB
max_wal_size = 2GB
```

### 8GB RAM Server

```
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 32MB
maintenance_work_mem = 512MB
max_connections = 200
```

### 16GB RAM Server

```
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_connections = 300
```

## Monitoring Performance

### Check Cache Hit Ratio

```sql
SELECT 
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit)  as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

Goal: ratio > 0.99 (99% cache hit rate)

### Check Slow Queries

```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### Check Table Bloat

```sql
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Manual Maintenance

```sql
-- Update statistics
ANALYZE;

-- Full vacuum (reclaims space)
VACUUM FULL ANALYZE;

-- Reindex to reduce index bloat
REINDEX DATABASE warranty_db;
```
