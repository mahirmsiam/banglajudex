# BanglaJudex API Reference

Complete API documentation for BanglaJudex backend services.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. Future versions may add API key authentication.

---

## Health & Status

### GET /

Get API information.

**Response:**
```json
{
  "name": "BanglaJudex API",
  "version": "1.0.0",
  "description": "Extractive Conversational Legal Research System"
}
```

### GET /health

Check system health.

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "vector_db": "healthy",
  "llm": "healthy",
  "timestamp": "2026-01-27T10:00:00Z"
}
```

---

## Search

### POST /search

Search for judgments using hybrid search.

**Request Body:**
```json
{
  "query": "pre-emption rights under Section 96",
  "filters": {
    "court": "appellate_division",
    "year_from": 2015,
    "year_to": 2020,
    "statute": "State Acquisition and Tenancy Act",
    "section": "96",
    "judge": "Justice Rahman",
    "case_type": "civil",
    "outcome": "allowed"
  },
  "limit": 10,
  "offset": 0
}
```

**Filter Options:**

| Field | Type | Description |
|-------|------|-------------|
| `court` | string | `appellate_division` or `high_court_division` |
| `year_from` | integer | Start year (inclusive) |
| `year_to` | integer | End year (inclusive) |
| `statute` | string | Statute name or partial match |
| `section` | string | Section number |
| `judge` | string | Judge name |
| `case_type` | string | `civil`, `criminal`, `writ` |
| `outcome` | string | `allowed`, `dismissed`, `partly_allowed` |

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "case_title": "Abdul Karim vs. Bangladesh",
      "case_number": "CA 123/2020",
      "court": "Appellate Division",
      "date": "2021-03-15",
      "paragraphs": [
        {
          "id": "uuid",
          "text": "The court held that...",
          "page_no": 5,
          "para_no": 12,
          "section": "findings",
          "score": 0.95
        }
      ],
      "score": 0.92
    }
  ],
  "total": 1,
  "query": "pre-emption rights under Section 96"
}
```

---

## Conversational Query

### POST /query

Ask a natural language question with LLM-generated answer.

**Request Body:**
```json
{
  "query": "What did the court hold regarding pre-emption after mutation?",
  "conversation_id": "uuid-optional",
  "filters": {
    "court": "appellate_division"
  }
}
```

**Response:**
```json
{
  "answer": "The court held that mutation of property does not affect the pre-emption rights as established in previous decisions. (Abdul Karim vs. Bangladesh, CA 123/2020, Page 6, Paragraph 15)",
  "citations": [
    {
      "case_title": "Abdul Karim vs. Bangladesh",
      "case_number": "CA 123/2020",
      "page_no": 6,
      "para_no": 15,
      "text": "Mutation of property does not affect the pre-emption rights..."
    }
  ],
  "sources": [
    {
      "id": "uuid",
      "case_title": "Abdul Karim vs. Bangladesh",
      "case_number": "CA 123/2020",
      "paragraphs_used": 2
    }
  ],
  "conversation_id": "uuid"
}
```

**Error Response (No Results):**
```json
{
  "answer": "No explicit finding on this issue was located in the uploaded judgments.",
  "citations": [],
  "sources": [],
  "conversation_id": "uuid"
}
```

---

## Cases

### GET /cases

List all ingested cases.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Number of results |
| `offset` | integer | 0 | Pagination offset |
| `court` | string | - | Filter by court |
| `year` | integer | - | Filter by year |

**Response:**
```json
{
  "cases": [
    {
      "id": "uuid",
      "case_title": "Abdul Karim vs. Bangladesh",
      "case_number": "CA 123/2020",
      "court": "Appellate Division",
      "date": "2021-03-15",
      "outcome": "Allowed",
      "paragraph_count": 45
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### GET /cases/{id}

Get detailed case information.

**Response:**
```json
{
  "id": "uuid",
  "case_title": "Abdul Karim vs. Bangladesh",
  "case_number": "CA 123/2020",
  "court": "Appellate Division",
  "date": "2021-03-15",
  "case_type": "Civil",
  "outcome": "Allowed",
  "source_file": "CA_123_2020.pdf",
  "page_count": 12,
  "judges": [
    {
      "id": "uuid",
      "name": "Justice A. B. M. Khairul Haque"
    }
  ],
  "statutes": [
    {
      "id": "uuid",
      "name": "State Acquisition and Tenancy Act, 1950",
      "sections": ["96", "97"]
    }
  ],
  "paragraphs": [
    {
      "id": "uuid",
      "text": "The appellant challenged...",
      "page_no": 1,
      "para_no": 1,
      "section": "facts"
    }
  ]
}
```

---

## Filters

### GET /filters

Get available filter options.

**Response:**
```json
{
  "courts": [
    {"value": "appellate_division", "label": "Appellate Division"},
    {"value": "high_court_division", "label": "High Court Division"}
  ],
  "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021],
  "statutes": [
    {"value": "penal_code", "label": "Penal Code, 1860"},
    {"value": "crpc", "label": "Code of Criminal Procedure, 1898"}
  ],
  "case_types": [
    {"value": "civil", "label": "Civil"},
    {"value": "criminal", "label": "Criminal"},
    {"value": "writ", "label": "Writ"}
  ],
  "outcomes": [
    {"value": "allowed", "label": "Allowed"},
    {"value": "dismissed", "label": "Dismissed"},
    {"value": "partly_allowed", "label": "Partly Allowed"}
  ]
}
```

---

## Ingestion

### POST /ingest/start

Start PDF ingestion process.

**Response:**
```json
{
  "message": "Ingestion started",
  "job_id": "uuid",
  "files_found": {
    "ad_judgments": 349,
    "sc_judgments": 1500
  }
}
```

### GET /ingest/status

Get current ingestion status.

**Response:**
```json
{
  "is_running": true,
  "job_id": "uuid",
  "started_at": "2026-01-27T10:00:00Z",
  "progress": {
    "total_files": 1849,
    "processed": 450,
    "successful": 445,
    "failed": 5,
    "percentage": 24.3
  },
  "current_file": "CA_500_2020.pdf"
}
```

### GET /ingest/logs

Get ingestion logs.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Number of logs |
| `status` | string | - | Filter: `success`, `failed`, `skipped` |

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "filename": "CA_123_2020.pdf",
      "status": "success",
      "processed_at": "2026-01-27T10:05:00Z",
      "pages": 12,
      "paragraphs": 45
    },
    {
      "id": "uuid",
      "filename": "corrupted.pdf",
      "status": "failed",
      "error": "PDF extraction failed: corrupted file",
      "processed_at": "2026-01-27T10:06:00Z"
    }
  ],
  "total": 450
}
```

---

## Error Responses

All endpoints may return error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request body"
}
```

### 404 Not Found
```json
{
  "detail": "Case not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database connection error"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. Future versions may add rate limiting for production deployments.

---

## WebSocket (Future)

Real-time updates for ingestion progress will be available via WebSocket at:

```
ws://localhost:8000/ws/ingest
```
