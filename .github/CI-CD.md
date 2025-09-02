# GitHub Workflows and CI/CD

This directory contains GitHub Actions workflows and templates for the Kali AI-OS project.

## Workflows

### 🔐 Auth Server CI/CD (`auth-server-ci.yml`)
Comprehensive CI/CD pipeline for the authentication server that runs on every push and pull request affecting `auth-server/` files.

**Jobs:**
- **Code Quality Checks**: Ruff linting, Black formatting, isort, mypy type checking
- **Test Suite**: pytest with coverage across Python 3.11 and 3.12, PostgreSQL and Redis services
- **Security Scan**: Bandit security linting and Safety dependency checks
- **Docker Build**: Validates Docker image builds successfully
- **Integration Tests**: Full end-to-end testing with docker-compose
- **Notification**: Status reporting

**Triggers:**
- Push to `master`, `main`, or `develop` branches
- Pull requests targeting these branches
- Only when `auth-server/` files change

### 📋 PR Checks (`pr-checks.yml`)
Additional validations for pull requests to maintain code quality and consistency.

**Jobs:**
- **PR Validation**: Semantic PR titles, breaking change detection
- **Component Detection**: Smart detection of changed components
- **Task File Validation**: Ensures task documentation follows standards
- **Security Review**: Extra checks for security-related PRs
- **Size Check**: Warns about large PRs

## Development Setup

### Pre-commit Hooks
Install pre-commit hooks for local development:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Local Testing
Before pushing changes:

```bash
# In auth-server directory
cd auth-server

# Install dependencies
uv sync --all-extras

# Run linting
uv run ruff check .
uv run ruff format --check .
uv run black --check .
uv run isort --check .

# Run type checking
uv run mypy app/

# Run security checks
uv run bandit -r app/
uv run safety check

# Run tests
uv run pytest tests/ -v --cov=app

# Test Docker build
docker build -t kali-auth-test .
```

## Code Quality Standards

### Linting Tools
- **Ruff**: Fast Python linter (replaces flake8, isort partially)
- **Black**: Code formatter (88 char line length)
- **isort**: Import sorting (black profile)
- **mypy**: Type checking (permissive for now)

### Security Tools
- **Bandit**: Security linter for Python
- **Safety**: Dependency vulnerability scanner
- **Pre-commit**: Additional security pattern checks

### Testing Standards
- **Minimum 80% test coverage**
- **All tests must pass before merge**
- **Integration tests for critical paths**
- **Security tests for auth features**

### PR Requirements
- ✅ All CI checks must pass
- ✅ Code review approval required
- ✅ Semantic commit messages
- ✅ No merge conflicts
- ✅ Documentation updated if needed

## Issue Templates

### 🐛 Bug Report (`bug_report.yml`)
Structured template for reporting bugs with:
- Component selection
- Environment details
- Reproduction steps
- Expected vs actual behavior

### ✨ Feature Request (`feature_request.yml`)
Template for suggesting new features with:
- Problem description
- Proposed solution
- Priority assessment
- Implementation willingness

## Configuration Files

### `.pre-commit-config.yaml`
Pre-commit hooks configuration for local development with:
- File quality checks (trailing whitespace, file size limits)
- Python linting and formatting
- Security checks
- Test execution
- Custom auth-server specific checks

### `pyproject.toml` (auth-server)
Python project configuration with:
- Dependency management
- Tool configurations (ruff, black, isort, mypy, bandit, pytest)
- Coverage settings
- Development and test dependencies

## Best Practices

### Commit Messages
Use conventional commits format:
```
feat: add user registration endpoint
fix: resolve JWT token expiration bug
docs: update API documentation
test: add integration tests for auth flow
```

### Branch Strategy
- `master/main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature branches
- `fix/*`: Bug fix branches
- `chore/*`: Maintenance tasks

### Security Guidelines
- ❌ Never commit secrets or API keys
- ✅ Use environment variables for configuration
- ✅ Validate all inputs
- ✅ Follow OWASP guidelines
- ✅ Regular dependency updates

### Performance Standards
- 🚀 Tests should complete in < 2 minutes
- 🚀 Linting should complete in < 30 seconds
- 🚀 Docker builds should complete in < 5 minutes
- 🚀 Integration tests should complete in < 1 minute

---

For questions about CI/CD or contributing guidelines, please check the main project README or create an issue.
