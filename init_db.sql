-- Database initialization script for LangGraph checkpointing

-- Create checkpoints table (LangGraph will create this automatically, but we can prepare it)
-- This file can be extended with additional setup as needed

-- Create extension for UUID support if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Exact normalized query cache for paper search results.
CREATE TABLE IF NOT EXISTS paper_search_cache (
	query_key TEXT PRIMARY KEY,
	normalized_query TEXT NOT NULL,
	papers JSONB NOT NULL,
	fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Note: LangGraph's PostgresSaver will create its own tables automatically
-- This file is primarily for any additional database setup you might need

-- Example: Create indexes for performance (if needed after LangGraph creates tables)
-- CREATE INDEX IF NOT EXISTS idx_checkpoint_thread_id ON checkpoints(thread_id);
-- CREATE INDEX IF NOT EXISTS idx_checkpoint_timestamp ON checkpoints(created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE scientific_articles_engine TO postgres;
