# Kali AI-OS Authentication Server

Secure authentication and API key management for Kali AI-OS using FastAPI, PostgreSQL, and Redis with support for **Groq** and **Google Generative AI** API keys.

## Features

- User registration and authentication with secure password requirements
- JWT token management with configurable expiration
- Encrypted API key storage for Groq and Google Generative AI
- Session management with automatic cleanup
- Database auto-setup with PostgreSQL migrations
- Docker deployment with health checks
- Rate limiting and security validation
- RESTful API with automatic documentation

## Quick Start

### Prerequisites

- **uv** (Python package manager) - Install from https://docs.astral.sh/uv/
- **Docker & Docker Compose** for containerized deployment
- **Python 3.11+** for local development

### 🐳 Docker Deployment (Recommended)

1. **Setup Environment Variables**
   ```bash
   # From the project root directory (Samsung-AI-os/)
   cp .env.example .env
   
   # Generate secure keys and update .env file
   python3 -c "
   from cryptography.fernet import Fernet
   import secrets
   
   print('# Add these to your .env file:')
   print(f'DB_PASSWORD={secrets.token_urlsafe(32)}')
   print(f'JWT_SECRET_KEY={secrets.token_urlsafe(64)}')
   print(f'ENCRYPTION_KEY={Fernet.generate_key().decode()}')
   print('DEBUG=true')
   "
   ```

2. **Start Services**
   ```bash
   # From Samsung-AI-os/ directory (where docker-compose.yml is located)
   docker-compose up -d
   
   # Check service health
   docker-compose ps
   ```

3. **Verify Deployment**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/health
   
   # View API documentation
   open http://localhost:8000/docs
   
   # Check database status
   curl http://localhost:8000/database/status
   ```

4. **Test User Registration**
   ```bash
   # Register a new user
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser", 
       "email": "test@example.com", 
       "password": "SecurePassword123"
     }'
   
   # Login and get JWT token + encrypted API keys
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser", 
       "password": "SecurePassword123"
     }'
   ```

5. **Add API Keys (Groq & Google GenAI)**
   ```bash
   # Get your JWT token from login response, then:
   
   # Add Groq API key
   curl -X POST http://localhost:8000/auth/api-keys \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "key_name": "groq",
       "api_key": "gsk_your_actual_groq_api_key_here"
     }'
   
   # Add Google Generative AI key
   curl -X POST http://localhost:8000/auth/api-keys \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "key_name": "google_genai",
       "api_key": "AIzaSy_your_actual_google_genai_key_here"
     }'
   ```

### 💻 Local Development

1. **Install uv Package Manager**
   ```bash
   # Install uv (ultra-fast Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Add to PATH (restart shell or run):
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Setup Development Environment**
   ```bash
   # Navigate to auth-server directory
   cd auth-server/
   
   # Install dependencies (10-100x faster than pip!)
   uv sync
   
   # Install test dependencies
   uv sync --group test
   ```

3. **Set Environment Variables**
   ```bash
   # Set required environment variables for local development
   export ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
   export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
   export DEBUG="true"
   export DATABASE_URL="sqlite:///./test.db"  # Use SQLite for local dev
   ```

4. **Run Tests**
   ```bash
   # Run all tests with coverage
   uv run pytest tests/ -v --cov=app
   
   # Run specific test files
   uv run pytest tests/test_auth.py -v
   uv run pytest tests/test_encryption.py -v
   uv run pytest tests/test_database.py -v
   
   # Generate HTML coverage report
   uv run pytest tests/ --cov=app --cov-report=html
   
   # Run tests with different verbosity levels
   uv run pytest tests/ -v           # Verbose output
   uv run pytest tests/ -vv          # Very verbose output
   uv run pytest tests/ -s           # Show print statements
   uv run pytest tests/ -x           # Stop on first failure
   uv run pytest tests/ --tb=short   # Short traceback format
   
   # Run tests matching specific patterns
   uv run pytest tests/ -k "test_user_registration"     # Run tests with this name pattern
   uv run pytest tests/ -k "not slow"                   # Skip tests marked as slow
   uv run pytest tests/ -m "unit"                       # Run tests marked with @pytest.mark.unit
   
   # Parallel test execution (install pytest-xdist first)
   uv add --group test pytest-xdist
   uv run pytest tests/ -n auto      # Run tests in parallel using all CPUs
   uv run pytest tests/ -n 4         # Run tests using 4 processes
   
   # Generate different coverage report formats
   uv run pytest tests/ --cov=app --cov-report=term-missing  # Show missing lines in terminal
   uv run pytest tests/ --cov=app --cov-report=xml           # Generate coverage.xml
   uv run pytest tests/ --cov=app --cov-report=json          # Generate coverage.json
   
   # Run tests with specific markers
   uv run pytest tests/ -m "not integration"  # Skip integration tests
   uv run pytest tests/ -m "unit or security" # Run unit and security tests only
   ```

5. **Start Development Server**
   ```bash
   # Start FastAPI server with hot reload
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Server will be available at:
   # - API: http://localhost:8000
   # - Docs: http://localhost:8000/docs
   # - ReDoc: http://localhost:8000/redoc
   ```

6. **Test Local Development**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/health
   
   # Test user registration
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"devuser","email":"dev@test.com","password":"DevPassword123"}'
   ```

## API Endpoints

### Public Endpoints
- `GET /` - API information and supported providers
- `GET /health` - Health check with database connectivity
- `GET /database/status` - Database connection details
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication (returns JWT + encrypted API keys)

### Authenticated Endpoints (Require JWT Token)
- `GET /auth/me` - Current user profile
- `PUT /auth/me` - Update user profile
- `POST /auth/change-password` - Change user password
- `POST /auth/api-keys` - Add/update API keys (Groq or Google GenAI)
- `GET /auth/api-keys` - List user's configured API keys
- `DELETE /auth/api-keys/{key_name}` - Remove API key
- `GET /auth/sessions` - List active user sessions
- `DELETE /auth/sessions/{session_id}` - Revoke specific session
- `GET /auth/stats` - User statistics and key configuration status

## Supported API Providers

### Groq
- **Key Format**: `gsk_*` (validated on input)
- **Usage**: High-performance AI inference
- **Key Name**: `groq`

### Google Generative AI
- **Key Format**: `AIza*` (validated on input)  
- **Usage**: Google's Gemini and PaLM models
- **Key Name**: `google_genai`

## Security Features

### Password Requirements
- Minimum 8 characters
- Must contain uppercase and lowercase letters
- Must contain at least one digit
- Must contain at least one special character
- Blocks common weak passwords

### API Key Security
- All API keys encrypted using **Fernet** symmetric encryption
- Keys never stored in plaintext in database
- Memory-only delivery to client applications
- Format validation for each provider

### Authentication Security
- **JWT tokens** with configurable expiration (24h default)
- **bcrypt** password hashing with salt
- **Rate limiting** for login attempts (5 attempts/minute)
- **Session management** with automatic cleanup
- **CORS** configuration for VM access

## Configuration

### Environment Variables

```bash
# Database Configuration
DB_PASSWORD=your_secure_db_password_32_chars_minimum
DATABASE_URL=postgresql://kali_auth:${DB_PASSWORD}@postgres:5432/kali_auth_db

# JWT Configuration  
JWT_SECRET_KEY=your_jwt_secret_key_64_chars_minimum
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Encryption Configuration
ENCRYPTION_KEY=your_base64_fernet_encryption_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Security Configuration
LOGIN_RATE_LIMIT=5
MIN_PASSWORD_LENGTH=8
REQUIRE_UPPERCASE=true
REQUIRE_LOWERCASE=true
REQUIRE_DIGITS=true
REQUIRE_SPECIAL_CHARS=true

# CORS (adjust for your network)
ALLOWED_ORIGINS=["http://localhost:3000","http://192.168.1.0/24"]
```

## Database Schema

### Tables
- **users**: User accounts with secure authentication
- **api_keys**: Encrypted API keys for supported providers
- **sessions**: JWT session tracking and management

### Automatic Setup
- Database tables created automatically on first startup
- Migration files executed by PostgreSQL init scripts
- Indexes created for optimal query performance
- Foreign key constraints ensure data integrity

## Troubleshooting

### Common Issues

**1. Container won't start - Environment variables missing**
```bash
# Check if .env file exists in project root
ls -la /path/to/Samsung-AI-os/.env

# Verify environment variables are set
docker-compose config
```

**2. Database connection failed**
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Test database connection manually
docker exec -it $(docker ps -q -f name=postgres) \
  psql -U kali_auth -d kali_auth_db -c "SELECT version();"
```

**3. Health check failing**
```bash
# Check application logs
docker-compose logs auth-server

# Test database connectivity
curl http://localhost:8000/database/status
```

**4. JWT token validation errors**
```bash
# Verify JWT secret key length (minimum 32 characters)
echo $JWT_SECRET_KEY | wc -c

# Check token expiration in response
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}' | jq '.expires_in'
```

**5. API key encryption errors**
```bash
# Verify encryption key format (Fernet base64)
python3 -c "
from cryptography.fernet import Fernet
try:
    Fernet('$ENCRYPTION_KEY'.encode())
    print('✅ Encryption key valid')
except:
    print('❌ Invalid encryption key format')
"
```

### Performance Monitoring

```bash
# Check service status
docker-compose ps

# Monitor resource usage
docker stats

# View application metrics
curl http://localhost:8000/system/info

# Check database performance
docker exec -it $(docker ps -q -f name=postgres) \
  psql -U kali_auth -d kali_auth_db -c "\dt+"
```

## Testing Guide

### 🧪 Comprehensive Testing with pytest

The project uses **Test-Driven Development (TDD)** approach with comprehensive test coverage.

#### Test Structure
```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py             # Authentication endpoint tests
├── test_database.py         # Database model and connection tests
└── test_encryption.py       # API key encryption/decryption tests
```

#### Basic Testing Commands
```bash
# Run all tests (basic)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with very verbose output (shows each test function)
uv run pytest -vv

# Show print statements and logging output
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Show short traceback format
uv run pytest --tb=short
```

#### Advanced Testing Options

**1. Running Specific Tests**
```bash
# Run specific test file
uv run pytest tests/test_auth.py -v

# Run specific test class
uv run pytest tests/test_auth.py::TestUserRegistration -v

# Run specific test function
uv run pytest tests/test_auth.py::TestUserRegistration::test_user_registration_success -v

# Run tests matching pattern
uv run pytest -k "registration" -v                    # All tests with "registration" in name
uv run pytest -k "test_user_registration or test_login" -v  # Multiple patterns
uv run pytest -k "not slow" -v                        # Exclude tests marked as slow
```

**2. Test Markers and Categories**
```bash
# Run tests by markers (if implemented)
uv run pytest -m "unit" -v                # Unit tests only
uv run pytest -m "integration" -v         # Integration tests only
uv run pytest -m "security" -v            # Security-related tests
uv run pytest -m "not slow" -v            # Skip slow tests
```

**3. Coverage Reporting**
```bash
# Basic coverage
uv run pytest --cov=app

# Coverage with missing lines shown
uv run pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser to view

# Generate XML coverage (for CI/CD)
uv run pytest --cov=app --cov-report=xml

# Generate JSON coverage
uv run pytest --cov=app --cov-report=json

# Set minimum coverage threshold (fail if below 80%)
uv run pytest --cov=app --cov-fail-under=80
```

**4. Parallel Test Execution**
```bash
# Install parallel testing plugin
uv add --group test pytest-xdist

# Run tests in parallel (auto-detect CPUs)
uv run pytest -n auto

# Run tests with specific number of processes
uv run pytest -n 4

# Parallel with coverage (requires pytest-cov)
uv run pytest -n auto --cov=app --cov-report=html
```

**5. Output and Formatting Options**
```bash
# Quiet output (minimal)
uv run pytest -q

# Show test durations (slowest tests first)
uv run pytest --durations=10

# Show all test durations
uv run pytest --durations=0

# Custom output format
uv run pytest --tb=line     # One line per failure
uv run pytest --tb=long     # Long traceback format
uv run pytest --tb=no       # No traceback
```

#### Docker Environment Testing
```bash
# Test with Docker containers running
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run integration tests that need database
uv run pytest tests/test_database.py -v

# Run all tests with Docker environment
uv run pytest tests/ -v --cov=app

# Cleanup
docker-compose down
```

#### Test Environment Variables
```bash
# Set test environment variables
export ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
export DEBUG="true"
export DATABASE_URL="sqlite:///./test.db"

# Run tests with environment
uv run pytest tests/ -v
```

#### Continuous Testing (Watch Mode)
```bash
# Install pytest-watch for automatic test running
uv add --group test pytest-watch

# Watch for file changes and re-run tests
uv run ptw tests/ -- -v

# Watch specific test file
uv run ptw tests/test_auth.py -- -v
```

#### Test Data and Fixtures
The tests use **fixtures** defined in `conftest.py`:

- `db_session` - Clean database session for each test
- `client` - FastAPI test client with database override
- `sample_user_data` - Test user registration data
- `sample_api_keys` - Test API keys for Groq and Google GenAI

#### Common Test Scenarios

**1. Authentication Flow Testing**
```bash
# Test user registration and login
uv run pytest tests/test_auth.py::TestUserRegistration -v
uv run pytest tests/test_auth.py::TestUserLogin -v

# Test JWT token validation
uv run pytest tests/test_auth.py::TestJWTTokens -v
```

**2. API Key Encryption Testing**
```bash
# Test encryption/decryption of API keys
uv run pytest tests/test_encryption.py -v

# Test specific encryption functions
uv run pytest tests/test_encryption.py::TestEncryptionFunctions::test_encrypt_groq_api_key -v
```

**3. Database Operations Testing**
```bash
# Test database models and relationships
uv run pytest tests/test_database.py::TestDatabaseModels -v

# Test CRUD operations
uv run pytest tests/test_database.py::TestDatabaseOperations -v
```

#### Test Output Examples

**Successful Test Run:**
```bash
$ uv run pytest tests/test_auth.py::TestUserRegistration::test_user_registration_success -v

======================== test session starts ========================
collected 1 item

tests/test_auth.py::TestUserRegistration::test_user_registration_success PASSED [100%]

======================== 1 passed in 0.45s ========================
```

**Coverage Report:**
```bash
$ uv run pytest --cov=app --cov-report=term-missing

======================== test session starts ========================
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/__init__.py                       0      0   100%
app/auth/__init__.py                  0      0   100%
app/auth/dependencies.py             85     12    86%   45-48, 67-70
app/auth/models.py                   76      5    93%   23, 89-92
app/auth/routes.py                  156     23    85%   67-71, 123-127
app/core/__init__.py                  0      0   100%
app/core/config.py                   87     12    86%   45-49, 78-82
app/core/security.py                145     18    88%   89-95, 156-162
app/database/__init__.py              0      0   100%
app/database/connection.py           98     15    85%   67-72, 145-151
app/database/models.py               45      3    93%   78-80
app/main.py                         123     25    80%   89-95, 167-175
app/utils/__init__.py                 0      0   100%
app/utils/encryption.py             134     12    91%   89-95, 167-170
---------------------------------------------------------------
TOTAL                               949    125    87%

======================== 15 passed in 12.34s ========================
```

#### Debugging Failed Tests
```bash
# Run with pdb debugger on failure
uv run pytest --pdb

# Drop to pdb on first failure
uv run pytest -x --pdb

# Show local variables in traceback
uv run pytest -l

# Capture output (disable -s temporarily)
uv run pytest --capture=no
```

## Development Workflow

### Making Changes
```bash
# 1. Make code changes
# 2. Run tests to ensure functionality
uv run pytest tests/ -v

# 3. Run specific tests for changed functionality
uv run pytest tests/test_auth.py -k "registration" -v

# 4. Check test coverage
uv run pytest --cov=app --cov-report=term-missing

# 5. Restart services to pick up changes
docker-compose restart auth-server

# 6. Test endpoints
curl http://localhost:8000/health
```

### Adding New Features (TDD Approach)
1. **Write tests first** (Red phase)
   ```bash
   # Write failing test for new feature
   uv run pytest tests/test_new_feature.py -v  # Should fail
   ```

2. **Implement minimal functionality** (Green phase)
   ```bash
   # Implement just enough to make tests pass
   uv run pytest tests/test_new_feature.py -v  # Should pass
   ```

3. **Refactor and improve** (Refactor phase)
   ```bash
   # Improve code while keeping tests passing
   uv run pytest tests/ -v  # All tests should pass
   ```

4. **Verify integration**
   ```bash
   # Test with full test suite
   uv run pytest tests/ --cov=app -v
   
   # Test with Docker environment
   docker-compose restart auth-server
   curl http://localhost:8000/health
   ```

### Test-First Development Example
```bash
# 1. Create failing test for new endpoint
echo "def test_new_endpoint(): assert False" >> tests/test_new_feature.py
uv run pytest tests/test_new_feature.py -v  # Fails ❌

# 2. Implement minimal endpoint
# ... add code to make test pass ...
uv run pytest tests/test_new_feature.py -v  # Passes ✅

# 3. Add more comprehensive tests
# ... write additional test cases ...
uv run pytest tests/test_new_feature.py -v  # All pass ✅

# 4. Refactor and optimize
# ... improve implementation ...
uv run pytest tests/ --cov=app -v  # Verify no regressions
```

## Production Deployment

### Security Checklist
- [ ] Change default passwords and keys
- [ ] Set `DEBUG=false` in production
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Regular security updates
- [ ] Backup database regularly

### Performance Optimization
- [ ] Configure database connection pooling
- [ ] Set up Redis for session storage
- [ ] Enable request/response compression
- [ ] Configure reverse proxy (nginx)
- [ ] Set up horizontal scaling if needed

---

## Support

For issues and questions:
- Check the troubleshooting section above
- Review container logs: `docker-compose logs auth-server`
- Test with curl commands provided in this README
- Verify environment variables are properly set

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Next**: Ready for Task 2 (Voice Recognition Engine) integration