from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "postgresql+asyncpg://postgres:937393@localhost:5432/ride_api"

engine = create_async_engine(DATABASE_URL, echo=True)


SessionLocal = sessionmaker(
    autocommit=False,
    bind=engine,
    class_=AsyncSession
)


async def get_db():
    async with SessionLocal() as session:
        yield session

@asynccontextmanager
async def get_db_session(): 
    agen = get_db()
    try:
        session = await agen.__anext__()
        yield session
    finally:
        await agen.aclose()

if __name__ == "__main__":
    import asyncio

    async def test_connection():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully!")

    asyncio.run(test_connection())
