# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MyUnla** is a Python-based MCP (Model Context Protocol) Gateway system that provides:
- Multi-tenant MCP server management
- HTTP/SSE/STDIO protocol gateway
- RESTful API server with FastAPI
- Vue.js frontend for configuration management
- Docker and Kubernetes deployment support

## Architecture

### Core Components

#### 1. API Server (`myunla/app.py`)
- **Framework**: FastAPI with async support
- **Port**: 8000 (default)
- **Routes**: `/api/v1/auth`, `/api/v1/mcp`, `/api/v1/openapi`, `/api/v1/tenant`
- **Database**: SQLAlchemy with async support (SQLite/PostgreSQL/MySQL)

#### 2. Gateway Server (`myunla/gateway/server.py`)
- **Protocol**: MCP (Model Context Protocol) implementation
- **Port**: 8001 (default)
- **Endpoints**:
  - `/{prefix}/sse` - Server-Sent Events
  - `/{prefix}/message` - JSON-RPC message handling
  - `/{prefix}/mcp` - MCP protocol endpoints
- **Session Management**: Redis/memory-based session storage

#### 3. Frontend (`web/`)
- **Framework**: Vue 3 + TypeScript + Element Plus
- **Port**: 5173 (development)
- **Build Tool**: Vite
- **API Client**: Auto-generated via Orval from OpenAPI specs

#### 4. State Management (`myunla/gateway/state.py`)
- **Runtime State**: Per-prefix MCP configuration
- **Protocol Types**: HTTP, SSE, STREAMABLE, STDIO, GRPC
- **Transport Layer**: Pluggable transport system
- **Multi-tenancy**: Tenant-based configuration isolation

## Development Commands

### Backend (Python)
```bash
# Install dependencies
uv sync

# Format code
make fmt

# Database migrations
make makemigration  # Create new migration
make migrate        # Apply migrations

# Start servers
make start-servers      # Production mode
make start-servers-dev  # Development with hot reload
make start-api         # API server only (port 8000)
make start-gateway     # Gateway server only (port 8001)
make stop-servers      # Stop all servers

# API documentation
dump-api-docs          # Generate OpenAPI docs

# Pre-commit setup
make setup-precommit
make precommit-run
```

### Frontend (Vue.js)
```bash
# Navigate to frontend
cd web

# Install dependencies
pnpm install

# Development server
pnpm run dev

# Build for production
pnpm run build

# Generate API types from backend
pnpm run generate-api-types
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=myunla

# Run specific test file
pytest tests/test_specific.py

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

## Key Configuration Files

### Backend Configuration
- `myunla/config/apiserver_config.py` - API server settings
- `myunla/config/session_config.py` - Session storage (Redis/memory)
- `myunla/config/notifier_config.py` - Notification system
- `myunla/alembic.ini` - Database migrations

### Frontend Configuration
- `web/vite.config.ts` - Vite build configuration
- `web/orval.config.ts` - API client generation
- `web/uno.config.ts` - UnoCSS styling
- `web/eslint.config.js` - ESLint rules

### Deployment
- `deploy/helm/` - Kubernetes Helm charts
- `makefile` - Build and deployment commands
- `pyproject.toml` - Python project configuration

## Database Schema

### Core Models
- **User**: Authentication and authorization
- **Tenant**: Multi-tenant isolation
- **McpConfig**: MCP server configurations
- **Router**: Route definitions for MCP servers
- **Tool**: Available MCP tools
- **HttpServer**: HTTP server configurations

### Migration Commands
```bash
# Create migration
alembic -c myunla/alembic.ini revision --autogenerate -m "description"

# Apply migrations
alembic -c myunla/alembic.ini upgrade head

# Downgrade migration
alembic -c myunla/alembic.ini downgrade -1
```

## API Endpoints

### Authentication (`/api/v1/auth`)
- POST `/register` - User registration
- POST `/login` - User login
- POST `/logout` - User logout
- GET `/me` - Current user info
- POST `/change-password` - Password change

### MCP Management (`/api/v1/mcp`)
- GET `/configs` - List MCP configurations
- POST `/configs` - Create new MCP config
- GET `/configs/{name}` - Get specific config
- PUT `/configs/{name}` - Update config
- DELETE `/configs/{name}` - Delete config

### Tenant Management (`/api/v1/tenant`)
- GET `/tenants` - List tenants
- POST `/tenants` - Create tenant
- GET `/tenants/{id}` - Get tenant details
- PUT `/tenants/{id}` - Update tenant
- DELETE `/tenants/{id}` - Delete tenant

## Environment Variables

### Backend
```bash
# Database
DATABASE_URL=sqlite:///myunla/config/db.sqlite3
# Or: postgresql+asyncpg://user:pass@localhost/myunla

# Security
SECRET_KEY=your-secret-key
CREATE_DEFAULT_DATA=false
DEBUG=true

# Redis (optional, for session storage)
REDIS_URL=redis://localhost:6379/0
```

### Frontend
```bash
# Development
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Code Structure

```
myunla/
├── app.py                 # Main FastAPI application
├── gateway/               # MCP gateway implementation
│   ├── server.py          # Gateway server entry point
│   ├── state.py           # Global state management
│   ├── transports/        # Protocol transports (HTTP/SSE/STDIO)
│   ├── session/           # Session management
│   └── notifier/          # Notification system
├── controllers/           # API controllers
├── repos/                 # Database repositories
├── models/                # SQLAlchemy models
├── schema/                # Pydantic schemas
├── utils/                 # Utility functions
└── config/               # Configuration modules

web/
├── src/
│   ├── components/        # Vue components
│   ├── stores/           # Pinia stores
│   ├── router/           # Vue Router
│   └── api/              # API client (auto-generated)
├── generated/            # Auto-generated code from OpenAPI
└── public/               # Static assets
```

## Development Workflow

1. **Start Backend**: `make start-servers-dev`
2. **Start Frontend**: `cd web && pnpm run dev`
3. **Access UI**: http://localhost:5173
4. **API Docs**: http://localhost:8000/docs

## Common Issues & Solutions

### Port Conflicts
- API Server: 8000
- Gateway Server: 8001
- Frontend Dev: 5173
- Redis: 6379

### Database Issues
- Run `make migrate` after schema changes
- Check `myunla/config/db.sqlite3` permissions
- For PostgreSQL: ensure asyncpg is installed

### Frontend API Connection
- Ensure `VITE_API_BASE_URL` matches backend port
- Run `pnpm run generate-api-types` after backend changes

### Session Storage
- Default: memory storage
- For production: configure Redis in `session_config.py`

## Deployment

### Docker
```bash
# Build images
docker build -t myunla:latest .

# Run with Docker Compose
docker-compose up -d
```

### Kubernetes
```bash
# Install with Helm
helm install myunla deploy/helm/

# Upgrade
helm upgrade myunla deploy/helm/
```
