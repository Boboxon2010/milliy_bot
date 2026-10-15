import asyncio
import html
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from sqlalchemy.future import select
from sqlalchemy import func, delete

from database.connection import async_session
from database.models import User, TestResult, UserError, Test
from keyboards.builders import get_main_menu_keyboard
from utils.math_renderer import render_math_to_image

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    full_name = message.from_user.full_name

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()

        if not user:
            new_user = User(tg_id=tg_id, full_name=full_name)
            session.add(new_user)
            await session.commit()

    await message.answer(
        f"Assalomu alaykum, <b>{html.escape(full_name)}</b>!\n\n"
        f"🏛 <b>UzBMB Milliy Sertifikat Mock Test va AI Esse Evaluator</b> botiga xush kelibsiz.\n"
        f"Bu yerda siz barcha fanlardan mock testlar yechishingiz, insholaringizni AI orqali tekshirtirishingiz, "
        f"xatolaringiz ustida ishlashingiz va respublika reytingida o'z o'rningizni ko'rishingiz mumkin.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "👤 Profil")
async def cmd_profile(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == message.from_user.id)
        )
        user = result.scalars().first()

        if user is None:
            await message.answer(
                "❌ Profil ma'lumotlari topilmadi. Iltimos, /start buyrug'ini bosing.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        # Foydalanuvchining umumiy statistikasi
        tests_count = await session.scalar(
            select(func.count(TestResult.id)).where(TestResult.user_id == user.id)
        ) or 0
        best_score = await session.scalar(
            select(func.max(TestResult.score)).where(TestResult.user_id == user.id)
        ) or 0.0
        pending_errors = await session.scalar(
            select(func.count(UserError.id)).where(UserError.user_id == user.id)
        ) or 0

    registered_at = (
        user.created_at.strftime("%Y-%m-%d %H:%M")
        if user.created_at
        else "Noma'lum"
    )
    await message.answer(
        f"👤 <b>Foydalanuvchi Profili</b>\n\n"
        f"▫️ F.I.Sh: <b>{html.escape(user.full_name)}</b>\n"
        f"▫️ Telegram ID: <code>{user.tg_id}</code>\n"
        f"▫️ Yechilgan mock testlar: <b>{tests_count} ta</b>\n"
        f"▫️ Eng yuqori natija: <b>{best_score} ball</b>\n"
        f"▫️ O'rganilishi kerak bo'lgan xatolar: <b>{pending_errors} ta</b>\n"
        f"📅 Ro'yxatdan o'tgan sana: <code>{registered_at}</code>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text.in_({"ℹ️ Ma'lumot", "ℹ️ Bot haqida"}))
async def cmd_about(message: Message):
    await message.answer(
        "ℹ️ <b>UzBMB Milliy Sertifikat Boti haqida:</b>\n\n"
        "• Ushbu platforma Bilimni baholash agentligi (UzBMB) davlat standarti asosida ishlaydi.\n"
        "• <b>Mock Testlar:</b> Ona tili va adabiyot, Matematika, Fizika, Kimyo, Tarix, Ingliz tili.\n"
        "• <b>Real vaqt reytingi:</b> Har bir test yakunlangach darhol yangilanib boradi.\n"
        "• <b>To'liq va qisman natijalar:</b> Tugallangan va muddatidan oldin yakunlangan barcha testlar saqlanadi.\n"
        "• <b>Esse AI:</b> 24 ballik rasmiy mezonlar bo'yicha sun'iy intellekt tahlili.\n"
        "• <b>Xatolar ustida ishlash:</b> Har bir noto'g'ri javob qayd etilib, o'zlashtirish uchun saqlanadi.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "📊 Mening Natijalarim")
async def cmd_my_results(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user_res.scalars().first()

        if not user:
            await message.answer("Sizda hali natijalar mavjud emas. Avval test ishlang!")
            return

        res_query = await session.execute(
            select(TestResult).where(TestResult.user_id == user.id).order_by(TestResult.id.desc()).limit(10)
        )
        results = res_query.scalars().all()

    if not results:
        await message.answer(
            "📊 Siz hali birorta ham test ishlamagansiz.\n"
            "\"📝 Mock Test Yechish\" tugmasini bosib bilmingizni sinab ko'ring!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    text = "📊 <b>Sizning oxirgi test natijalaringiz:</b>\n\n"
    for idx, r in enumerate(results, 1):
        is_comp = getattr(r, "is_completed", True)
        ans_count = getattr(r, "answered_count", r.total_questions)
        
        status_label = "🟢 <b>To'liq yakunlangan</b>" if is_comp else f"🟡 <b>Chala/Tugatilgan ({ans_count}/{r.total_questions})</b>"

        sana = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "Noma'lum"
        text += (
            f"<b>{idx}. Fan: {r.subject}</b>\n"
            f"   Holat: {status_label}\n"
            f"   ✅ To'g'ri javoblar: {r.correct_count} / {ans_count} ta\n"
            f"   ⭐ To'plangan ball: <b>{r.score} ball</b>\n"
            f"   📅 Sana: <code>{sana}</code>\n"
            f"----------------------------------\n"
        )

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@router.message(F.text == "⚠️ Xatolar Ustida Ishlash")
async def cmd_user_errors(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user_res.scalars().first()

        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return

        err_query = await session.execute(
            select(UserError, Test)
            .join(Test, UserError.test_id == Test.id)
            .where(UserError.user_id == user.id)
            .order_by(UserError.id.desc())
        )
        errors = err_query.all()

    if not errors:
        await message.answer(
            "🎉 <b>Ajoyib! Sizda hozircha saqlangan xatolar yo'q.</b>\n\n"
            "Barcha testlarni muvaffaqiyatli topshirgansiz yoki barcha xatolarni o'rgangansiz.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"⚠️ <b>Xatolar ustida ishlash bo'limi</b>\n\n"
        f"Sizda jami <b>{len(errors)} ta</b> xato savol mavjud (quyida eng oxirgi 5 tasi ko'rsatilmoqda).\n"
        f"Har bir savolning to'g'ri javobi va tushuntirishini o'rganib, uni ro'yxatdan o'chirishingiz mumkin:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

    for idx, (err, test) in enumerate(errors[:5], 1):
        explanation = test.explanation or "Tushuntirish mavjud emas"
        user_ans = err.user_answer or "Noma'lum"

        caption = (
            f"📌 <b>{idx}-xato savol | Fan: {test.subject}</b>\n\n"
            f"❓ <b>Savol:</b> {html.escape(test.question_text[:300], quote=False)}\n\n"
            f"❌ <b>Siz belgilagan javob:</b> <code>{user_ans}</code>\n"
            f"✅ <b>Haqiqiy to'g'ri javob:</b> <code>{test.correct_answer}</code>\n\n"
            f"💡 <b>Tushuntirish:</b> <i>{html.escape(explanation, quote=False)}</i>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ O'zlashtirdim (Xatoni o'chirish)", callback_data=f"del_err_{err.id}")]
        ])

        try:
            photo = await asyncio.to_thread(render_math_to_image, test.question_text)
            await message.answer_photo(
                photo=photo,
                caption=caption[:1024],
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception:
            logging.exception("Failed to render error question image.")
            await message.answer(caption, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("del_err_"))
async def callback_delete_user_error(callback: CallbackQuery):
    err_id = int(callback.data.split("del_err_")[1])
    async with async_session() as session:
        await session.execute(delete(UserError).where(UserError.id == err_id))
        await session.commit()

    await callback.message.edit_caption(
        caption="🎉 <b>Barakalla! Ushbu savol o'zlashtirildi va xatolar ro'yxatidan o'chirildi.</b>",
        parse_mode="HTML"
    )
    await callback.answer("✅ Xato o'chirildi!")


@router.message(F.text == "🏆 Reyting")
async def cmd_leaderboard(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        # Barcha foydalanuvchilarning eng yuqori ballari bo'yicha to'liq reyting
        lb_query = await session.execute(
            select(User.id, User.full_name, func.max(TestResult.score).label("max_score"))
            .join(TestResult, User.id == TestResult.user_id)
            .group_by(User.id, User.full_name)
            .order_by(func.max(TestResult.score).desc())
        )
        all_leaders = lb_query.all()

        current_user = (await session.execute(select(User).where(User.tg_id == tg_id))).scalars().first()

    if not all_leaders:
        await message.answer(
            "🏆 <b>Hozircha reyting jadvalida natijalar mavjud emas.</b>\n"
            "Birinchi bo'lib mock test topshiring va 1-o'rinni egallang!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    # Foydalanuvchining o'z o'rni
    user_rank = None
    user_best_score = 0.0
    if current_user:
        for r_idx, (u_id, u_name, m_score) in enumerate(all_leaders, 1):
            if u_id == current_user.id:
                user_rank = r_idx
                user_best_score = m_score
                break

    text = "🏆 <b>UzBMB Milliy Sertifikat Respublika Reytingi</b>\n\n"
    for idx, (u_id, name, score) in enumerate(all_leaders[:10], 1):
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"<b>{idx}.</b>"))
        escaped_name = html.escape(name)
        text += f"{medal} <b>{escaped_name}</b> — <code>{score} ball</code>\n"

    text += "\n----------------------------------\n"
    if user_rank:
        text += f"👤 <b>Sizning natijangiz:</b> <b>#{user_rank}-o'rin</b> (Eng yuqori ball: <code>{user_best_score} ball</code>)\n"
    else:
        text += "👤 <i>Siz hali test ishlamagansiz. Mock test yechib reytingga kiring!</i>\n"

    text += "<i>💡 Reyting har bir test yakunlangandan so'ng avtomatik yangilanadi.</i>"

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())