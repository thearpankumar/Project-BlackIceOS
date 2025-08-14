# Task 1: Authentication Server Foundation

## What This Task Is About
This task builds the secure foundation for the entire Kali AI-OS by creating a FastAPI authentication server that:
- **Manages user accounts** and secure authentication
- **Stores encrypted API keys** for OpenAI/Anthropic services
- **Provides secure API key delivery** to the Kali AI-OS (never stores keys on disk in VM)
- **Runs on the host system** using Docker Compose for easy management
- **Ensures zero-trust security** where VM never permanently stores sensitive data

## Why This Task Is Critical
- **Security Foundation**: All other tasks depend on secure API key management
- **Legal Compliance**: Proper user authentication and audit trails
- **Scalability**: Can serve multiple Kali AI-OS instances
- **Development Workflow**: Enables team to work with real AI APIs safely

## How to Complete This Task - Step by Step

### Phase 1: Setup Development Environment (30 minutes)
```bash
# 1. Create project structure
mkdir -p auth-server/{app/{auth,database,core,utils},tests,migrations}

# 2. Setup Python virtual environment
cd auth-server
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 3. Install base dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis
pip install cryptography pyjwt bcrypt python-multipart
pip install pytest pytest-asyncio pytest-cov
```

### Phase 2: Write Tests First (45 minutes)
```python
# tests/test_auth.py - Write these tests BEFORE implementing
def test_user_registration():
    """Test user can register successfully"""
    # Write test that expects user registration to work
    
def test_user_login():
    """Test user can login and receive JWT + encrypted keys"""
    # Write test that expects login to return token + keys
    
def test_api_key_encryption():
    """Test API keys are encrypted/decrypted correctly"""
    # Write test that verifies encryption works
    
def test_session_management():
    """Test session creation and validation"""
    # Write test that verifies JWT sessions work
```

### Phase 3: Database Setup (30 minutes)
```sql
-- Create database schema first
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_name VARCHAR(50) NOT NULL,
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 4: Core Implementation (2 hours)
```python
# app/main.py - Start with minimal FastAPI app
from fastapi import FastAPI
app = FastAPI(title="Kali AI-OS Auth Server")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# app/auth/routes.py - Implement auth endpoints
@app.post("/auth/register")
async def register_user(user_data: UserCreate):
    # Hash password with bcrypt
    # Store user in database
    # Return success response

@app.post("/auth/login")  
async def login_user(credentials: UserLogin):
    # Verify password
    # Generate JWT token
    # Retrieve and encrypt user's API keys
    # Return token + encrypted keys
```

### Phase 5: Docker Configuration (45 minutes)
```dockerfile
# Dockerfile - Create container for auth server
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```yaml
# docker-compose.yml - Already created, configure environment
# Set your environment variables in .env file
DB_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_32_chars_minimum  
ENCRYPTION_KEY=your_base64_encryption_key
```

### Phase 6: Testing & Validation (30 minutes)
```bash
# Run all tests
python -m pytest tests/ -v --cov=app

# Start services
docker-compose up -d

# Test API endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"secure123"}'
```

## Overview
Build a secure FastAPI authentication server that runs on the host system using Docker Compose. This server manages user authentication and provides encrypted API keys to the Kali AI-OS.

## Directory Structure
```
Samsung-AI-os/
├── auth-server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── models.py
│   │   │   ├── utils.py
│   │   │   └── dependencies.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   ├── models.py
│   │   │   └── migrations/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── encryption.py
│   │       └── validators.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_database.py
│   │   ├── test_encryption.py
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── docker-compose.yml
└── .env
```

## Technology Stack
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0.23
- **Authentication**: JWT tokens with bcrypt hashing
- **Encryption**: cryptography 41.0.7 for API key storage
- **Container**: Docker with hot reload capability
- **Session Management**: Redis 5.0.1

### 2. Implementation Requirements

#### Core Features
1. **User Registration & Authentication**
   - Secure password hashing with bcrypt
   - JWT token generation and validation
   - Email verification (optional)

2. **API Key Management**
   - Encrypted storage of OpenAI/Anthropic keys
   - Memory-only key delivery to Kali AI-OS
   - Key rotation capability

3. **Session Management**
   - JWT tokens with configurable expiration
   - Session refresh mechanism
   - Automatic cleanup of expired sessions

4. **Security Features**
   - Rate limiting for login attempts
   - CORS configuration for VM access
   - Request logging and audit trails

#### Database Schema
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- API Keys table (encrypted)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_name VARCHAR(50) NOT NULL,
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
```

## Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  auth-server:
    build: 
      context: ./auth-server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://kali_auth:${DB_PASSWORD}@postgres:5432/kali_auth_db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    volumes:
      - ./auth-server/app:/app/app:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - kali-ai-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=kali_auth_db
      - POSTGRES_USER=kali_auth
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./auth-server/database/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kali_auth -d kali_auth_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - kali-ai-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - kali-ai-network

volumes:
  postgres_data:
  redis_data:

networks:
  kali-ai-network:
    driver: bridge
```

### Environment Configuration (.env.example)
```bash
# Database
DB_PASSWORD=your_secure_db_password_here

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Encryption
ENCRYPTION_KEY=your_encryption_key_32_bytes_base64_encoded

# API Keys (Users will input these)
# OPENAI_API_KEY=sk-your-openai-key
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS (for VM access)
ALLOWED_ORIGINS=["http://localhost:3000", "http://192.168.1.0/24"]
```

## Testing Strategy

### Unit Tests (70% coverage minimum)
```bash
# Run unit tests
cd auth-server
python -m pytest tests/ -v --cov=app --cov-report=html

# Expected tests:
# - Authentication flow
# - Password hashing/verification
# - JWT token generation/validation
# - API key encryption/decryption
# - Database operations
# - Session management
```

### Integration Tests
```bash
# Test database connections
python -m pytest tests/test_database.py -v

# Test API endpoints
python -m pytest tests/test_auth.py -v

# Test encryption/decryption
python -m pytest tests/test_encryption.py -v
```

### Security Tests
```python
def test_password_strength_validation():
    """Test password meets security requirements"""
    weak_passwords = ["123", "password", "abc123"]
    for pwd in weak_passwords:
        response = client.post("/auth/register", json={
            "username": "test",
            "password": pwd,
            "email": "test@example.com"
        })
        assert response.status_code == 400

def test_rate_limiting():
    """Test login rate limiting works"""
    for i in range(6):  # Assuming 5 attempts limit
        client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
    
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "correctpassword"
    })
    assert response.status_code == 429  # Too Many Requests

def test_jwt_token_expiration():
    """Test JWT tokens expire correctly"""
    # Test with expired token
    pass
```

## Deployment & Testing

### Setup Commands
```bash
# 1. Clone repository and setup environment
cd Samsung-AI-os
cp .env.example .env
# Edit .env with your secure values

# 2. Generate encryption keys
python -c "
from cryptography.fernet import Fernet
print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())
"

# 3. Start services
docker-compose up -d

# 4. Run tests
cd auth-server
python -m pytest tests/ -v

# 5. Check health
curl http://localhost:8000/health
```

### Validation Criteria
✅ **Must pass before considering task complete:**

1. **Functionality Tests**
   - User registration/login works
   - JWT tokens generated and validated
   - API keys encrypted and retrievable
   - Session management operational

2. **Security Tests**
   - Passwords properly hashed
   - API keys never stored in plaintext
   - Rate limiting prevents brute force
   - CORS properly configured

3. **Performance Tests**
   - Login response < 200ms
   - Database queries < 100ms
   - Handle 100 concurrent users
   - Memory usage < 512MB

4. **Integration Tests**
   - Docker containers start successfully
   - Database migrations run
   - Health checks pass
   - VM can connect to auth server

### Success Metrics
- ✅ All tests pass (90%+ coverage)
- ✅ Security audit complete
- ✅ Performance benchmarks met
- ✅ Docker deployment successful
- ✅ Ready for Kali AI-OS integration

## Next Steps
After completing this task:
1. Document API endpoints for Kali AI-OS integration
2. Set up monitoring and logging
3. Configure backup strategies for database
4. Proceed to Task 2: Voice Recognition Engine

## Troubleshooting
Common issues and solutions:
- **Database connection fails**: Check PostgreSQL container logs
- **JWT tokens invalid**: Verify JWT_SECRET_KEY in environment
- **Encryption errors**: Ensure ENCRYPTION_KEY is base64 encoded
- **Docker build fails**: Check Dockerfile and requirements.txt