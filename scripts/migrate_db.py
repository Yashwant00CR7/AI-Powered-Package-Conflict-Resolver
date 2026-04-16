
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///legacy_solver.db")

async def migrate():
    print(f"Starting migration on {DB_URL}...")
    engine = create_async_engine(DB_URL)
    
    async with engine.begin() as conn:
        print("Creating 'user_credentials' table if it doesn't exist...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                user_id VARCHAR(128) PRIMARY KEY,
                gemini_api_key TEXT,
                openrouter_api_key TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
    
    await engine.dispose()
    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
