-- Initial database schema for Kali AI-OS Auth Server
-- This file is automatically executed by PostgreSQL on first startup
-- Updated to support Groq and Google Generative AI instead of OpenAI/Anthropic

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- API Keys table (encrypted) - supports Groq and Google Generative AI
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(50) NOT NULL,
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_name ON api_keys(key_name);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Insert default admin user (password: 'admin123' - CHANGE IN PRODUCTION)
INSERT INTO users (username, email, password_hash) VALUES
('admin', 'admin@kali-ai-os.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewVyIslc/u9eJkF6')
ON CONFLICT (username) DO NOTHING;

-- Add constraint to ensure valid API key types (Groq and Google Generative AI)
ALTER TABLE api_keys ADD CONSTRAINT chk_valid_key_name
CHECK (key_name IN ('groq', 'google_genai'));

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts for Kali AI-OS authentication';
COMMENT ON TABLE api_keys IS 'Encrypted API keys for Groq and Google Generative AI services';
COMMENT ON TABLE sessions IS 'User session management for JWT tokens';
COMMENT ON COLUMN api_keys.key_name IS 'Type of API key: groq or google_genai';
COMMENT ON COLUMN api_keys.encrypted_key IS 'API key encrypted using Fernet symmetric encryption';
