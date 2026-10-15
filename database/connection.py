import os
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from database.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:12345@localhost:5432/milliy_bot_db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "postgresql":
            # 1. users.tg_id ni BIGINT qilish
            tg_id_type = await conn.scalar(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_schema = current_schema() "
                    "AND table_name = 'users' AND column_name = 'tg_id'"
                )
            )
            if tg_id_type == "integer":
                await conn.execute(
                    text("ALTER TABLE users ALTER COLUMN tg_id TYPE BIGINT")
                )
                logging.info("Migrated users.tg_id from INTEGER to BIGINT.")

            # 2. test_results jadvaliga yangi ustunlar qo'shish va eskirgan not-null cheklovlarni yumshatish
            await conn.execute(text("ALTER TABLE test_results ADD COLUMN IF NOT EXISTS answered_count INTEGER DEFAULT 45"))
            await conn.execute(text("ALTER TABLE test_results ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT TRUE"))
            await conn.execute(text("ALTER TABLE test_results ALTER COLUMN raw_score DROP NOT NULL"))
            await conn.execute(text("ALTER TABLE test_results ALTER COLUMN t_score DROP NOT NULL"))
            await conn.execute(text("ALTER TABLE test_results ALTER COLUMN level DROP NOT NULL"))
            await conn.execute(text("ALTER TABLE test_results ALTER COLUMN time_spent_seconds DROP NOT NULL"))

            # 3. tests jadvalidagi explanation ni ixtiyoriy qilish
            await conn.execute(text("ALTER TABLE tests ALTER COLUMN explanation DROP NOT NULL"))

            # 4. user_errors jadvaliga user_answer qo'shish
            await conn.execute(text("ALTER TABLE user_errors ADD COLUMN IF NOT EXISTS user_answer VARCHAR(255)"))

            # 5. tests jadvaliga image_path qo'shish
            await conn.execute(text("ALTER TABLE tests ADD COLUMN IF NOT EXISTS image_path VARCHAR(500)"))