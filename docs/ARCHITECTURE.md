# BanglaJudex Architecture

## System Overview

BanglaJudex is an extractive conversational legal research system designed for Bangladesh Supreme Court judgments. The system prioritizes accurate citations over interpretation.

## Core Components

### 1. PDF Ingestion Pipeline

```
PDF Files → Text Extraction → OCR (if needed) → Parsing → Embeddings → Storage
```

**Components:**
- **PDF Scanner**: Discovers PDF files in judgment directories
- **Text Extractor**: Uses PyMuPDF for text extraction
- **OCR Engine**: Tesseract for scanned documents
- **Judgment Parser**: Extracts metadata (case number, date, judges, statutes)
- **Paragraph Splitter**: Splits text into paragraph-level chunks
- **Embedding Generator**: Sentence Transformers (all-MiniLM-L6-v2)
- **Storage**: PostgreSQL (metadata) + ChromaDB (vectors)

### 2. Hybrid Retrieval Engine

```
Query → [Structured Filter + Vector Search + Keyword Match] → Ranked Results
```

**Scoring Formula:**
```
final_score = 0.5 * vector_similarity + 0.3 * keyword_match + 0.2 * statute_match
```

**Section Priority Weights:**
- Findings: 1.20x
- Decision: 1.15x
- Issues: 1.10x
- Facts: 1.00x

### 3. Extractive LLM

```
Context Paragraphs → Ollama (Mistral) → Extractive Answer with Citations
```

**Key Constraints:**
- No interpretation or legal advice
- Mandatory citations (Case, Page, Paragraph)
- Refusal when relevant text not found
- Grounded only in provided context

## Data Model

```
┌──────────────────┐       ┌──────────────────┐
│      Cases       │───────│     Judges       │
├──────────────────┤       ├──────────────────┤
│ id (UUID)        │       │ id (UUID)        │
│ case_title       │       │ name             │
│ case_number      │       └──────────────────┘
│ court            │
│ date             │       ┌──────────────────┐
│ case_type        │───────│    Statutes      │
│ outcome          │       ├──────────────────┤
│ source_file      │       │ id (UUID)        │
│ page_count       │       │ name             │
│ file_hash        │       │ sections[]       │
└────────┬─────────┘       └──────────────────┘
         │
         │ 1:N
         ▼
┌──────────────────┐
│   Paragraphs     │
├──────────────────┤
│ id (UUID)        │
│ case_id (FK)     │
│ text             │
│ page_no          │
│ para_no          │
│ section          │
│ embedding_id     │
└──────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React + Vite | User interface |
| API | FastAPI | REST endpoints |
| Database | PostgreSQL 15 | Metadata storage |
| Vector Store | ChromaDB | Semantic search |
| Embeddings | Sentence Transformers | Text embeddings |
| LLM | Ollama + Mistral | Answer generation |
| PDF Processing | PyMuPDF + Tesseract | Text extraction |

## API Design

### Endpoints Structure

```
/                 # API info
/health           # Health check
/search           # Hybrid search
/query            # LLM-powered Q&A
/cases            # Case listing
/cases/{id}       # Case details
/paragraphs/{id}  # Paragraph details
/filters          # Filter options
/ingest/start     # Start ingestion
/ingest/status    # Ingestion status
/ingest/logs      # Processing logs
```

## Security Considerations

1. **Input Validation**: Pydantic models for all requests
2. **SQL Injection**: SQLAlchemy ORM with parameterized queries
3. **CORS**: Configurable allowed origins
4. **Rate Limiting**: Planned for production

## Scalability

### Horizontal Scaling
- Stateless API design
- Database connection pooling
- Background task queue for ingestion

### Performance Optimizations
- Paragraph-level indexing (vs. document-level)
- Hybrid search caching
- Batch embedding generation

## Deployment Architecture

### Development
```
Local Machine
├── PostgreSQL (Docker)
├── Backend (uvicorn)
├── Frontend (vite dev)
└── Ollama (local)
```

### Production (Docker Compose)
```
Docker Network
├── postgres (container)
├── backend (container)
├── frontend (nginx container)
└── ollama (container + GPU)
```

### Production (Kubernetes)
```
K8s Cluster
├── postgres (StatefulSet)
├── backend (Deployment + HPA)
├── frontend (Deployment)
├── ollama (Deployment + GPU nodes)
├── ingress (nginx)
└── persistent volumes
```

## Future Enhancements

1. **Multi-language Support**: Bengali text in judgments
2. **Advanced Analytics**: Judgment trends, citation networks
3. **Real-time Updates**: WebSocket for ingestion progress
4. **API Authentication**: JWT-based auth
5. **Batch Processing**: Kubernetes Jobs for large ingestions
