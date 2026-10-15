import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

from database.connection import init_db
from handlers import user_handler, test_handler, essay_handler, admin_handler

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN topilmadi! .env faylini tekshiring.")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout
    )
    
    # Ma'lumotlar bazasini yaratish
    await init_db()
    logging.info("Ma'lumotlar bazasi muvaffaqiyatli ulandi va jadvallar yaratildi.")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Routerni ulash
    dp.include_router(user_handler.router)
    dp.include_router(test_handler.router)
    dp.include_router(essay_handler.router)
    dp.include_router(admin_handler.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot ishga tushdi va polling boshlandi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")