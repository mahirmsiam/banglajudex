# BanglaJudex Setup Guide

This guide walks you through setting up BanglaJudex for local development.

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker (for PostgreSQL)
- Ollama (for LLM inference)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/BanglaJudex.git
cd BanglaJudex
```

### 2. Start PostgreSQL Database

```bash
# Using Docker
docker run -d --name postgres-banglajudex \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=banglajudex \
  -p 5433:5432 \
  postgres:15-alpine
```

Verify it's running:
```bash
docker ps
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/banglajudex
AD_JUDGMENTS_PATH=../ad_judgments
SC_JUDGMENTS_PATH=../sc_judgments
CHROMA_PERSIST_PATH=./chroma_data
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=mistral
EMBEDDING_MODEL=all-MiniLM-L6-v2
FRONTEND_URL=http://localhost:3000
```

### 5. Initialize Database

```bash
# From the backend directory
python init_db.py
```

Expected output:
```
Initializing database...
[OK] Database tables created successfully!
```

### 6. Start Backend Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Verify at: http://localhost:8000/health

### 7. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Access at: http://localhost:3000

### 8. Setup Ollama (for LLM features)

1. Download and install Ollama from https://ollama.com

2. Start Ollama:
   ```bash
   ollama serve
   ```

3. Pull the Mistral model:
   ```bash
   ollama pull mistral
   ```

### 9. Add PDF Judgments

Place your PDF files in:
- `ad_judgments/` - Appellate Division judgments
- `sc_judgments/` - High Court Division judgments

### 10. Start Ingestion

Trigger PDF processing:

```bash
curl -X POST http://localhost:8000/ingest/start
```

Or via API docs: http://localhost:8000/docs

Check status:
```bash
curl http://localhost:8000/ingest/status
```

## Verification Checklist

| Component | URL | Expected |
|-----------|-----|----------|
| Backend API | http://localhost:8000 | API info JSON |
| Health Check | http://localhost:8000/health | status: healthy |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Frontend | http://localhost:3000 | React app |
| Ollama | http://localhost:11434 | Ollama is running |

## Troubleshooting

### Database Connection Error

```
asyncpg.PostgresConnectionError: connection refused
```

**Solution**: Make sure PostgreSQL is running on the correct port (5432 or 5433)

### Ollama Connection Error

```
WinError 10061: No connection could be made
```

**Solution**: Start Ollama with `ollama serve`

### Module Not Found

```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Make sure you're running commands from the `backend` directory

### Port Already in Use

```
Address already in use
```

**Solution**: Kill the process using the port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

## Running Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov aiosqlite

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Docker Compose (Alternative)

For a containerized setup:

```bash
# Start all services
docker-compose up -d

# Pull Mistral model
docker exec -it banglajudex-llm ollama pull mistral

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Next Steps

After setup:

1. **Ingest PDFs**: Trigger `/ingest/start` to process judgments
2. **Search**: Use the frontend to search and filter cases
3. **Query**: Ask natural language questions about case law
4. **Explore API**: Check `/docs` for all available endpoints
