import asyncio
import re
from pathlib import Path

from sqlalchemy import select

from database.connection import async_session, init_db
from database.models import Test
from utils.math_renderer import render_math_to_image


IMAGE_DIR = Path("static/questions")


def _subject_slug(subject: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", subject).strip("_")


def _image_path(test: Test) -> Path:
    filename = f"{_subject_slug(test.subject or 'Test')}_{test.id}.png"
    return IMAGE_DIR / filename


async def seed_question_images() -> None:
    await init_db()
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    created_count = 0
    linked_count = 0

    async with async_session() as session:
        tests = (
            await session.execute(select(Test).order_by(Test.id))
        ).scalars().all()

        for test in tests:
            image_path = _image_path(test)
            if not image_path.exists():
                image = await asyncio.to_thread(
                    render_math_to_image, test.question_text
                )
                image_path.write_bytes(image.data)
                created_count += 1

            relative_path = image_path.as_posix()
            if test.image_path != relative_path:
                test.image_path = relative_path
                linked_count += 1

        await session.commit()

    print(f"{created_count} ta yangi rasm yaratildi.")
    print(f"{linked_count} ta test rasmi bazaga bog'landi.")


if __name__ == "__main__":
    asyncio.run(seed_question_images())
