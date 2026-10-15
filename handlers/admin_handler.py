import asyncio
import os
import time
import html
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func, select
from dotenv import load_dotenv

from database.connection import async_session
from database.models import User, Test, TestResult, UserEssayTopic
from utils.math_renderer import render_math_to_image
from utils.gemini_client import GEMINI_MODEL, MODELS_TO_TRY

load_dotenv()

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "boboxon")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "boboxon2010")
ADMIN_SESSION_DURATION = 100 * 60  # 100 daqiqa (soniyalarda)

# user_id -> expire_timestamp
admin_sessions: dict[int, float] = {}

router = Router()


def is_admin_session_valid(user_id: int) -> bool:
    """Admin sessiyasi mavjudligi va 100 daqiqalik muddati tugamaganligini tekshiradi."""
    if user_id not in admin_sessions:
        return False
    if time.time() > admin_sessions[user_id]:
        admin_sessions.pop(user_id, None)
        return False
    return True


def get_remaining_minutes(user_id: int) -> int:
    """Sessiya tugashiga necha daqiqa qolganini hisoblaydi."""
    if user_id not in admin_sessions:
        return 0
    remaining = int((admin_sessions[user_id] - time.time()) / 60)
    return max(0, remaining)


class AdminAuthState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()


class AdminState(StatesGroup):
    waiting_for_broadcast = State()


class AddTestState(StatesGroup):
    waiting_for_subject = State()
    waiting_for_custom_subject = State()
    waiting_for_type = State()
    waiting_for_difficulty = State()
    waiting_for_question_text = State()
    waiting_for_option_a = State()
    waiting_for_option_b = State()
    waiting_for_option_c = State()
    waiting_for_option_d = State()
    waiting_for_correct_option = State()
    waiting_for_open_answer = State()
    waiting_for_explanation = State()


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Mock Test Qo'shish", callback_data="admin_add_test")],
        [InlineKeyboardButton(text="⚙️ Bot Sozlamalari", callback_data="admin_settings")],
        [InlineKeyboardButton(text="📢 Xabar Tarqatish", callback_data="admin_action_broadcast")],
        [InlineKeyboardButton(text="📊 Batafsil Statistika", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton(text="🚪 Chiqish", callback_data="admin_action_logout")]
    ])


def get_subjects_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Ona tili va adabiyot", callback_data="adm_sub_Ona tili va adabiyot")],
        [InlineKeyboardButton(text="📐 Matematika", callback_data="adm_sub_Matematika")],
        [InlineKeyboardButton(text="⚛️ Fizika", callback_data="adm_sub_Fizika")],
        [InlineKeyboardButton(text="🧪 Kimyo", callback_data="adm_sub_Kimyo")],
        [InlineKeyboardButton(text="📜 Tarix", callback_data="adm_sub_Tarix")],
        [InlineKeyboardButton(text="🇬🇧 Ingliz tili", callback_data="adm_sub_Ingliz tili")],
        [InlineKeyboardButton(text="➕ Yangi fan kiritish", callback_data="adm_sub_custom")],
        [InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_back_dashboard")]
    ])


async def show_admin_dashboard(message: Message, user_id: int):
    rem_min = get_remaining_minutes(user_id)
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        tests_count = await session.scalar(select(func.count(Test.id)))
        results_count = await session.scalar(select(func.count(TestResult.id)))
        essays_count = await session.scalar(select(func.count(UserEssayTopic.id)))

    text = (
        f"👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"⏱ <i>Sessiya muddati: <b>{rem_min} daqiqa</b> faol.</i>\n\n"
        f"👥 Foydalanuvchilar: <b>{users_count or 0} ta</b>\n"
        f"📚 Jami mock testlar: <b>{tests_count or 0} ta</b>\n"
        f"📝 Yechilgan testlar: <b>{results_count or 0} ta</b>\n"
        f"✍️ Saqlangan esselar: <b>{essays_count or 0} ta</b>\n\n"
        f"Kerakli bo'limni tanlang:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_panel_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel_admin(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Amaliyot bekor qilindi.")


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    # Foydalanuvchi talabi: har bir /admin buyrug'idan keyin login va parol so'ralsin, avtomatik kirmasin!
    admin_sessions.pop(message.from_user.id, None)
    await state.clear()
    await state.set_state(AdminAuthState.waiting_for_login)
    await message.answer(
        "🔐 <b>Admin paneliga kirish</b>\n\n"
        "Iltimos, administrator <b>login</b>ini kiriting:\n"
        "<i>(Bekor qilish uchun /cancel)</i>",
        parse_mode="HTML"
    )


@router.message(AdminAuthState.waiting_for_login)
async def process_admin_login(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, loginingizni matn ko'rinishida yuboring.")
        return

    input_login = message.text.strip()
    if input_login == ADMIN_LOGIN:
        await state.set_state(AdminAuthState.waiting_for_password)
        await message.answer(
            "🔑 <b>Login qabul qilindi!</b>\n\n"
            "Endi administrator <b>parol</b>ini kiriting:",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Login noto'g'ri!</b>\n"
            "Iltimos, qaytadan kiriting yoki bekor qilish uchun /cancel buyrug'ini bosing.",
            parse_mode="HTML"
        )


@router.message(AdminAuthState.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, parolingizni matn ko'rinishida yuboring.")
        return

    input_pass = message.text.strip()
    if input_pass == ADMIN_PASSWORD:
        user_id = message.from_user.id
        admin_sessions[user_id] = time.time() + ADMIN_SESSION_DURATION
        await state.clear()
        await message.answer(
            "✅ <b>Muvaffaqiyatli kirdingiz!</b>\n"
            "⏱ <i>Admin huquqi 100 daqiqa (yoki keyingi /admin buyrug'igacha) amal qiladi.</i>\n",
            parse_mode="HTML"
        )
        await show_admin_dashboard(message, user_id)
    else:
        await message.answer(
            "❌ <b>Parol noto'g'ri!</b>\n"
            "Iltimos, parolni qaytadan kiriting yoki bekor qilish uchun /cancel buyrug'ini bosing.",
            parse_mode="HTML"
        )


@router.message(Command("logout"))
async def cmd_logout(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in admin_sessions:
        admin_sessions.pop(user_id, None)
        await state.clear()
        await message.answer("🚪 Admin panelidan muvaffaqiyatli chiqdingiz.")
    else:
        await message.answer("Siz admin paneliga kirmagansiz.")


@router.callback_query(F.data == "admin_action_logout")
async def callback_admin_logout(callback: CallbackQuery, state: FSMContext):
    admin_sessions.pop(callback.from_user.id, None)
    await state.clear()
    await callback.message.edit_text("🚪 Admin panelidan muvaffaqiyatli chiqdingiz.")
    await callback.answer()


@router.callback_query(F.data == "admin_back_dashboard")
async def callback_back_dashboard(callback: CallbackQuery, state: FSMContext):
    if not is_admin_session_valid(callback.from_user.id):
        await callback.answer("⚠️ Admin sessiyangiz muddati tugagan. Qaytadan kiring: /admin", show_alert=True)
        return
    await state.clear()
    await show_admin_dashboard(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "admin_settings")
async def callback_admin_settings(callback: CallbackQuery):
    if not is_admin_session_valid(callback.from_user.id):
        await callback.answer("⚠️ Admin sessiyangiz muddati tugagan. Qaytadan kiring: /admin", show_alert=True)
        return

    rem_min = get_remaining_minutes(callback.from_user.id)
    async with async_session() as session:
        subjects_query = await session.execute(
            select(Test.subject, func.count(Test.id)).group_by(Test.subject)
        )
        subjects_data = subjects_query.all()

    subj_text = ""
    for s_name, count in subjects_data:
        subj_text += f"  • {s_name}: <b>{count} ta test</b>\n"
    if not subj_text:
        subj_text = "  • <i>Hozircha testlar mavjud emas</i>\n"

    settings_text = (
        "⚙️ <b>Bot Tizim Sozlamalari</b>\n\n"
        f"🤖 <b>AI Modeli:</b> <code>{GEMINI_MODEL}</code>\n"
        f"🛡 <b>Zaxira (Fallback) modellar:</b> <code>{', '.join(MODELS_TO_TRY[:3])}</code>\n"
        "🗄 <b>Ma'lumotlar bazasi:</b> <code>PostgreSQL (Faol va ulangan)</code>\n"
        f"⏱ <b>Admin sessiyasi:</b> <code>{rem_min} daqiqa qoldi</code> (maks. 100 daqiqa)\n"
        f"🔐 <b>Admin Login:</b> <code>{ADMIN_LOGIN}</code>\n\n"
        "📚 <b>Fanlar bo'yicha savollar banki:</b>\n"
        f"{subj_text}\n"
        "<i>Har bir fanga mock test qo'shish uchun 'Mock Test Qo'shish' tugmasidan foydalaning.</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Mock Test Qo'shish", callback_data="admin_add_test")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back_dashboard")]
    ])
    await callback.message.edit_text(settings_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_detailed_stats")
async def callback_detailed_stats(callback: CallbackQuery):
    if not is_admin_session_valid(callback.from_user.id):
        await callback.answer("⚠️ Admin sessiyangiz muddati tugagan. Qaytadan kiring: /admin", show_alert=True)
        return

    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        tests_count = await session.scalar(select(func.count(Test.id)))
        completed_results = await session.scalar(
            select(func.count(TestResult.id)).where(TestResult.is_completed == True)
        )
        partial_results = await session.scalar(
            select(func.count(TestResult.id)).where(TestResult.is_completed == False)
        )
        avg_score = await session.scalar(select(func.avg(TestResult.score))) or 0.0
        essays_count = await session.scalar(select(func.count(UserEssayTopic.id)))

    stats_text = (
        "📊 <b>Batafsil Tizim Statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar soni: <b>{users_count or 0} ta</b>\n"
        f"📚 Jami mavjud savollar: <b>{tests_count or 0} ta</b>\n"
        f"🟢 To'liq yakunlangan testlar: <b>{completed_results or 0} ta</b>\n"
        f"🟡 Muddatidan oldin to'xtatilgan testlar: <b>{partial_results or 0} ta</b>\n"
        f"⭐ O'rtacha to'plangan ball: <b>{round(avg_score, 1)} ball</b>\n"
        f"✍️ AI tekshirgan esselar: <b>{essays_count or 0} ta</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back_dashboard")]
    ])
    await callback.message.edit_text(stats_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ==================== MOCK TEST QO'SHISH TIZIMI ====================

@router.callback_query(F.data == "admin_add_test")
async def start_add_test(callback: CallbackQuery, state: FSMContext):
    if not is_admin_session_valid(callback.from_user.id):
        await callback.answer("⚠️ Admin sessiyangiz muddati tugagan. Qaytadan kiring: /admin", show_alert=True)
        return

    await state.set_state(AddTestState.waiting_for_subject)
    text = (
        "➕ <b>Mock Test Qo'shish</b>\n\n"
        "Qaysi fanga yangi savol qo'shmoqchisiz? Quyidagi fanlardan birini tanlang yoki yangisini kiriting:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_subjects_selection_keyboard())
    await callback.answer()


@router.callback_query(AddTestState.waiting_for_subject, F.data.startswith("adm_sub_"))
async def process_subject_choice(callback: CallbackQuery, state: FSMContext):
    subj_code = callback.data.split("adm_sub_")[1]
    if subj_code == "custom":
        await state.set_state(AddTestState.waiting_for_custom_subject)
        await callback.message.edit_text(
            "✍️ Iltimos, yangi fan nomini kiriting:\n<i>(Masalan: Geografiya, Biologiya)</i>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await state.update_data(subject=subj_code)
    await _ask_test_type(callback.message, state, subj_code)
    await callback.answer()


@router.message(AddTestState.waiting_for_custom_subject)
async def process_custom_subject_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, fan nomini matn ko'rinishida yuboring.")
        return
    subj_name = message.text.strip()
    await state.update_data(subject=subj_name)
    await _ask_test_type(message, state, subj_name)


async def _ask_test_type(message: Message, state: FSMContext, subject_name: str):
    await state.set_state(AddTestState.waiting_for_type)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔘 Yopiq test (A, B, C, D)", callback_data="testtype_single"),
            InlineKeyboardButton(text="✍️ Ochiq test (Yozma)", callback_data="testtype_text")
        ],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_back_dashboard")]
    ])
    text = (
        f"📖 Fan: <b>{subject_name}</b>\n\n"
        "Savol turini tanlang:\n"
        "• <b>Yopiq test:</b> 4 ta variantli (A, B, C, D)\n"
        "• <b>Ochiq test:</b> Foydalanuvchi javobni matn/raqam sifatida yozadi"
    )
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(AddTestState.waiting_for_type, F.data.startswith("testtype_"))
async def process_type_choice(callback: CallbackQuery, state: FSMContext):
    q_type = callback.data.split("testtype_")[1]
    await state.update_data(question_type=q_type)

    await state.set_state(AddTestState.waiting_for_difficulty)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 1-daraja (1.3 ball)", callback_data="testdiff_1")],
        [InlineKeyboardButton(text="🟡 2-daraja (2.2 ball)", callback_data="testdiff_2")],
        [InlineKeyboardButton(text="🔴 3-daraja (3.4 ball)", callback_data="testdiff_3")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_back_dashboard")]
    ])
    await callback.message.edit_text(
        "📊 Savolning qiyinlik darajasini tanlang (UzBMB ball tizimi):",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AddTestState.waiting_for_difficulty, F.data.startswith("testdiff_"))
async def process_difficulty_choice(callback: CallbackQuery, state: FSMContext):
    diff = int(callback.data.split("testdiff_")[1])
    await state.update_data(difficulty=diff)

    await state.set_state(AddTestState.waiting_for_question_text)
    await callback.message.edit_text(
        "❓ <b>Savol matnini yuboring:</b>\n\n"
        "<i>Matematik ifodalar yoki formulalar bo'lsa, x^2, sqrt(x), log_2(x) yoki $...$ ko'rinishida yozishingiz mumkin. "
        "Bot uni avtomatik tarzda professional rasmga aylantiradi.</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddTestState.waiting_for_question_text)
async def process_question_text(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, savol matnini yuboring.")
        return

    q_text = message.text.strip()
    await state.update_data(question_text=q_text)

    data = await state.get_data()
    if data.get("question_type") == "single":
        await state.set_state(AddTestState.waiting_for_option_a)
        await message.answer("🅰️ <b>A variant</b> matnini kiriting:", parse_mode="HTML")
    else:
        await state.set_state(AddTestState.waiting_for_open_answer)
        await message.answer(
            "🎯 <b>To'g'ri javobni kiriting:</b>\n"
            "<i>(Masalan: 25 yoki 'Alisher Navoiy' yoki -4)</i>",
            parse_mode="HTML"
        )


@router.message(AddTestState.waiting_for_option_a)
async def process_option_a(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, variant matnini kiriting.")
        return
    await state.update_data(option_a=message.text.strip())
    await state.set_state(AddTestState.waiting_for_option_b)
    await message.answer("🅱️ <b>B variant</b> matnini kiriting:", parse_mode="HTML")


@router.message(AddTestState.waiting_for_option_b)
async def process_option_b(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, variant matnini kiriting.")
        return
    await state.update_data(option_b=message.text.strip())
    await state.set_state(AddTestState.waiting_for_option_c)
    await message.answer("🅲 <b>C variant</b> matnini kiriting:", parse_mode="HTML")


@router.message(AddTestState.waiting_for_option_c)
async def process_option_c(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, variant matnini kiriting.")
        return
    await state.update_data(option_c=message.text.strip())
    await state.set_state(AddTestState.waiting_for_option_d)
    await message.answer("🅳 <b>D variant</b> matnini kiriting:", parse_mode="HTML")


@router.message(AddTestState.waiting_for_option_d)
async def process_option_d(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, variant matnini kiriting.")
        return
    await state.update_data(option_d=message.text.strip())

    await state.set_state(AddTestState.waiting_for_correct_option)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="A", callback_data="correct_a"),
            InlineKeyboardButton(text="B", callback_data="correct_b"),
            InlineKeyboardButton(text="C", callback_data="correct_c"),
            InlineKeyboardButton(text="D", callback_data="correct_d")
        ]
    ])
    await message.answer(
        "🎯 <b>Qaysi variant to'g'ri?</b> Quyidagilardan tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(AddTestState.waiting_for_correct_option, F.data.startswith("correct_"))
async def process_correct_option(callback: CallbackQuery, state: FSMContext):
    corr = callback.data.split("correct_")[1].upper()
    await state.update_data(correct_answer=corr)

    await state.set_state(AddTestState.waiting_for_explanation)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_explanation")]
    ])
    await callback.message.edit_text(
        f"✅ To'g'ri javob sifatida <b>{corr}</b> belgilandi.\n\n"
        "💡 Ushbu savol uchun <b>tushuntirish (yechim)</b> matnini kiriting yoki o'tkazib yuboring:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddTestState.waiting_for_open_answer)
async def process_open_correct_answer(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, to'g'ri javob matnini kiriting.")
        return
    corr = message.text.strip()
    await state.update_data(correct_answer=corr)

    await state.set_state(AddTestState.waiting_for_explanation)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_explanation")]
    ])
    await message.answer(
        f"✅ To'g'ri javob: <b>{corr}</b>.\n\n"
        "💡 Ushbu savol uchun <b>tushuntirish (yechim)</b> matnini kiriting yoki o'tkazib yuboring:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(AddTestState.waiting_for_explanation, F.data == "skip_explanation")
async def skip_explanation(callback: CallbackQuery, state: FSMContext):
    await state.update_data(explanation="")
    await callback.answer()
    await _save_test_and_render_image(callback.message, state, callback.from_user.id)


@router.message(AddTestState.waiting_for_explanation)
async def process_explanation(message: Message, state: FSMContext):
    exp = message.text.strip() if message.text else ""
    await state.update_data(explanation=exp)
    await _save_test_and_render_image(message, state, message.from_user.id)


async def _save_test_and_render_image(message: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    subject = data.get("subject", "Noma'lum")
    q_type = data.get("question_type", "single")
    difficulty = data.get("difficulty", 1)
    q_text = (data.get("question_text") or "").strip()
    opt_a = data.get("option_a")
    opt_b = data.get("option_b")
    opt_c = data.get("option_c")
    opt_d = data.get("option_d")
    correct_ans = (data.get("correct_answer") or "").strip()
    explanation = (data.get("explanation") or "").strip()

    # 1. Bazaga saqlash
    new_test = Test(
        subject=subject,
        question_text=q_text,
        question_type=q_type,
        difficulty=difficulty,
        option_a=opt_a,
        option_b=opt_b,
        option_c=opt_c,
        option_d=opt_d,
        correct_answer=correct_ans,
        explanation=explanation if explanation else None
    )

    async with async_session() as session:
        session.add(new_test)
        await session.commit()
        await session.refresh(new_test)

    # 2. Rasmda FAQAT masala matni yoki misolning matematik ko'rinishi aks etadi
    image_text = q_text

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana test qo'shish", callback_data="admin_add_test")],
        [InlineKeyboardButton(text="👑 Admin panelga qaytish", callback_data="admin_back_dashboard")]
    ])

    esc_subject = html.escape(subject, quote=False)
    esc_correct = html.escape(correct_ans, quote=False)
    esc_exp = html.escape(explanation, quote=False) if explanation else ""

    caption_lines = [
        "🎉 <b>YANGI TEST MUVAFFAQIYATLI SAQLANDI!</b>\n",
        f"🆔 <b>Test ID:</b> <code>#{new_test.id}</code>",
        f"📖 <b>Fan:</b> {esc_subject}",
        f"📊 <b>Turi:</b> {'🔘 Yopiq test' if q_type == 'single' else '✍️ Ochiq test'}",
        f"⭐ <b>Qiyinlik:</b> {difficulty}-daraja",
        f"🎯 <b>To'g'ri javob:</b> <code>{esc_correct}</code>"
    ]
    if q_type == "single":
        caption_lines.append(
            f"\n<b>Variantlar:</b>\n"
            f"A) {html.escape(str(opt_a or ''), quote=False)}\n"
            f"B) {html.escape(str(opt_b or ''), quote=False)}\n"
            f"C) {html.escape(str(opt_c or ''), quote=False)}\n"
            f"D) {html.escape(str(opt_d or ''), quote=False)}"
        )
    if esc_exp:
        caption_lines.append(f"\n💡 <b>Tushuntirish:</b> <i>{esc_exp}</i>")

    caption_lines.append("\n🖼 <i>Savol masalasi rasm ko'rinishida yaratildi (yuqorida).</i>")
    caption = "\n".join(caption_lines)

    try:
        photo = await asyncio.to_thread(render_math_to_image, image_text)
        await message.answer_photo(
            photo=photo,
            caption=caption[:1024],
            parse_mode="HTML",
            reply_markup=kb
        )
        if len(caption) > 1024:
            await message.answer(caption[1024:], parse_mode="HTML")
    except Exception as exc:
        logging.exception("Failed to send rendered preview photo: %s", exc)
        await message.answer(
            caption[:4000],
            parse_mode="HTML",
            reply_markup=kb
        )

    await state.clear()



# ==================== BROADCAST TIZIMI ====================

@router.callback_query(F.data == "admin_action_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin_session_valid(callback.from_user.id):
        await callback.answer("⚠️ Admin sessiyangiz muddati tugagan. Qaytadan kiring: /admin", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.message.answer(
        "📢 <b>Xabar tarqatish:</b>\n\n"
        "Barcha bot foydalanuvchilariga yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "<i>(Bekor qilish uchun /cancel)</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin_session_valid(message.from_user.id):
        await message.answer("⚠️ Admin huquqi talab qilinadi. Kirish uchun: /admin")
        return

    await state.set_state(AdminState.waiting_for_broadcast)
    await message.answer(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:\n"
        "<i>(Bekor qilish uchun /cancel)</i>",
        parse_mode="HTML"
    )


@router.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin_session_valid(message.from_user.id):
        await state.clear()
        return

    if not message.text:
        await message.answer("Iltimos, yubormoqchi bo'lgan matnli xabaringizni yuboring.")
        return

    async with async_session() as session:
        users = (await session.execute(select(User.tg_id))).scalars().all()

    sent_status = await message.answer(f"⏳ Xabar tarqatilmoqda (jami {len(users)} ta foydalanuvchi)...")

    success, failed = 0, 0
    for tg_id in users:
        try:
            await message.bot.send_message(tg_id, message.text, parse_mode="HTML")
            success += 1
        except Exception:
            try:
                await message.bot.send_message(tg_id, message.text)
                success += 1
            except Exception:
                failed += 1

    try:
        await sent_status.delete()
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📤 Muvaffaqiyatli: <b>{success} ta</b>\n"
        f"❌ Yuborilmadi: <b>{failed} ta</b>",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard()
    )
    await state.clear()