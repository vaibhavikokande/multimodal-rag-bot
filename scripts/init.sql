-- PostgreSQL initialization script
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Full text search configuration
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_text_search
    ON documents USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(raw_text, '')));
