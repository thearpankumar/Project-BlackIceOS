# Samsung AI OS Control System

A comprehensive dual-component system for intelligent desktop automation and secure authentication services.

## 🏗️ Project Architecture

This repository contains two main components:

### 🤖 **Ai0S** - Agentic AI OS Control System
A sophisticated desktop application for voice-controlled OS automation using AI agents, built with CustomTkinter, FastAPI, LangGraph, and MCP (Model Context Protocol).

### 🔐 **Auth Server** - Secure Authentication Service  
A professional FastAPI-based authentication server with PostgreSQL, Redis, JWT tokens, and comprehensive security features.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [UV](https://docs.astral.sh/uv/) package manager
- PostgreSQL (for auth-server)
- Redis (for auth-server)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Samsung-AI-os
   ```

2. **Set up Ai0S (AI Control System)**
   ```bash
   cd Ai0S
   uv sync --all-extras
   ```

3. **Set up Auth Server**
   ```bash
   cd ../auth-server
   uv sync --all-extras
   ```

### Environment Configuration

#### Ai0S Configuration
Create `Ai0S/.env`:
```bash
# AI Models (Required)
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Model Selection
GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_MODEL=gemini-2.0-flash-exp

# UI Settings
UI_THEME=dark
WINDOW_WIDTH=1400
WINDOW_HEIGHT=900

# Voice Settings
ENABLE_VOICE=true
AUDIO_SAMPLE_RATE=16000

# Communication
WS_HOST=127.0.0.1
WS_PORT=8001
API_PORT=8000
```

#### Auth Server Configuration
Create `auth-server/.env`:
```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/kali_auth_db
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
ENCRYPTION_KEY=your-fernet-encryption-key

# Environment
DEBUG=false
ENVIRONMENT=production
```

## 🎮 Running the Applications

### Start Ai0S (AI Control System)
```bash
cd Ai0S
uv run python run_app.py
```
Or using the entry point:
```bash
uv run ai0s
```

### Start Auth Server
```bash
cd auth-server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Both with Docker Compose
```bash
docker compose up -d
```

## 🎯 Ai0S Features

### **Professional Desktop UI**
- Modern CustomTkinter interface with dark/light themes
- Real-time voice input with audio visualization
- Interactive chat interface with rich formatting
- Step-by-step execution tracking with live progress
- Live screenshot preview and visual monitoring

### **Advanced AI Integration**
- **Gemini 2.0 Flash**: Voice transcription and vision analysis
- **Groq LLaMA**: Intelligence, planning, and decision making
- **LangGraph**: Sophisticated state machine orchestration
- **Dynamic Planning**: AI generates execution plans in real-time
- **Error Recovery**: Intelligent plan adaptation on failures

### **Cross-Platform Automation (MCP)**
- **30+ Tools**: Browser, application, UI, system, file operations
- **Platform Detection**: Windows, macOS, Linux support
- **Safety Controls**: Permission validation and rate limiting
- **Dynamic Commands**: OS-appropriate command generation

## 🔐 Auth Server Features

### **Security & Authentication**
- JWT token-based authentication with refresh tokens
- Bcrypt password hashing with salt
- Rate limiting and brute force protection
- Account lockout and security monitoring
- Role-based access control (RBAC)

### **Database & Caching**
- PostgreSQL with Alembic migrations
- Redis for session management and caching
- Connection pooling and optimization
- Health monitoring and metrics

### **API Features**
- RESTful API with OpenAPI/Swagger documentation
- Input validation with Pydantic models
- Comprehensive error handling
- CORS support for web integration
- Health checks and monitoring endpoints

## 🧪 Development

### Code Quality (Ai0S)
```bash
cd Ai0S
uv run ruff check .
uv run black --check .
uv run isort --check-only .
uv run mypy src/
```

### Code Quality (Auth Server)
```bash
cd auth-server
uv run ruff check .
uv run black --check .
uv run isort --check-only .
uv run mypy app/
```

### Testing (Auth Server)
```bash
cd auth-server
uv run pytest tests/ --cov=app
```

## 📁 Project Structure

```
Samsung-AI-os/
├── Ai0S/                          # AI Control System
│   ├── src/Ai0S/
│   │   ├── desktop_app/           # CustomTkinter GUI
│   │   ├── backend/               # FastAPI + AI Core
│   │   ├── agents/                # LangGraph Orchestrator
│   │   ├── mcp_server/            # MCP Tools (30+ tools)
│   │   ├── config/                # Settings management
│   │   └── utils/                 # Platform utilities
│   ├── pyproject.toml
│   └── run_app.py
├── auth-server/                   # Authentication Service
│   ├── app/
│   │   ├── auth/                  # Authentication logic
│   │   ├── database/              # Database models & connection
│   │   ├── core/                  # Core utilities
│   │   └── main.py                # FastAPI application
│   ├── tests/                     # Test suites
│   ├── migrations/                # Database migrations
│   ├── pyproject.toml
│   └── Dockerfile
├── docker-compose.yml             # Multi-service orchestration
└── README.md                      # This file
```

## 🚀 Deployment

### Docker Deployment
```bash
# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production
- Set strong JWT secrets and encryption keys
- Configure proper database connections
- Set up monitoring and logging
- Configure reverse proxy (nginx/traefik)
- Set up SSL certificates

## 🔧 API Documentation

### Auth Server Endpoints
- **POST** `/auth/register` - User registration
- **POST** `/auth/login` - User authentication
- **POST** `/auth/refresh` - Token refresh
- **GET** `/auth/me` - User profile
- **POST** `/auth/logout` - User logout
- **GET** `/health` - Health check
- **GET** `/docs` - Interactive API documentation

### Ai0S Backend Endpoints
- **POST** `/api/execute` - Execute AI commands
- **GET** `/api/status` - System status
- **WebSocket** `/ws` - Real-time communication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Run code quality checks
5. Commit your changes: `git commit -m 'feat: add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Commit Convention
Use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Groq** for high-performance LLM inference
- **Google** for Gemini AI models
- **Anthropic** for inspiration from Claude
- **CustomTkinter** for modern Python GUI framework
- **FastAPI** for high-performance web framework
- **LangGraph** for AI agent orchestration

## 🆘 Support

For support and questions:
1. Check the documentation in each component's README
2. Review the API documentation at `/docs`
3. Open an issue on GitHub
4. Check existing issues and discussions

---

**🎯 Implementation Status: Production Ready**

Both components are fully functional and production-ready with comprehensive features, security, and professional architecture following enterprise development best practices.