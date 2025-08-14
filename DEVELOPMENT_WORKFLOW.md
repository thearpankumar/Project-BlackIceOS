# Developer Workflow - Complete Guide

## 🚀 Setup (First Time Only)

```bash
# Clone and setup
git clone <your-repo-url>
cd Samsung-AI-os
pip install pre-commit && pre-commit install

# Setup auth server with uv
cd auth-server
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras
```

## 📦 UV Package Management

**uv** is our modern, fast Python package manager. Use it for all Python operations:

```bash
# Install dependencies
uv sync --all-extras          # Install all deps including dev tools
uv sync --no-dev             # Production deps only
uv add fastapi               # Add new dependency
uv add pytest --dev         # Add dev dependency
uv remove package-name      # Remove dependency

# Run commands in virtual environment
uv run python script.py     # Run Python scripts
uv run pytest tests/        # Run tests
uv run uvicorn app.main:app  # Start server
```

## 📋 Daily Development Commands

### Start Development
```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Start services (from project root)
docker compose up -d

# Verify auth server is working
curl http://localhost:8000/health
```

### Development Cycle
```bash
cd auth-server

# Run all tests with coverage
uv run --env-file ../.env pytest tests/ -v --cov=app --cov-report=term-missing

# Quick test run
uv run --env-file ../.env pytest tests/ -v

# Run specific test file
uv run --env-file ../.env pytest tests/test_auth.py -v

# Run specific test method
uv run --env-file ../.env pytest tests/test_auth.py::TestUserRegistration::test_user_registration_success -v
```

### Code Quality & Formatting
```bash
# Linting (check and fix)
uv run ruff check .                    # Check for issues
uv run ruff check . --fix              # Auto-fix issues
uv run ruff check . --output-format=github  # CI format

# Code formatting
uv run black .                         # Format all files
uv run black --check .                 # Check formatting only
uv run black --diff .                  # Show formatting changes

# Import sorting
uv run isort .                         # Sort imports
uv run isort --check-only .            # Check import sorting

# Type checking
uv run mypy app/                       # Type check
uv run mypy app/ --ignore-missing-imports  # Ignore missing stubs

# Security scanning
uv run bandit -r app/                  # Security linter
uv run safety check                    # Vulnerability check

# All quality checks at once
uv run ruff check . --fix && uv run black . && uv run isort . && uv run mypy app/ --ignore-missing-imports
```

### Server Operations
```bash
# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start server with specific env
uv run --env-file ../.env uvicorn app.main:app --reload

# Run with debug logging
DEBUG=true uv run uvicorn app.main:app --reload --log-level debug
```

### Database Operations
```bash
# Check database health (requires services running)
uv run python -c "from app.database.connection import check_database_health; print('✅ DB healthy' if check_database_health() else '❌ DB issues')"

# Run database migrations
PGPASSWORD=your_password psql -h localhost -U kali_auth -d kali_auth_db -f migrations/001_initial_schema.sql
```

## 🔧 Essential Commands Reference

| Task | Command |
|------|---------|
| **Install all deps** | `uv sync --all-extras` |
| **Add dependency** | `uv add package-name` |
| **Add dev dependency** | `uv add package-name --dev` |
| **Run tests** | `uv run --env-file ../.env pytest tests/` |
| **Run tests with coverage** | `uv run --env-file ../.env pytest tests/ --cov=app` |
| **Start server** | `uv run uvicorn app.main:app --reload` |
| **Lint & fix** | `uv run ruff check . --fix` |
| **Format code** | `uv run black .` |
| **Sort imports** | `uv run isort .` |
| **Type check** | `uv run mypy app/ --ignore-missing-imports` |
| **Security scan** | `uv run bandit -r app/` |
| **Dependency check** | `uv run safety check` |
| **Start services** | `docker compose up -d` |
| **View logs** | `docker compose logs -f auth-server` |
| **Stop services** | `docker compose down` |
| **Run pre-commit** | `uv run --env-file ../.env pre-commit run --all-files --config ../.pre-commit-config.yaml` |

## 🔄 Git Workflow & Pre-commit

### Commit & Push
```bash
# Stage changes
git add .

# Pre-commit will auto-run these checks:
# - ruff (linting & fixing)
# - black (formatting) 
# - isort (import sorting)
# - mypy (type checking)
# - bandit (security)
# - pytest (tests)

# Commit (triggers pre-commit hooks)
git commit -m "feat: your feature description"

# Push to remote
git push origin feat/your-feature-name
```

### Manual Pre-commit
```bash
# Run all pre-commit hooks manually
uv run --env-file ../.env pre-commit run --all-files --config ../.pre-commit-config.yaml

# Run specific hook
pre-commit run ruff --all-files
pre-commit run black --all-files
pre-commit run pytest
```

## 🐛 Troubleshooting Guide

### Tests Failing?
```bash
# Check environment variables
cat ../.env | grep -E "(DATABASE_URL|ENCRYPTION_KEY|ENVIRONMENT|JWT_SECRET_KEY)"

# Reset services and wait
docker compose down && docker compose up -d
sleep 10

# Run tests with verbose output
uv run --env-file ../.env pytest tests/ -v --tb=short

# Run tests with full error details
uv run --env-file ../.env pytest tests/ -v --tb=long

# Debug specific test
uv run --env-file ../.env pytest tests/test_auth.py::TestUserRegistration::test_user_registration_success -v -s
```

### Linting/Formatting Issues?
```bash
# Fix all formatting issues
uv run ruff check . --fix
uv run black .
uv run isort .

# Check what would be changed
uv run black --diff .
uv run ruff check .

# Commit formatting fixes
git add . && git commit -m "style: fix formatting"
```

### Import/Dependency Issues?
```bash
# Reinstall dependencies
uv sync --all-extras

# Check installed packages
uv pip list

# Update dependencies
uv lock --upgrade

# Clear uv cache
uv cache clean
```

### Docker Issues?
```bash
# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d

# Check logs
docker compose logs auth-server
docker compose logs postgres

# Clean docker system
docker system prune -f
```

### CI/CD Failing?
```bash
# Run same checks as CI locally
uv run ruff check . --output-format=github
uv run black --check --diff .
uv run isort --check-only --diff .
uv run mypy app/ --ignore-missing-imports
uv run bandit -r app/ -f json || true
uv run safety check --json || true
uv run --env-file ../.env pytest tests/ --tb=short --cov=app --cov-fail-under=50

# Test docker build locally
docker build -t test-auth-server ./auth-server
docker run --rm -e ENCRYPTION_KEY="test-key" -e JWT_SECRET_KEY="test-jwt" test-auth-server uv run python -c "from app.main import app; print('✅ Works')"
```

## 📝 Commit Message Format

Follow conventional commits:

```bash
feat: add user registration endpoint
fix: resolve database connection timeout  
docs: update API documentation
test: add integration tests for auth
style: fix code formatting
refactor: restructure user models
perf: optimize database queries
chore: update dependencies
```

## 🌐 Service URLs

- **Auth Server**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Database**: postgresql://localhost:5432/kali_auth_db
- **Redis**: redis://localhost:6379/0

## 🧪 Testing Strategy

### Test Types
```bash
# Unit tests (fast)
uv run --env-file ../.env pytest tests/test_auth.py tests/test_encryption.py -v

# Integration tests (slower, requires DB)
uv run --env-file ../.env pytest tests/test_database.py -v

# All tests with coverage
uv run --env-file ../.env pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Tests with specific markers
uv run --env-file ../.env pytest tests/ -m "not integration" -v  # Skip integration tests
```

### Test Coverage
```bash
# Generate coverage report
uv run --env-file ../.env pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Check coverage threshold
uv run --env-file ../.env pytest tests/ --cov=app --cov-fail-under=50
```

## ⚠️ Pre-PR Checklist

Before creating a Pull Request, ensure:

- [ ] **Dependencies**: `uv sync --all-extras` completed successfully
- [ ] **Tests pass**: `uv run --env-file ../.env pytest tests/ --cov=app --cov-fail-under=50`
- [ ] **Linting**: `uv run ruff check . --fix` (no remaining issues)
- [ ] **Formatting**: `uv run black .` (all files formatted)
- [ ] **Import sorting**: `uv run isort .` (imports properly sorted)  
- [ ] **Type checking**: `uv run mypy app/ --ignore-missing-imports` (no type errors)
- [ ] **Security**: `uv run bandit -r app/` (no security issues)
- [ ] **Pre-commit**: `uv run --env-file ../.env pre-commit run --all-files --config ../.pre-commit-config.yaml` passes
- [ ] **Docker build**: `docker build -t test ./auth-server` succeeds
- [ ] **Integration**: Services start with `docker compose up -d`
- [ ] **API health**: `curl -f http://localhost:8000/health` returns 200

## 🚀 Production Deployment

### Environment Variables Required
```bash
# Required in production
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://host:port/0
JWT_SECRET_KEY=your-super-secure-jwt-secret-key
ENCRYPTION_KEY=your-32-byte-base64-fernet-key

# Optional
DEBUG=false
HOST=0.0.0.0  
PORT=8000
ALLOWED_ORIGINS=["https://yourdomain.com"]
```

### Production Build
```bash
# Build production image
docker build -t auth-server:latest ./auth-server

# Run production container
docker run -p 8000:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e REDIS_URL="$REDIS_URL" \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e ENCRYPTION_KEY="$ENCRYPTION_KEY" \
  -e DEBUG=false \
  auth-server:latest
```

---

## 📚 Additional Resources

- **uv Documentation**: https://docs.astral.sh/uv/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic V2 Guide**: https://docs.pydantic.dev/latest/migration/
- **Docker Compose Reference**: https://docs.docker.com/compose/
- **Pre-commit Hooks**: https://pre-commit.com/

---

**Need help?** 
- Check existing GitHub issues
- Review error logs with `docker compose logs auth-server`  
- Run diagnostics with `uv run --env-file ../.env pytest tests/ -v --tb=long`
- Create a detailed issue with reproduction steps

**Remember**: Always use `uv run` for Python commands to ensure proper virtual environment activation! 🚀