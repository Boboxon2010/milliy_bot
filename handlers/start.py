from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.future import select

from database.connection import async_session
from database.models import User
from keyboards.builders import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    full_name = message.from_user.full_name

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()

        if not user:
            # Yangi foydalanuvchini bazaga qo'shamiz
            user = User(
                tg_id=tg_id,
                full_name=full_name
            )
            session.add(user)
            await session.commit()

    await message.answer(
        f"Assalomu alaykum, **{full_name}**! 👋\n\n"
        f"🎯 Bu bot sizga **Milliy Sertifikat** imtihonlariga tayyorlanishda va esselarni sun'iy intellekt orqali tekshirishda yordam beradi.\n\n"
        f"Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Profil")
async def profile_handler(message: Message):
    tg_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()

    if user:
        profile_text = (
            f"👤 **Foydalanuvchi Profili**\n\n"
            f"F.I.Sh: **{user.full_name}**\n"
            f"Telegram ID: `{user.tg_id}`\n"
            f"📅 Ro'yxatdan o'tgan vaqtingiz: `{user.created_at.strftime('%Y-%m-%d %H:%M')}`"
        )
    else:
        profile_text = "❌ Profil ma'lumotlari topilmadi. Iltimos, /start buyrug'ini bosing."

    await message.answer(profile_text, parse_mode="Markdown")

@router.message(F.text == "ℹ️ Ma'lumot")
async def info_handler(message: Message):
    info_text = (
        f"ℹ️ **Bot haqida ma'lumot**\n\n"
        f"Bu bot **UzBMB (Bilimni baholash agentligi)** talablari asosida Milliy Sertifikat imtihonlariga mustaqil tayyorlanish uchun maxsus ishlab chiqilgan.\n\n"
        f"🔹 **Mock Test:** Turli fanlardan imtihon formatidagi testlarni ishlang va xatolaringizni tahlil qiling.\n"
        f"🔹 **Esse AI:** Yozgan essengizni Google Gemini sun'iy intellektiga tekshirttirib, batafsil ball va maslahatlar oling.\n\n"
        f"Savol va takliflar bo'yicha Dasturchiga murojaat qilishingiz mumkin."
    )
    await message.answer(info_text, parse_mode="Markdown")