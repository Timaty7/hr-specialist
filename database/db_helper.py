"""
PostgreSQL (asyncpg) арқылы асинхронды сессияларды басқару утилиті.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models import Base
from config.settings import settings

# asyncpg драйверін қолдана отырып асинхронды қозғалтқыш құру
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def init_db():
    """PostgreSQL дерекқорында кестелерді автоматты түрде құру"""
    async with engine.begin() as conn:
        # Кестелер тек бұрын құрылмаған жағдайда ғана құрылады
        await conn.run_sync(Base.metadata.create_all)