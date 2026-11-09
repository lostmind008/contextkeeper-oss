# Database Architecture - Sacred Plan Template

## Overview
This sacred plan defines the core database architecture principles and constraints for the project.

## Core Principles

### Database Technology
- **Primary Database**: PostgreSQL 14+
- **Reasoning**: ACID compliance, mature ecosystem, excellent performance
- **Alternatives Considered**: MySQL (rejected due to licensing), MongoDB (rejected due to ACID requirements)

### Scaling Strategy
- **Read Replicas**: Implement for read-heavy workloads
- **Connection Pooling**: Use PgBouncer for connection management  
- **Sharding**: Horizontal sharding for user data when > 1M users

## Schema Design Standards

### Primary Keys
```sql
-- Always use UUID v4 for primary keys
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- other fields
);
```

### Timestamps
```sql
-- All tables must have these timestamp fields
created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
```

### Soft Deletes
```sql
-- Implement soft deletes for audit trails
deleted_at TIMESTAMP WITH TIME ZONE NULL
```

## Security Requirements

### Encryption
- **At Rest**: All sensitive data encrypted using AES-256
- **In Transit**: All connections must use TLS 1.3+
- **Application Level**: PII encrypted before storage

### Access Control
```sql
-- Implement row-level security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_policy ON users
    FOR ALL TO app_user
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

### Backup Strategy
- **Frequency**: Daily full backups, continuous WAL archiving
- **Retention**: 30 days full backups, 1 year compliance data
- **Testing**: Monthly restore tests required

## Migration Standards

### Backward Compatibility
- New columns must have DEFAULT values or be nullable
- Never drop columns in migrations (mark as unused)
- Index creation must use CONCURRENT option

### Migration Process
```sql
-- Example migration template
BEGIN;

-- Add new column with default
ALTER TABLE users 
ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT false;

-- Create index concurrently (separate transaction)
COMMIT;

CREATE INDEX CONCURRENTLY idx_users_email_verified 
ON users (email_verified) WHERE email_verified = true;
```

## Performance Guidelines

### Indexing Strategy
- All foreign keys must have indexes
- Composite indexes for common query patterns
- Partial indexes for filtered queries

### Query Optimization
- All queries > 100ms must be reviewed
- Use EXPLAIN ANALYZE for query planning
- Implement query timeout (30s max)

## Monitoring and Alerts

### Key Metrics
- Connection count (alert > 80% of max_connections)
- Query response time (alert > 1s average)
- Disk usage (alert > 85%)
- Replication lag (alert > 30s)

### Logging
- Log all DDL statements
- Log queries > 5s execution time  
- Enable pg_stat_statements extension

## Compliance Requirements

### Data Retention
- User data: 7 years after account closure
- Transaction data: 10 years for financial compliance
- Audit logs: 3 years minimum

### GDPR Compliance
- Implement data export functionality
- Support right to erasure (hard delete after soft delete period)
- Data processing logs for auditing

## Approval and Enforcement

This sacred plan requires approval from:
- Database Team Lead
- Security Team  
- Architecture Review Board

**Violations of this plan must be approved through the same process.**

---

**Plan Status**: DRAFT → Requires 2-layer verification for approval
**Last Updated**: [Date]
**Version**: 1.0