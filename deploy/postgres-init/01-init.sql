# PostgreSQL initialization script for Docker
# This script sets up the initial database schema and users

set -e

# Create additional databases if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
    
    -- Create additional schemas
    CREATE SCHEMA IF NOT EXISTS automation_hub;
    CREATE SCHEMA IF NOT EXISTS logs;
    CREATE SCHEMA IF NOT EXISTS monitoring;
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON SCHEMA automation_hub TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON SCHEMA logs TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON SCHEMA monitoring TO $POSTGRES_USER;
    
    -- Create basic tables for logging
    CREATE TABLE IF NOT EXISTS logs.agent_activity (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        agent_name VARCHAR(100) NOT NULL,
        activity_type VARCHAR(50) NOT NULL,
        description TEXT,
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS logs.task_history (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        task_id VARCHAR(255) NOT NULL,
        agent_name VARCHAR(100) NOT NULL,
        status VARCHAR(50) NOT NULL,
        task_description TEXT,
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_agent_activity_agent_name ON logs.agent_activity(agent_name);
    CREATE INDEX IF NOT EXISTS idx_agent_activity_created_at ON logs.agent_activity(created_at);
    CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON logs.task_history(task_id);
    CREATE INDEX IF NOT EXISTS idx_task_history_agent_name ON logs.task_history(agent_name);
    CREATE INDEX IF NOT EXISTS idx_task_history_created_at ON logs.task_history(created_at);
    
    -- Insert initial data
    INSERT INTO logs.agent_activity (agent_name, activity_type, description) 
    VALUES ('system', 'initialization', 'Database initialized successfully')
    ON CONFLICT DO NOTHING;
    
EOSQL

echo "✅ PostgreSQL initialization completed"