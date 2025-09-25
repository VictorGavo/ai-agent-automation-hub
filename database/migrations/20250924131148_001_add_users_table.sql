-- Migration: add_users_table
-- Created: 2025-09-24T13:11:48.553782
-- Agent: TestDatabaseAgent

-- Forward migration
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollback migration (run manually if needed)
/*
DROP TABLE IF EXISTS users;
*/
