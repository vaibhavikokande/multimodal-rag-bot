# Multimodal Enterprise RAG Bot

An enterprise-grade, production-ready **Retrieval-Augmented Generation (RAG)** platform that understands and answers questions from any data format — PDFs, DOCX, PPTX, images, videos, audio, diagrams, and more.

---

## Screenshots

### Login Page
![Login](screenshots/01_login.png)

### AI Chat Interface
![Chat](screenshots/02_chat.png)

### Knowledge Base — Documents
![Documents](screenshots/03_documents.png)

### Analytics Dashboard
![Analytics](screenshots/04_analytics.png)

### Admin Panel — User Management
![Admin](screenshots/06_admin.png)

### Register Page
![Register](screenshots/07_register.png)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        NGINX (Port 80/443)                       │
│                    Reverse Proxy + Rate Limiting                 │
└──────────────────────┬──────────────────┬───────────────────────┘
                       │                  │
          ┌────────────▼──────┐  ┌────────▼──────────┐
          │  Next.js Frontend  │  │  FastAPI Backend   │
          │   (Port 3000)      │  │   (Port 8000)      │
          └───────────────────┘  └──────────┬─────────┘
                                             │
              ┌──────────────────────────────┼──────────────────┐
              │                              │                   │
   ┌──────────▼──────────┐  ┌───────────────▼────┐  ┌─────────▼───────┐
   │  PostgreSQL (5432)   │  │  ChromaDB (8001)    │  │  Redis (6379)   │
   │  Relational Store    │  │  Vector Database    │  │  Cache + Queue  │
   └─────────────────────┘  └────────────────────┘  └────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| AI/LLM | GPT-4o, Claude 3.5 Sonnet, OpenAI Embeddings |
| Vector DB | ChromaDB (default) / Pinecone |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| OCR | Tesseract + PaddleOCR |
| Audio/Video | OpenAI Whisper, MoviePy, OpenCV |
| Auth | JWT + RBAC |
| Deployment | Docker, Docker Compose, Nginx |

---

## Features

### Document Processing
- ✅ PDF (with OCR fallback for scanned PDFs)
- ✅ DOCX, PPTX, TXT, CSV, XLSX
- ✅ Auto-chunking with overlap
- ✅ Table extraction
- ✅ Metadata extraction

### Image Understanding (GPT-4 Vision)
- ✅ Architecture diagrams
- ✅ Flowcharts and UML
- ✅ Charts and graphs (data extraction)
- ✅ Technical drawings
- ✅ Screenshots

### Video & Audio
- ✅ Audio extraction from video
- ✅ Whisper speech-to-text transcription
- ✅ Keyframe extraction + visual analysis
- ✅ Support for MP4, AVI, MOV, MP3, WAV, M4A

### RAG Pipeline
- ✅ Hybrid search (vector + BM25 keyword)
- ✅ Query reformulation with conversation context
- ✅ Re-ranking for optimal relevance
- ✅ Citation-based responses
- ✅ Real-time streaming (SSE)

### AI Chat
- ✅ ChatGPT-style interface
- ✅ Streaming responses with typing animation
- ✅ Multi-model support (GPT-4o, Claude 3.5)
- ✅ Conversation memory (last 10 messages)
- ✅ Source citations with document references
- ✅ Thumbs up/down feedback

### Enterprise Features
- ✅ JWT Authentication + RBAC (5 roles)
- ✅ Multi-workspace support
- ✅ Admin dashboard with user management
- ✅ Usage analytics and query logs
- ✅ Auto-tagging and summarization
- ✅ Dark/light mode

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (required)
- Anthropic API key (optional)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/multimodal-rag-bot
cd multimodal-rag-bot

# Configure backend
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY

# Configure frontend
cp frontend/.env.local.example frontend/.env.local
```

### 2. Launch with Docker Compose

```bash
docker-compose up -d
```

Services will start:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs
- ChromaDB: http://localhost:8001

### 3. Login

Default admin credentials:
- Email: `admin@company.com`
- Password: `Admin@123456`

---

## Manual Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and DB connection

# Start PostgreSQL and Redis (using Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine
docker run -d -p 8001:8000 chromadb/chroma

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local

# Start development server
npm run dev
```

---

## API Reference

### Authentication
```
POST /api/v1/auth/register    — Register new user
POST /api/v1/auth/login       — Login (returns JWT)
POST /api/v1/auth/refresh     — Refresh token
GET  /api/v1/auth/me          — Get current user
```

### Documents
```
POST /api/v1/documents/upload                — Upload files
GET  /api/v1/documents/?workspace_id=1       — List documents
GET  /api/v1/documents/{id}                  — Document details
DELETE /api/v1/documents/{id}                — Delete document
POST /api/v1/documents/{id}/reprocess        — Re-index document
```

### Chat (RAG)
```
POST /api/v1/chat/sessions                   — Create session
GET  /api/v1/chat/sessions?workspace_id=1    — List sessions
POST /api/v1/chat/message                    — Send message (sync)
POST /api/v1/chat/stream                     — Send message (streaming SSE)
GET  /api/v1/chat/sessions/{id}/messages     — Get history
```

### Admin
```
GET /api/v1/admin/dashboard        — Platform metrics
GET /api/v1/admin/users            — User management
PUT /api/v1/admin/users/{id}       — Update user role/status
GET /api/v1/admin/query-logs       — Query logs
GET /api/v1/admin/analytics/usage  — Usage analytics
```

---

## User Roles

| Role | Permissions |
|------|-------------|
| `superadmin` | Full system access |
| `admin` | User management, analytics |
| `manager` | Workspace management |
| `user` | Upload, chat, view documents |
| `viewer` | Read-only access |

---

## Environment Variables

### Backend (`.env`)
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `DATABASE_URL` | PostgreSQL async URL | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `SECRET_KEY` | JWT signing key (32+ chars) | Yes |
| `VECTOR_DB_PROVIDER` | `chromadb` or `pinecone` | Yes |
| `CHROMA_HOST` | ChromaDB host | If chromadb |
| `PINECONE_API_KEY` | Pinecone API key | If pinecone |

### Frontend (`.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |

---

## Folder Structure

```
multimodal-rag-bot/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/      # REST API routes
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   ├── workspaces.py
│   │   │   └── admin.py
│   │   ├── core/                  # Config, security, deps
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── crud/                  # Database operations
│   │   ├── services/
│   │   │   ├── document_processor/ # PDF, DOCX, PPTX parsing
│   │   │   ├── image_analyzer/    # GPT-4 Vision
│   │   │   ├── video_processor/   # Whisper transcription
│   │   │   ├── embedding_pipeline/ # OpenAI embeddings + vector DB
│   │   │   └── rag_engine/        # RAG query + streaming
│   │   ├── db/                    # Database session
│   │   └── main.py               # FastAPI app
│   ├── alembic/                   # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/         # Login page
│   │   ├── (auth)/register/      # Register page
│   │   └── (dashboard)/
│   │       ├── chat/             # AI chat interface
│   │       ├── documents/        # Document management
│   │       ├── analytics/        # Usage analytics
│   │       └── admin/            # Admin panel
│   ├── components/
│   │   ├── chat/                 # ChatSidebar, ChatWindow
│   │   ├── layout/               # Sidebar, Header
│   │   └── ui/                   # StatusBadge, etc.
│   ├── lib/
│   │   ├── store/                # Zustand state (auth, workspace, chat)
│   │   ├── hooks/                # useDocuments, etc.
│   │   └── api.ts               # Axios client
│   ├── Dockerfile
│   └── package.json
│
├── nginx/nginx.conf               # Reverse proxy config
├── docker-compose.yml             # Full stack orchestration
└── scripts/init.sql              # DB initialization
```

---

## Deployment

### Production (Docker Compose)

```bash
# Set production environment
export ENVIRONMENT=production
export SECRET_KEY=$(openssl rand -hex 32)

# Use production compose
docker-compose -f docker-compose.yml up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Vercel (Frontend only)
```bash
cd frontend
vercel deploy
```

### Cloud Database
Update `DATABASE_URL` in `.env` to point to:
- **AWS RDS**: `postgresql+asyncpg://user:pass@rds-endpoint:5432/ragbot`
- **Supabase**: `postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres`
- **Neon**: `postgresql+asyncpg://user:pass@ep-xxx.neon.tech/ragbot`

---

## Performance Tuning

- **Chunking**: Adjust `CHUNK_SIZE` (default 1000 tokens) and `CHUNK_OVERLAP` (200)
- **Retrieval**: Tune `TOP_K_RESULTS` (default 10) and `HYBRID_SEARCH_ALPHA` (0=keyword, 1=vector)
- **Models**: Use `gpt-4o-mini` for faster, cheaper responses; `gpt-4o` for best quality
- **Workers**: Scale `uvicorn --workers N` based on CPU cores
- **Celery**: Increase `--concurrency` for parallel document processing

---

## License

MIT License — free to use, modify, and deploy commercially.
