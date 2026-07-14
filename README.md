# AI Software Engineering Platform

An AI-powered software engineering platform with multi-agent orchestration. Built with FastAPI, Next.js 14, PostgreSQL, Redis, and Qdrant.

## Architecture

- **Deterministic Central Orchestrator**: State machine controls workflow execution
- **7 Specialized Agents**: Planner, Researcher, Coder, Test Writer, Critic, Debugger, Doc Writer
- **AI Providers**: DeepSeek, Gemini, GPT (direct API calls)
- **Vector Search**: Qdrant for repository context retrieval
- **Real-time Updates**: WebSocket notifications

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + SQLAlchemy + Alembic |
| Frontend | Next.js 14 + Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache/Broker | Redis 7 |
| Vector DB | Qdrant |
| Task Queue | Celery |
| Container | Docker Compose |

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/csebelal/ai-coding-platform.git
   cd ai-coding-platform
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start services:
   ```bash
   docker compose up --build -d
   ```

4. Run database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Qdrant Dashboard: http://localhost:6333/dashboard

## Workflow States

```
INITIALIZED → PLANNING → RESEARCHING → WRITING_TESTS → CODING → VERIFYING → REVIEWING → DOCUMENTING → COMPLETED
                                    ↻ DEBUGGING (max 3 retries)
```

## Development

### Backend
```bash
docker compose exec backend bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Running Tests
```bash
docker compose exec backend pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/projects | List projects |
| POST | /api/v1/projects | Create project |
| POST | /api/v1/tasks | Create task |
| POST | /api/v1/tasks/{id}/execute | Execute task |
| GET | /api/v1/demo/workflow | Demo workflow |
| PUT | /api/v1/preferences | Update preferences |
| WS | /ws/{task_id} | Real-time updates |

## Project Structure

```
ai-coding-platform/
├── backend/
│   ├── app/
│   │   ├── agents/          # 7 AI agents + orchestrator
│   │   ├── api/             # FastAPI routers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── memory/          # Conversation/repo memory
│   ├── tests/               # Test suite
│   └── alembic/             # DB migrations
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   └── lib/             # API client, auth, hooks
├── worker/                  # Celery worker
├── docker-compose.yml       # Development
└── docker-compose.prod.yml  # Production
```
