# BanglaJudex

**Extractive Conversational Legal Research System for Bangladesh Judgments**

A production-grade web application that enables users to query, filter, and conversationally interact with Bangladesh Supreme Court judgments.

## Features

- 🔍 **Hybrid Search**: Structured filtering + semantic similarity + keyword matching
- 📖 **Citation-First**: Every answer includes Case Title, Case Number, Page, Paragraph
- 🤖 **Extractive AI**: Answers grounded in judgment text, no interpretation
- ⚖️ **Bangladesh Courts**: Appellate Division and High Court Division judgments

## Quick Start

```bash
# Start all services
docker-compose up -d

# Trigger PDF ingestion
curl -X POST http://localhost:8000/api/ingest/start

# Access the web interface
open http://localhost:3000
```

## Architecture

```
PDF Folders → Ingestion Worker → OCR/Text Extraction → Judgment Parser
    → PostgreSQL (metadata) + ChromaDB (vectors) → Hybrid Retrieval
    → Extractive LLM → Web Interface
```

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL 15
- **Vector DB**: ChromaDB
- **LLM**: Ollama + Mistral 7B (local)
- **Frontend**: React + Vite
- **OCR**: Tesseract

## Project Structure

```
├── backend/           # FastAPI application
├── frontend/          # React application
├── ad_judgments/      # Appellate Division PDFs
├── sc_judgments/      # High Court Division PDFs
└── docker-compose.yml
```

## License

MIT
