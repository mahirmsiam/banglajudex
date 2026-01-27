# BanglaJudex

> **Extractive Conversational Legal Research System for Bangladesh Judgments**

A production-grade web application that enables users to query, filter, and conversationally interact with Bangladesh Supreme Court judgments (Appellate Division and High Court Division).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

---

## 🎯 Features

- **🔍 Hybrid Search**: Structured filtering + semantic similarity + keyword matching
- **📖 Citation-First**: Every answer includes Case Title, Case Number, Page, Paragraph
- **🤖 Extractive AI**: Answers grounded in judgment text, no interpretation or legal advice
- **⚖️ Bangladesh Courts**: Appellate Division and High Court Division judgments
- **📄 Bulk Ingestion**: Process thousands of PDFs with OCR support for scanned documents
- **💬 Conversational**: Natural language queries with follow-up question support

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PDF Folders   │────▶│ Ingestion Worker│────▶│  Text + OCR     │
│ (ad_judgments/  │     │                 │     │  Extraction     │
│  sc_judgments/) │     └─────────────────┘     └────────┬────────┘
└─────────────────┘                                      │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │◀────│ Judgment Parser │◀────│   Paragraphs    │
│   (Metadata)    │     │   (Metadata)    │     │  + Embeddings   │
└────────┬────────┘     └─────────────────┘     └────────┬────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Hybrid Search  │◀────│   ChromaDB      │◀────│  Sentence       │
│    Engine       │     │ (Vector Store)  │     │  Transformers   │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Extractive LLM │────▶│    FastAPI      │────▶│   React UI      │
│   (Ollama)      │     │    Backend      │     │   Frontend      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (for containerized deployment)
- **PostgreSQL 15+** (or use Docker)
- **Ollama** (for local LLM inference)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/BanglaJudex.git
cd BanglaJudex

# Start all services
docker-compose up -d

# Pull the Mistral model (first time only)
docker exec -it banglajudex-llm ollama pull mistral

# Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

### Option 2: Local Development

#### 1. Start PostgreSQL

```bash
# Using Docker
docker run -d --name postgres-banglajudex \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=banglajudex \
  -p 5433:5432 \
  postgres:15-alpine
```

#### 2. Start Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your settings

# Initialize database
python init_db.py

# Run server
python -m uvicorn app.main:app --reload --port 8000
```

#### 3. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

#### 4. Start Ollama (for LLM features)

```bash
# Install Ollama from https://ollama.com
ollama serve

# Pull Mistral model (in another terminal)
ollama pull mistral
```

---

## 📁 Project Structure

```
BanglaJudex/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── db/            # Database configuration
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   │   ├── embeddings.py   # Vector embeddings
│   │   │   ├── ingestion.py    # PDF processing
│   │   │   ├── llm.py          # LLM integration
│   │   │   ├── parsing.py      # Judgment parsing
│   │   │   └── retrieval.py    # Hybrid search
│   │   ├── config.py      # Configuration
│   │   └── main.py        # App entry point
│   ├── tests/             # Unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
├── ad_judgments/          # Appellate Division PDFs
├── sc_judgments/          # High Court Division PDFs
├── docker-compose.yml
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5433/banglajudex` |
| `AD_JUDGMENTS_PATH` | Path to Appellate Division PDFs | `./ad_judgments` |
| `SC_JUDGMENTS_PATH` | Path to High Court Division PDFs | `./sc_judgments` |
| `CHROMA_PERSIST_PATH` | ChromaDB storage path | `./chroma_data` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `LLM_MODEL` | LLM model name | `mistral` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `API_PORT` | Backend API port | `8000` |
| `FRONTEND_URL` | Frontend URL (for CORS) | `http://localhost:3000` |

---

## 📖 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | API info |
| `POST` | `/search` | Search judgments with filters |
| `POST` | `/query` | Conversational query with LLM |
| `GET` | `/cases` | List all cases |
| `GET` | `/cases/{id}` | Get case details |
| `GET` | `/paragraphs/{id}` | Get paragraph details |
| `GET` | `/filters` | Get available filter options |
| `POST` | `/ingest/start` | Start PDF ingestion |
| `GET` | `/ingest/status` | Get ingestion status |
| `GET` | `/ingest/logs` | Get ingestion logs |

### Search Request Example

```json
POST /search
{
  "query": "pre-emption rights under Section 96",
  "filters": {
    "court": "appellate_division",
    "year_from": 2015,
    "year_to": 2020,
    "statute": "State Acquisition and Tenancy Act",
    "section": "96"
  }
}
```

### Query Request Example

```json
POST /query
{
  "query": "What did the court hold regarding pre-emption after mutation?",
  "conversation_id": "uuid-optional",
  "filters": {
    "court": "appellate_division"
  }
}
```

---

## 🧪 Testing

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_parsing.py -v
```

---

## 📊 Database Schema

### Core Tables

- **cases**: Judgment metadata (case_title, case_number, court, date, outcome)
- **judges**: Judge names (many-to-many with cases)
- **statutes**: Statutes and sections cited (many-to-many with cases)
- **paragraphs**: Text chunks with page/paragraph numbers
- **ingestion_logs**: PDF processing status and errors

### Retrieval Strategy

1. **Structured Filtering**: Court, year, judge, case type, statute, outcome
2. **Vector Search**: Semantic similarity using sentence embeddings
3. **Keyword Matching**: BM25-style keyword overlap
4. **Hybrid Scoring**: 50% vector + 30% keyword + 20% statute match

---

## ⚠️ Important Constraints

### Legal Disclaimer

This system is for **legal research purposes only**. It does NOT:
- Provide legal advice
- Interpret laws beyond explicit text
- Make legal recommendations

### Extractive-Only Policy

All answers MUST:
- Be directly grounded in judgment text
- Include explicit citations (Case, Page, Paragraph)
- Refuse to answer if relevant text is not found

### Mandatory Refusal Response

When no relevant text is found:
> "No explicit finding on this issue was located in the uploaded judgments."

---

## 🛠️ Development

### Adding New Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run linting: `flake8 app/`
4. Run tests: `pytest`
5. Submit pull request

### Code Style

- **Python**: Black formatter, isort, flake8
- **JavaScript**: ESLint, Prettier

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## 📞 Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/yourusername/BanglaJudex/issues) page.

---

## 🙏 Acknowledgments

- Bangladesh Supreme Court for public judgment access
- Open-source LLM community
- FastAPI and React teams

---

**Built with ❤️ for the legal community of Bangladesh**
