# BanglaJudex Unit Tests

This directory contains the test suite for BanglaJudex backend services.

## Test Structure

```
tests/
├── __init__.py           # Test package
├── conftest.py           # Shared fixtures and configuration
├── test_parsing.py       # Judgment parsing tests
├── test_retrieval.py     # Search and retrieval tests
├── test_llm.py           # LLM service tests
├── test_ingestion.py     # PDF ingestion tests
└── test_api.py           # API endpoint tests
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov aiosqlite
```

### Run All Tests

```bash
# From backend directory
cd backend
pytest
```

### Run Specific Test File

```bash
pytest tests/test_parsing.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_parsing.py::TestJudgmentParser -v
```

### Run Specific Test

```bash
pytest tests/test_parsing.py::TestJudgmentParser::test_extract_case_number_civil_appeal -v
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

## Test Categories

### Unit Tests
- `test_parsing.py`: Metadata extraction from judgment text
- `test_llm.py`: Answer generation and validation
- `test_ingestion.py`: PDF processing and batch operations

### Integration Tests
- `test_api.py`: API endpoints with mocked services
- `test_retrieval.py`: Hybrid search functionality

## Fixtures

Common fixtures are defined in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `test_engine` | In-memory SQLite database engine |
| `db_session` | Test database session |
| `mock_pdf_content` | Sample PDF bytes |
| `sample_judgment_text` | Sample judgment text for parsing |
| `mock_embedding_service` | Mocked embedding service |
| `mock_llm_service` | Mocked LLM service |

## Writing Tests

### Test Naming Convention
- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<behavior>`

### Async Tests
Use `@pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_call()
    assert result is not None
```

### Mocking
Use `unittest.mock` for mocking external services:

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    with patch('app.services.llm.ollama_client') as mock:
        mock.chat.return_value = {"message": {"content": "test"}}
        result = await llm_service.generate_answer(...)
```

## Continuous Integration

Tests are run automatically on:
- Pull request creation
- Push to main branch

GitHub Actions configuration in `.github/workflows/test.yml`.
