# High Level Architecture

## Technical Summary

LangBuilder is a **Python web application with React frontend** for building language model workflows (LangChain-based). It's a fork/derivative of LangFlow with enterprise enhancements planned.

**Architecture Pattern**: Monolithic backend (FastAPI) + SPA frontend (React), deployed as a single service or containerized.

**Current State**:
- **Authentication**: JWT-based with OAuth2 password flow, optional auto-login for development
- **Authorization**: Basic user/superuser roles ONLY (binary permissions)
- **Database**: SQLAlchemy + SQLModel with async support
- **API**: RESTful with FastAPI, WebSocket support for real-time features
- **State Management**: React Context + Zustand stores

## Actual Tech Stack

| Category        | Technology           | Version       | Notes                                    |
| --------------- | -------------------- | ------------- | ---------------------------------------- |
| **Backend**     |                      |               |                                          |
| Runtime         | Python               | 3.10-3.13     | Type hints, async/await                  |
| Framework       | FastAPI              | (via deps)    | Async ASGI framework                     |
| ORM             | SQLModel/SQLAlchemy  | >=2.0.38      | Async session support                    |
| Database        | SQLite/PostgreSQL    | Varies        | Configurable via env (default SQLite)    |
| Authentication  | python-jose          | (JWT)         | JWT token generation/validation          |
| Password Hash   | cryptography/Fernet  | (via deps)    | Password hashing                         |
| Migration       | Alembic              | (included)    | Database migrations                      |
| Validation      | Pydantic             | v2            | Data validation via SQLModel             |
| **Frontend**    |                      |               |                                          |
| Runtime         | Node.js              | 18+           | Development only                         |
| Framework       | React                | 18.3.1        | Functional components, hooks             |
| Build Tool      | Vite                 | 5.4.19        | Fast dev server, HMR                     |
| State Mgmt      | Zustand              | 4.5.2         | Lightweight state management             |
| UI Library      | Radix UI + Tailwind  | Latest        | Headless components + utility CSS        |
| Routing         | React Router         | 6.23.1        | Client-side routing                      |
| HTTP Client     | Axios                | 1.7.4         | API requests                             |
| Type Checking   | TypeScript           | 5.4.5         | Strict mode                              |
| **DevOps**      |                      |               |                                          |
| Package Manager | uv (backend)         | Latest        | Fast Python package manager              |
| Package Manager | npm (frontend)       | Latest        | Node.js package manager                  |
| Build System    | Make                 | GNU Make      | Unified dev commands                     |
| Containerization| Docker               | Latest        | Multi-service docker-compose             |

## Repository Structure Reality Check

- **Type**: Monorepo (backend + frontend in single repo)
- **Package Manager**: `uv` for Python, `npm` for Node.js
- **Notable**: Frontend builds static files that are served by backend in production

---
