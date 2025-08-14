# Developer Workflow - Quick Reference

## 🚀 Setup (First Time Only)

```bash
# Clone and setup
git clone <your-repo-url>
cd Samsung-AI-os
pip install pre-commit && pre-commit install

# Setup auth server
cd auth-server
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras
```

## 📋 Daily Development Commands

### Start Development
```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Start services
docker compose up -d
```

### Development Cycle
```bash
cd auth-server

# Run tests
uv run --env-file ../.env pytest tests/ -v

# Code quality checks
uv run ruff check . --fix
uv run black .
uv run mypy app/ --ignore-missing-imports

# Manual test
curl http://localhost:8000/health
```

### Commit & Push
```bash
# Pre-commit will auto-run checks
git add .
git commit -m "feat: your feature description"
git push origin feat/your-feature-name
```

## 🔧 Essential Commands

| Task | Command |
|------|---------|
| **Install deps** | `uv sync --all-extras` |
| **Run tests** | `uv run --env-file ../.env pytest tests/` |
| **Start server** | `uv run uvicorn app.main:app --reload` |
| **Lint & format** | `uv run ruff check . --fix && uv run black .` |
| **Type check** | `uv run mypy app/ --ignore-missing-imports` |
| **Start services** | `docker compose up -d` |
| **View logs** | `docker compose logs -f auth-server` |
| **Run pre-commit** | `uv run --env-file ../.env pre-commit run --all-files --config ../.pre-commit-config.yaml` |

## 🐛 Troubleshooting

### Tests Failing?
```bash
# Check environment
cat ../.env | grep -E "(DATABASE_URL|ENCRYPTION_KEY|ENVIRONMENT)"

# Reset services
docker compose down && docker compose up -d
sleep 5
uv run --env-file ../.env pytest tests/
```

### Pre-commit Failing?
```bash
# Fix formatting issues
uv run ruff check . --fix
uv run black .
git add . && git commit -m "fix: formatting"
```

### CI/CD Failing?
```bash
# Run same checks as CI locally
uv run ruff check . --output-format=github
uv run black --check --diff .
uv run mypy app/ --ignore-missing-imports
uv run --env-file ../.env pytest tests/ --tb=short
```

## 📝 Commit Format
```bash
feat: add user registration endpoint
fix: resolve database connection timeout
docs: update API documentation
test: add integration tests
```

## 🌐 Service URLs
- **Auth Server**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## ⚠️ Before Creating PR
- [ ] Tests pass: `uv run --env-file ../.env pytest tests/`
- [ ] Code formatted: `uv run black . && uv run ruff check . --fix`
- [ ] Type checks: `uv run mypy app/ --ignore-missing-imports`
- [ ] Pre-commit passes: `uv run --env-file ../.env pre-commit run --all-files  --config ../.pre-commit-config.yaml
`

---
**Need help?** Check existing issues or create a new one.
