# Development Workflow Guide

Welcome to the Kali AI-OS development team! This guide will help you get up and running quickly and follow our established development practices.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (recommended: 3.11 or 3.12)
- **uv** (ultra-fast Python package manager)
- **Docker & Docker Compose**
- **Git** with SSH keys configured

### First-Time Setup

```bash
# 1. Clone the repository
git clone git@github.com:your-org/Samsung-AI-os.git
cd Samsung-AI-os

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 3. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 4. Set up auth server development environment
cd auth-server
uv sync --all-extras

# 5. Set up environment variables
cp ../.env.example ../.env
# Edit .env with your local configuration

# 6. Test the setup
uv run pytest tests/ -v
```

## 🏗️ Project Structure

```
Samsung-AI-os/
├── 🔐 auth-server/          # Authentication server (FastAPI + PostgreSQL)
│   ├── app/                 # Main application code
│   ├── tests/              # Test suite
│   ├── migrations/         # Database migrations
│   └── pyproject.toml      # Project configuration
├── 📋 tasks/               # Task documentation (project requirements)
├── 🐳 docker compose.yml   # Development environment
├── 🔧 .github/             # CI/CD workflows and templates
└── 📖 docs/                # Documentation (if applicable)
```

## 💼 Development Environment

### Using uv (Recommended)

**uv** is our package manager - it's 10-100x faster than pip!

```bash
cd auth-server

# Install dependencies
uv sync                          # Install all dependencies
uv sync --all-extras            # Include dev and test dependencies
uv add package-name              # Add new dependency
uv add --group dev tool-name     # Add development tool

# Run commands
uv run python app/main.py        # Run the app
uv run pytest tests/             # Run tests
uv run ruff check .              # Run linter
uv run pre-commit run --all-files --config ../.pre-commit-config.yaml
```

### Docker Development

```bash
# Start all services (PostgreSQL, Redis, Auth Server, Prometheus, Grafana)
docker compose up -d

# View logs
docker compose logs -f auth-server
docker compose logs -f postgres
docker compose logs -f prometheus
docker compose logs -f grafana

# Stop services
docker compose down

# Rebuild and start
docker compose up --build -d
```

## 📊 Monitoring

The development environment includes Prometheus and Grafana for monitoring the application.

- **Prometheus**: Collects metrics from the `auth-server`.
  - **URL**: http://localhost:9090
  - **Metrics Endpoint**: http://localhost:8000/metrics

- **Grafana**: Visualizes the metrics collected by Prometheus.
  - **URL**: http://localhost:3000
  - **Login**: `admin` / `admin` (you will be prompted to change the password on first login)

A pre-configured dashboard for the `auth-server` is not yet available. You can create your own dashboards in Grafana to monitor key metrics.


## 🔄 Development Workflow

### 1. **Branch Strategy**

We use **GitFlow** with semantic branch names:

```bash
# Feature development
git checkout -b feat/user-registration-endpoint
git checkout -b feat/add-oauth-integration

# Bug fixes  
git checkout -b fix/jwt-token-expiration
git checkout -b fix/database-connection-timeout

# Documentation
git checkout -b docs/update-api-documentation

# Refactoring
git checkout -b refactor/optimize-database-queries

# Tests
git checkout -b test/add-integration-tests
```

### 2. **Daily Development Cycle**

```bash
# Start your day
git checkout master
git pull origin master
git checkout -b feat/your-new-feature

# Make changes to code
# ... edit files ...

# Test your changes locally
cd auth-server
uv run pytest tests/ -v                    # Run tests
uv run ruff check . --fix                  # Fix linting issues
uv run ruff format .                       # Format code
docker compose up -d && sleep 10           # Start services
curl http://localhost:8000/health          # Test health endpoint

# Commit your changes (triggers pre-commit hooks)
git add .
git commit -m "feat: add user profile endpoint with validation"

# Push and create PR
git push origin feat/your-new-feature
# Create PR through GitHub UI
```

### 3. **Testing Requirements**

Before pushing any code:

#### **Local Testing Checklist**
```bash
cd auth-server

# ✅ Code Quality
uv run ruff check .                 # Linting
uv run ruff format --check .        # Formatting
uv run black --check .              # Black formatting
uv run isort --check .              # Import sorting
uv run mypy app/                    # Type checking

# ✅ Security
uv run bandit -r app/               # Security linting
uv run safety check                 # Dependency vulnerabilities

# ✅ Tests
uv run pytest tests/ -v --cov=app  # Unit tests with coverage
uv run pytest tests/ --cov-fail-under=80  # Ensure 80%+ coverage

# ✅ Integration
docker compose up -d
sleep 10
curl http://localhost:8000/health  # Health check
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"TestPass123!"}'
docker compose down
```

## 📝 Code Standards

### **Python Code Style**

- **Line Length**: 88 characters (Black standard)
- **Import Sorting**: isort with Black profile
- **Type Hints**: Encouraged but not required
- **Docstrings**: Use for all public functions and classes

```python
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class UserResponse(BaseModel):
    """User registration response model."""
    id: int
    username: str
    email: str
    is_active: bool

async def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """
    Create a new user with validation.
    
    Args:
        user_data: User creation data
        
    Returns:
        Dictionary containing user information and success status
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    # Implementation here
    pass
```

### **Commit Message Format**

Use **Conventional Commits** format:

```bash
# Format: <type>(<scope>): <description>
feat(auth): add user registration endpoint
fix(database): resolve connection timeout issue
docs(readme): update installation instructions
test(auth): add integration tests for login flow
refactor(security): optimize JWT token validation
perf(database): add indexes for faster queries
chore(deps): update dependencies to latest versions
ci(github): add automated security scanning
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

## 🧪 Testing Guidelines

### **Test Structure**
```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_user_registration_success(self, client):
        """Test successful user registration."""
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com", 
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
        assert "id" in response.json()
    
    def test_user_registration_duplicate_email(self, client):
        """Test registration fails with duplicate email."""
        # First registration
        client.post("/auth/register", json={
            "username": "user1",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        
        # Second registration with same email should fail
        response = client.post("/auth/register", json={
            "username": "user2", 
            "email": "test@example.com",
            "password": "AnotherPass123!"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
```

### **Test Categories**

- **Unit Tests** (`@pytest.mark.unit`): Fast tests for individual functions
- **Integration Tests** (`@pytest.mark.integration`): Tests with database/external services  
- **Security Tests** (`@pytest.mark.security`): Tests for authentication and authorization
- **Slow Tests** (`@pytest.mark.slow`): Long-running tests (skip during development)

```bash
# Run specific test categories
uv run pytest -m unit                    # Unit tests only
uv run pytest -m "not slow"             # Skip slow tests  
uv run pytest -k "registration"         # Tests matching pattern
uv run pytest tests/test_auth.py -v     # Specific file
```

## 🔒 Security Guidelines

### **Never Commit Secrets**

```bash
# ❌ DON'T DO THIS
API_KEY = "gsk_abc123def456"
JWT_SECRET = "mysecretkey"

# ✅ DO THIS
API_KEY = os.getenv("GROQ_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
```

### **Environment Variables**

Always use environment variables for configuration:

```python
# app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### **Input Validation**

Always validate and sanitize inputs:

```python
from pydantic import BaseModel, EmailStr, Field
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r"[0-9]", v):
            raise ValueError('Password must contain digit')
        return v
```

## 🐛 Debugging

### **Local Debugging**

```bash
# Enable debug mode
export DEBUG=true

# Run with verbose logging
uv run uvicorn app.main:app --reload --log-level debug

# Use debugger in code
import pdb; pdb.set_trace()  # Python debugger

# Database debugging
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
docker compose logs postgres
```

### **Docker Debugging**

```bash
# View container logs
docker compose logs -f auth-server
docker compose logs -f postgres

# Execute commands in container
docker compose exec auth-server bash
docker compose exec postgres psql -U kali_auth -d kali_auth_db

# Debug network issues
docker compose ps
docker network ls
```

## 🚨 Common Issues & Solutions

### **Issue: uv sync fails**
```bash
# Solution: Clear cache and retry
uv cache clean
uv sync --all-extras
```

### **Issue: Tests fail with database connection**
```bash
# Solution: Start services first
docker compose up -d postgres redis
sleep 5
uv run pytest tests/
```

### **Issue: Pre-commit hooks fail**
```bash
# Solution: Fix issues and retry
uv run ruff check . --fix    # Fix linting issues
uv run ruff format .         # Format code
git add .
git commit -m "fix: resolve linting issues"
```

### **Issue: Docker build fails**
```bash
# Solution: Clean Docker cache
docker system prune -f
docker compose build --no-cache
```

## 🔧 IDE Configuration

### **VS Code Setup**
Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreter": "./auth-server/.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### **PyCharm Setup**
1. Open project in PyCharm
2. Set interpreter to `auth-server/.venv/bin/python`
3. Enable Black formatter in Settings > Tools > External Tools
4. Configure Ruff as external linter

## 📊 Performance Guidelines

### **Database Queries**
```python
# ❌ N+1 queries
users = session.query(User).all()
for user in users:
    print(user.api_keys)  # Separate query for each user

# ✅ Eager loading  
users = session.query(User).options(joinedload(User.api_keys)).all()
for user in users:
    print(user.api_keys)  # Single query with joins
```

### **API Response Times**
- Authentication endpoints: < 200ms
- Database queries: < 100ms
- Health checks: < 50ms

### **Memory Usage**
- Maximum 512MB RAM during normal operation
- Monitor with: `docker stats`

## 🤝 Code Review Process

### **Before Creating PR**
1. ✅ All tests pass locally
2. ✅ Code follows style guidelines
3. ✅ Security checks pass
4. ✅ Documentation updated (if needed)
5. ✅ No TODO/FIXME comments (create issues instead)

### **PR Description Template**
```markdown
## What this PR does
Brief description of changes

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Security Impact
- [ ] No sensitive data exposed
- [ ] Input validation added
- [ ] Authentication/authorization checked
```

### **Reviewer Checklist**
- 🔍 Code quality and readability
- 🧪 Test coverage and quality
- 🔒 Security implications
- 📚 Documentation updates
- ⚡ Performance impact

## 🚀 Deployment

### **Development Environment**
```bash
# Local development
docker compose up -d

# Verify deployment
curl http://localhost:8000/health
```

### **Production Considerations**
- Set `DEBUG=false`
- Use strong JWT secrets
- Configure proper CORS origins
- Enable SSL/TLS
- Set up monitoring and logging

## 📚 Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **uv Documentation**: https://docs.astral.sh/uv/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Pytest**: https://docs.pytest.org/
- **Ruff**: https://docs.astral.sh/ruff/

## 🆘 Getting Help

1. **Check existing documentation** (README, this guide)
2. **Search existing issues** on GitHub
3. **Ask in team chat** for quick questions
4. **Create an issue** for bugs or feature requests
5. **Schedule a code review** for complex changes

## 📋 Checklists

### **New Feature Checklist**
- [ ] Create feature branch with proper naming
- [ ] Write tests first (TDD approach)
- [ ] Implement feature with proper error handling
- [ ] Update documentation
- [ ] Add/update type hints
- [ ] Perform security review
- [ ] Test locally with full stack
- [ ] Create PR with proper description
- [ ] Address review feedback
- [ ] Verify CI/CD passes

### **Bug Fix Checklist**
- [ ] Reproduce the bug locally
- [ ] Write test that demonstrates the bug
- [ ] Fix the bug (test should now pass)
- [ ] Verify fix doesn't break other functionality
- [ ] Add regression test if applicable
- [ ] Update documentation if needed
- [ ] Create PR with bug description and fix explanation

---

**Welcome to the team! Happy coding! 🎉**

For questions about this workflow, please create an issue or ask in the team chat.