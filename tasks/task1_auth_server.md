# Task 1: Authentication Server Foundation

## What This Task Is About
This task builds the secure foundation for the entire Kali AI-OS by creating a FastAPI authentication server that:
- **Manages user accounts** and secure authentication
- **Stores encrypted API keys** for Google GenAI/Groq services
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

### Phase 3: Automatic Database Setup (45 minutes)
```bash
# 1. Create database migration files (PostgreSQL auto-runs these)
mkdir -p auth-server/database/migrations

# 2. Create initial schema migration
cat > auth-server/database/migrations/001_initial_schema.sql << 'EOF'
-- Initial database schema for Kali AI-OS Auth Server
-- This file is automatically executed by PostgreSQL on first startup

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

-- API Keys table (encrypted)
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
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Insert default admin user (password: 'admin123' - CHANGE IN PRODUCTION)
INSERT INTO users (username, email, password_hash) VALUES 
('admin', 'admin@kali-ai-os.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewVyIslc/u9eJkF6')
ON CONFLICT (username) DO NOTHING;
EOF

# 3. Create SQLAlchemy models for application use
cat > auth-server/app/database/models.py << 'EOF'
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

class APIKey(Base):
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key_name = Column(String(50), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime)
    
    # Relationship
    user = relationship("User", back_populates="api_keys")

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    ip_address = Column(String(45))  # For both IPv4 and IPv6
    user_agent = Column(Text)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
EOF

# 4. Create database connection module
cat > auth-server/app/database/connection.py << 'EOF'
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kali_auth:password@localhost:5432/kali_auth_db")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database dependency for FastAPI
def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database tables (fallback if migrations didn't run)
def create_tables():
    """Create all tables if they don't exist (fallback method)"""
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to create database tables: {e}")
        return False

# Health check function
def check_database_health():
    """Check if database connection is healthy"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return False
EOF

# 5. Update main FastAPI app to include database initialization
echo "Database auto-setup complete! Tables will be created automatically."
```

### Phase 4: Core Implementation with Database Integration (2.5 hours)
```python
# app/main.py - FastAPI app with database integration
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import database components
from app.database.connection import create_tables, check_database_health
from app.database.models import Base
from app.auth import routes as auth_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting Kali AI-OS Authentication Server...")
    
    # Initialize database (fallback if migrations didn't run)
    if not create_tables():
        logger.warning("Database table creation failed, but continuing...")
    
    # Check database health
    if not check_database_health():
        logger.error("Database health check failed!")
        raise Exception("Cannot start server - database unavailable")
    
    logger.info("Authentication server started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down authentication server...")

# Create FastAPI app
app = FastAPI(
    title="Kali AI-OS Authentication Server",
    description="Secure authentication and API key management for Kali AI-OS",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for VM access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint with database status
@app.get("/health")
async def health_check():
    """Comprehensive health check including database"""
    db_healthy = check_database_health()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "version": "1.0.0",
        "service": "kali-ai-os-auth"
    }

# Include authentication routes
app.include_router(auth_routes.router, prefix="/auth", tags=["authentication"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Kali AI-OS Authentication Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "register": "/auth/register", 
            "login": "/auth/login",
            "refresh": "/auth/refresh"
        }
    }

# Database status endpoint
@app.get("/database/status")
async def database_status():
    """Check database connection status"""
    healthy = check_database_health()
    return {
        "database_connected": healthy,
        "status": "ok" if healthy else "error"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```python
# app/auth/routes.py - Authentication endpoints with database integration
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt
import jwt
from typing import Dict, Any

from app.database.connection import get_database
from app.database.models import User, APIKey, Session as UserSession
from app.auth.models import UserCreate, UserLogin, UserResponse, TokenResponse
from app.core.security import create_access_token, verify_token
from app.utils.encryption import encrypt_api_key, decrypt_api_key

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_database)):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Hash password
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: UserLogin, db: Session = Depends(get_database)):
    """Login user and return JWT token with encrypted API keys"""
    
    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    
    # Get user's API keys (encrypted)
    api_keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    encrypted_keys = {}
    
    for key in api_keys:
        try:
            # Keys are already encrypted in database, just return them
            encrypted_keys[key.key_name] = key.encrypted_key
        except Exception as e:
            logger.warning(f"Failed to process API key {key.key_name}: {e}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        encrypted_api_keys=encrypted_keys
    )
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

# Test API endpoints and database
curl http://localhost:8000/health
curl http://localhost:8000/database/status

# Test user registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"SecurePass123!"}'

# Test user login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"SecurePass123!"}'

# Verify database tables were created
docker exec -it $(docker ps -q -f name=postgres) psql -U kali_auth -d kali_auth_db -c "\dt"

# Check that migration ran
docker logs $(docker ps -q -f name=postgres) | grep "database system is ready"
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
   - Encrypted storage of Google GenAI/Groq keys
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
# GOOGLE_API_KEY=your-google-api-key
# GROQ_API_KEY=your-groq-api-key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS (for VM access)
ALLOWED_ORIGINS=["http://localhost:3000", "http://192.168.1.0/24"]
```

### Phase 7: Database Integration Verification (30 minutes)
```bash
# 1. Verify automatic database setup
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to initialize..."
sleep 10

# 2. Check if tables were created automatically
docker exec -it $(docker ps -q -f name=postgres) psql -U kali_auth -d kali_auth_db -c "
-- List all tables
\dt
-- Check users table structure
\d users
-- Check if admin user was created
SELECT username, email, created_at FROM users;
"

# 3. Test database connection from application
cat > test_db_connection.py << 'EOF'
import os
from sqlalchemy import create_engine, text

# Test database connection
DATABASE_URL = "postgresql://kali_auth:your_password@localhost:5432/kali_auth_db"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        print(f"✅ Database connected! Found {user_count} users.")
        
        # Test tables exist
        tables = connection.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        
        table_names = [row[0] for row in tables.fetchall()]
        expected_tables = ['users', 'api_keys', 'sessions']
        
        for table in expected_tables:
            if table in table_names:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF

python test_db_connection.py
rm test_db_connection.py

echo "✅ Database integration verified!"
```

## Testing Strategy

### Unit Tests (80% coverage minimum)
```bash
# Run unit tests with database
cd auth-server
python -m pytest tests/ -v --cov=app --cov-report=html

# Expected tests:
# - Database connection and health checks
# - Automatic table creation (migration)
# - User registration with database storage
# - Authentication flow with database queries
# - Password hashing/verification
# - JWT token generation/validation
# - API key encryption/decryption
# - Session management in database
# - Database transaction handling
# - Error handling for database failures
```

```python
# tests/test_database.py - Database-specific tests
import pytest
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, create_tables, check_database_health
from app.database.models import User, APIKey, Session as UserSession

@pytest.fixture
def db_session():
    """Create database session for testing"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_database_connection():
    """Test database connection is working"""
    assert check_database_health() == True

def test_tables_exist(db_session: Session):
    """Test all required tables exist"""
    # Check users table
    result = db_session.execute("SELECT COUNT(*) FROM users")
    assert result.fetchone()[0] >= 0
    
    # Check api_keys table
    result = db_session.execute("SELECT COUNT(*) FROM api_keys")
    assert result.fetchone()[0] >= 0
    
    # Check sessions table
    result = db_session.execute("SELECT COUNT(*) FROM sessions")
    assert result.fetchone()[0] >= 0

def test_user_crud_operations(db_session: Session):
    """Test user creation, reading, updating, deletion"""
    # Create user
    test_user = User(
        username="test_crud",
        email="crud@test.com",
        password_hash="hashed_password"
    )
    
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    
    # Read user
    retrieved_user = db_session.query(User).filter(User.username == "test_crud").first()
    assert retrieved_user is not None
    assert retrieved_user.email == "crud@test.com"
    
    # Update user
    retrieved_user.email = "updated@test.com"
    db_session.commit()
    
    updated_user = db_session.query(User).filter(User.username == "test_crud").first()
    assert updated_user.email == "updated@test.com"
    
    # Delete user
    db_session.delete(updated_user)
    db_session.commit()
    
    deleted_user = db_session.query(User).filter(User.username == "test_crud").first()
    assert deleted_user is None

def test_foreign_key_relationships(db_session: Session):
    """Test foreign key relationships work correctly"""
    # Create user
    user = User(username="fk_test", email="fk@test.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create API key for user
    api_key = APIKey(
        user_id=user.id,
        key_name="googlegenai",
        encrypted_key="encrypted_key_data"
    )
    
    db_session.add(api_key)
    db_session.commit()
    
    # Test relationship
    retrieved_user = db_session.query(User).filter(User.id == user.id).first()
    assert len(retrieved_user.api_keys) == 1
    assert retrieved_user.api_keys[0].key_name == "googlegenai"
    
    # Cleanup
    db_session.delete(user)  # Should cascade delete api_key
    db_session.commit()
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

# 2. Generate encryption keys and secure passwords
python -c "
import secrets
import base64
from cryptography.fernet import Fernet

# Generate database password
db_password = secrets.token_urlsafe(32)
print(f'DB_PASSWORD={db_password}')

# Generate JWT secret
jwt_secret = secrets.token_urlsafe(64)
print(f'JWT_SECRET_KEY={jwt_secret}')

# Generate encryption key
encryption_key = Fernet.generate_key().decode()
print(f'ENCRYPTION_KEY={encryption_key}')

print('\n✅ Add these to your .env file')
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

1. **Database Tests**
   - PostgreSQL container starts successfully
   - Migration files execute automatically
   - All tables created with proper schema
   - Database connection from FastAPI works
   - Foreign key relationships function correctly

2. **Functionality Tests**
   - User registration/login works with database
   - JWT tokens generated and validated
   - API keys encrypted and stored in database
   - Session management operational with database
   - Database transactions handle errors properly

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
   - Docker containers start successfully in correct order
   - PostgreSQL migration files execute on first startup
   - Health checks pass including database connectivity
   - FastAPI app connects to PostgreSQL successfully
   - VM can connect to auth server
   - Database persists data between container restarts

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

## Troubleshooting Database Issues

### Common Database Problems and Solutions:

**1. Tables not created automatically:**
```bash
# Check if migration files exist
ls -la auth-server/database/migrations/

# Check PostgreSQL container logs
docker logs $(docker ps -q -f name=postgres)

# Manually run migration if needed
docker exec -i $(docker ps -q -f name=postgres) psql -U kali_auth -d kali_auth_db < auth-server/database/migrations/001_initial_schema.sql
```

**2. Database connection fails:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection manually
docker exec -it $(docker ps -q -f name=postgres) psql -U kali_auth -d kali_auth_db -c "SELECT version();"

# Check environment variables
echo $DB_PASSWORD
```

**3. Migration files not executing:**
```bash
# Ensure migration files have correct permissions
chmod 644 auth-server/database/migrations/*.sql

# Check Docker volume mapping
docker inspect $(docker ps -q -f name=postgres) | grep -A 10 "Mounts"
```

**4. Application can't connect to database:**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test SQLAlchemy connection
python -c "from app.database.connection import check_database_health; print(check_database_health())"
```

**5. Database data lost between restarts:**
```bash
# Check if volume is properly configured
docker volume ls | grep postgres

# Backup database before restart
docker exec $(docker ps -q -f name=postgres) pg_dump -U kali_auth kali_auth_db > backup.sql
```

### Other Common Issues:
- **JWT tokens invalid**: Verify JWT_SECRET_KEY in environment
- **Encryption errors**: Ensure ENCRYPTION_KEY is base64 encoded
- **Docker build fails**: Check Dockerfile and requirements.txt
- **CORS errors**: Update ALLOWED_ORIGINS in environment variables