"""
Pytest configuration and fixtures for BanglaJudex tests.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models import *


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_pdf_content() -> bytes:
    """Generate mock PDF content for testing."""
    # This is a minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test PDF) Tj ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
startxref
0
%%EOF"""


@pytest.fixture
def sample_judgment_text() -> str:
    """Sample judgment text for testing parsing."""
    return """
    IN THE SUPREME COURT OF BANGLADESH
    APPELLATE DIVISION
    
    CIVIL APPEAL NO. 123 OF 2020
    
    Present:
    Mr. Justice A. B. M. Khairul Haque, C.J.
    Mr. Justice Md. Abdul Wahhab Miah
    
    BETWEEN:
    Md. Abdul Karim                    ...Appellant
            -Versus-
    Bangladesh Government             ...Respondent
    
    JUDGMENT
    
    Date of judgment: 15th March, 2021
    
    This appeal arises out of a writ petition filed under Article 102
    of the Constitution of the People's Republic of Bangladesh.
    
    The appellant challenged the decision under Section 96 of the
    State Acquisition and Tenancy Act, 1950 regarding pre-emption rights.
    
    FACTS:
    The appellant purchased a property through a registered kabala deed
    dated 10th January, 2018.
    
    ISSUES:
    1. Whether the pre-emption application was filed within the statutory period?
    2. Whether the mutation of the property affects pre-emption rights?
    
    FINDINGS:
    After careful consideration of the evidence and arguments, we find that
    the pre-emption application was filed within time. The mutation does not
    affect the pre-emption rights as held in similar cases.
    
    DECISION:
    The appeal is ALLOWED. The judgment of the High Court Division is set aside.
    
    ORDER:
    The respondent is directed to complete the pre-emption process within 60 days.
    """


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    mock = MagicMock()
    mock.generate_embedding = MagicMock(return_value=[0.1] * 384)
    mock.search = MagicMock(return_value=[])
    return mock


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock = AsyncMock()
    mock.generate_answer = AsyncMock(return_value={
        "answer": "Test answer based on provided context.",
        "citations": []
    })
    mock.check_health = AsyncMock(return_value=True)
    return mock
