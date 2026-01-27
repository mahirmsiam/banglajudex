"""
Database initialization script.
Creates all tables if they don't exist.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.database import init_db, engine
from app.models import *  # Import all models to register them

async def main():
    print("Initializing database...")
    try:
        await init_db()
        print("[OK] Database tables created successfully!")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
