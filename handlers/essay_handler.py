import html
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select

from database.connection import async_session
from database.models import User, UserEssayTopic
from keyboards.builders import get_essay_menu_keyboard
from utils.essay_evaluator import evaluate_essay_with_ai
from utils.essay_topics import get_random_essay_topics

router = Router()


class EssayState(StatesGroup):
    waiting_for_essay_text = State()
    selecting_from_history = State()


def _format_bullet_list(items: list) -> str:
    if not items:
        return ""
    lines = []
    for item in items:
        clean_item = html.escape(str(item).strip(), quote=False)
        if clean_item:
            lines.append(f"• {clean_item}")
    return "\n".join(lines)


@router.message(F.text == "✍️ Esse AI")
async def cmd_essay_ai(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>🏛 UzBMB Milliy Sertifikat Esse AI Evaluator</b>\n\n"
        "Ushbu bo'limda siz UzBMB ona tili va adabiyot standarti asosidagi "
        "esse topshiriqlarini tanlab, inshongizni sun'iy intellekt orqali 24 ballik rasmiy "
        "mezonlar bo'yicha tekshirtirishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_essay_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "essay_back_menu")
async def back_to_essay_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "<b>🏛 UzBMB Milliy Sertifikat Esse AI Evaluator</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_essay_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "essay_new_menu")
async def select_essay_type_menu(callback: CallbackQuery, state: FSMContext):
    await _show_random_essay_topics(callback, state)


@router.callback_query(F.data == "essay_my_topics")
async def show_my_essay_topics(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.tg_id == callback.message.chat.id))
        user_obj = user_res.scalars().first()

        if not user_obj:
            await callback.answer("Foydalanuvchi topilmadi. Avval /start bosing.", show_alert=True)
            return

        topics_res = await session.execute(
            select(UserEssayTopic).where(UserEssayTopic.user_id == user_obj.id).order_by(UserEssayTopic.id.desc())
        )
        my_topics = topics_res.scalars().all()

    if not my_topics:
        await callback.answer("Sizda hali saqlangan mavzular yo'q. Avval yangi esse yozing!", show_alert=True)
        return

    await state.set_state(EssayState.selecting_from_history)
    history_dict = {str(i + 1): t.topic_text for i, t in enumerate(my_topics[:10])}
    await state.update_data(history_topics=history_dict)

    text = "📚 <b>Siz foydalangan esse mavzulari tarixingiz (oxirgi 10 tasi):</b>\n\n"
    kb = []
    for idx, t in enumerate(my_topics[:10], 1):
        preview = t.topic_text.splitlines()[0] if t.topic_text else f"Mavzu #{idx}"
        text += f"<b>{idx}.</b> {html.escape(preview, quote=False)}\n\n"
        kb.append([InlineKeyboardButton(text=f"📝 #{idx} mavzuni tanlash", callback_data=f"hist_top_{idx}")])

    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="essay_back_menu")])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()


@router.callback_query(EssayState.selecting_from_history, F.data.startswith("hist_top_"))
async def handle_history_topic_selection(callback: CallbackQuery, state: FSMContext):
    idx_str = callback.data.split("_")[2]
    data = await state.get_data()
    history_topics = data.get("history_topics", {})
    selected_topic = history_topics.get(idx_str)

    if not selected_topic:
        await callback.answer("Mavzu topilmadi.", show_alert=True)
        return

    await state.update_data(selected_topic=selected_topic, essay_type="situational")
    await state.set_state(EssayState.waiting_for_essay_text)

    await callback.message.answer(
        f"📌 <b>Tanlangan mavzu:</b>\n\n<i>{html.escape(selected_topic, quote=False)}</i>\n\n"
        f"✍️ Ushbu mavzu bo'yicha yozgan insho matningizni xabar sifatida yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.in_(["essay_opinion", "essay_both", "essay_solution"]))
async def handle_legacy_essay_type_selection(callback: CallbackQuery, state: FSMContext):
    await _show_random_essay_topics(callback, state)


async def _show_random_essay_topics(callback: CallbackQuery, state: FSMContext) -> None:
    topics = get_random_essay_topics()
    await state.update_data(essay_type="situational", topics=topics)
    await state.set_state(EssayState.waiting_for_essay_text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📝 {index}-topshiriqni tanlash", callback_data=f"select_topic_{index - 1}")]
        for index in range(1, len(topics) + 1)
    ] + [
        [InlineKeyboardButton(text="🔄 Boshqa 2 ta tasodifiy topshiriq", callback_data="essay_new_menu")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="essay_back_menu")]
    ])

    text = "🏛 <b>Ona tili va adabiyot — tasodifiy esse topshiriqlari</b>\n\n"
    for index, topic in enumerate(topics, 1):
        text += f"<b>{index}-topshiriq:</b>\n{html.escape(topic, quote=False)}\n\n"
    text += "Yozish uchun yuqoridagi topshiriqlardan birini tanlang:"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(EssayState.waiting_for_essay_text, F.data.startswith("select_topic_"))
async def handle_topic_choice(callback: CallbackQuery, state: FSMContext):
    try:
        topic_idx = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
        return

    data = await state.get_data()
    topics = data.get("topics", [])
    essay_type = data.get("essay_type", "situational")

    if topic_idx >= len(topics):
        await callback.answer("Mavzu topilmadi.", show_alert=True)
        return

    selected_topic = topics[topic_idx]
    await state.update_data(selected_topic=selected_topic)

    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.tg_id == callback.message.chat.id))
        user_obj = user_res.scalars().first()
        if user_obj:
            existing = await session.execute(
                select(UserEssayTopic).where(
                    (UserEssayTopic.user_id == user_obj.id) &
                    (UserEssayTopic.topic_text == selected_topic)
                )
            )
            if not existing.scalars().first():
                new_topic_entry = UserEssayTopic(
                    user_id=user_obj.id,
                    topic_text=selected_topic,
                    essay_type=essay_type
                )
                session.add(new_topic_entry)
                await session.commit()

    await callback.message.answer(
        f"📌 <b>Tanlangan topshiriq:</b>\n\n<i>{html.escape(selected_topic, quote=False)}</i>\n\n"
        f"✍️ <b>Endi ushbu topshiriq bo'yicha tayyorlagan insho matningizni bitta xabar sifatida yuboring.</b>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EssayState.waiting_for_essay_text)
async def process_essay_submission(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Iltimos, insho matnini matnli xabar ko'rinishida yuboring.")
        return

    if message.text.startswith("/"):
        return

    essay_text = message.text.strip()
    data = await state.get_data()
    selected_topic = data.get("selected_topic", "UzBMB Esse Topshirig'i")
    essay_type = data.get("essay_type", "situational")

    loading_msg = await message.answer(
        "🧠 <b>Insho matni AI-Ekspert tomonidan mezonlar asosida tekshirilmoqda...</b>\n"
        "<i>Bu jarayon bir necha soniya vaqt olishi mumkin.</i>",
        parse_mode="HTML"
    )

    res = await evaluate_essay_with_ai(selected_topic, essay_text, essay_type)

    try:
        await loading_msg.delete()
    except Exception:
        pass

    if res.get("evaluation_error"):
        await message.answer(
            res.get("feedback", "⚠️ AI xizmatida vaqtinchalik xatolik yuz berdi. Qayta urinib ko'ring."),
            parse_mode="HTML",
            reply_markup=get_essay_menu_keyboard()
        )
        return

    if not res.get("is_valid", False):
        await message.answer(
            f"❌ <b>INSHO TALABGA JAVOB BERMADI!</b>\n\n"
            f"{html.escape(res.get('feedback', 'Matn talablarga javob bermaydi.'), quote=False)}",
            parse_mode="HTML",
            reply_markup=get_essay_menu_keyboard()
        )
        await state.clear()
        return

    criteria = res.get("criteria", {})
    task_ach = criteria.get("task_achievement", "-")
    coherence = criteria.get("coherence", "-")
    vocab = criteria.get("vocabulary", "-")
    grammar = criteria.get("grammar", "-")

    report_parts = [
        "🏛 <b>UzBMB ESSE AI EKSPERT TAHLILI</b>\n",
        f"📌 <b>Topshiriq:</b> <i>{html.escape(selected_topic.splitlines()[0], quote=False)}</i>",
        f"📏 <b>Ko'rsatkichlar:</b> {res.get('word_count', 0)} so'z | {res.get('sentence_count', 0)} gap | {res.get('paragraph_count', 1)} abzas",
        f"📊 <b>Jami ball:</b> <code>{res.get('score_total', 0)} / 24.0 ball</code> ({res.get('percentage', 0)}%)",
        f"🎓 <b>Daraja:</b> <b>{res.get('level', 'C')}</b>\n",
        "📈 <b>Mezonlar bo'yicha baholar (max 6 ball):</b>",
        f"▫️ Mazmun va topshiriq: <b>{task_ach}</b>",
        f"▫️ Mantiqiy izchillik: <b>{coherence}</b>",
        f"▫️ Leksik boylik: <b>{vocab}</b>",
        f"▫️ Grammatika va imlo: <b>{grammar}</b>"
    ]

    strong_points = res.get("strong_points", [])
    if strong_points:
        strong_formatted = _format_bullet_list(strong_points)
        if strong_formatted:
            report_parts.append(f"\n🌟 <b>Kuchli jihatlari:</b>\n{strong_formatted}")

    weak_points = res.get("weak_points", [])
    if weak_points:
        weak_formatted = _format_bullet_list(weak_points)
        if weak_formatted:
            report_parts.append(f"\n⚠️ <b>Aniqlangan xato va kamchiliklar:</b>\n{weak_formatted}")

    recommendations = res.get("recommendations", [])
    if recommendations:
        rec_formatted = _format_bullet_list(recommendations)
        if rec_formatted:
            report_parts.append(f"\n💡 <b>Tavsiyalar:</b>\n{rec_formatted}")

    feedback = res.get("feedback")
    if feedback:
        report_parts.append(f"\n📝 <b>Xulosa:</b> <i>{html.escape(str(feedback), quote=False)}</i>")

    full_report = "\n".join(report_parts)

    # Telegram xabar uzunligi chegarasi (4096 belgi)
    if len(full_report) <= 4000:
        await message.answer(full_report, parse_mode="HTML", reply_markup=get_essay_menu_keyboard())
    else:
        # Uzun bo'lsa qismlarga bo'lib yuborish
        part1 = "\n".join(report_parts[:7])
        part2 = "\n".join(report_parts[7:])
        await message.answer(part1, parse_mode="HTML")
        await message.answer(part2, parse_mode="HTML", reply_markup=get_essay_menu_keyboard())

    await state.clear()