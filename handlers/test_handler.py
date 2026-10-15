import asyncio
import html
import logging
import random
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import func

from database.connection import async_session
from database.models import Test, TestResult, User, UserError
from keyboards.builders import get_subjects_keyboard, get_main_menu_keyboard
from utils.math_renderer import render_math_to_image

router = Router()


class TestState(StatesGroup):
    answering_tests = State()
    finishing = State()


def _is_mock_test_menu(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    if "mock" in normalized and "test" in normalized:
        return True
    return "test" in normalized and any(
        action in normalized for action in ("yechish", "ishlash", "boshlash")
    )


def _is_single_choice(test: Test) -> bool:
    if test.question_type == "single":
        return True
    return test.question_type is None and any(
        (test.option_a, test.option_b, test.option_c, test.option_d)
    )


async def _delete_callback_message(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        logging.warning("Could not delete the answered mock-test message.")


async def _record_immediate_error(tg_id: int, test_dict: dict, user_ans: str):
    """Har bir javobdan so'ng xato qilingan bo'lsa darhol UserError jadvaliga saqlaydi."""
    correct_ans = str(test_dict.get("correct_answer", "")).strip().lower()
    if user_ans.strip().lower() != correct_ans:
        try:
            async with async_session() as session:
                user_res = await session.execute(select(User).where(User.tg_id == tg_id))
                user_obj = user_res.scalars().first()
                if user_obj:
                    existing_err = await session.execute(
                        select(UserError).where(
                            (UserError.user_id == user_obj.id) &
                            (UserError.test_id == test_dict["id"])
                        )
                    )
                    err_entry = existing_err.scalars().first()
                    if not err_entry:
                        session.add(
                            UserError(user_id=user_obj.id, test_id=test_dict["id"], user_answer=user_ans)
                        )
                    else:
                        err_entry.user_answer = user_ans
                    await session.commit()
        except Exception:
            logging.exception("Failed to record UserError immediately.")


@router.message(F.text.func(_is_mock_test_menu))
async def cmd_mock_test(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>🎯 UzBMB Milliy Sertifikat Mock Test</b>\n\n"
        "Test ishlamoqchi bo'lgan fanni tanlang:",
        reply_markup=get_subjects_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("subj_"))
async def start_mock_test_by_subject(callback: CallbackQuery, state: FSMContext):
    subject_name = callback.data.split("_", 1)[1]
    subject_names = [subject_name]
    if subject_name == "Ona tili va adabiyot":
        subject_names.append("O'zbek tili")
    
    async with async_session() as session:
        tests_res = await session.execute(
            select(Test).where(Test.subject.in_(subject_names))
        )
        all_tests = tests_res.scalars().all()

    single_tests = [test for test in all_tests if _is_single_choice(test)]
    text_tests = [test for test in all_tests if not _is_single_choice(test)]

    if not all_tests:
        await callback.message.answer(
            f"⚠️ <b>{subject_name}</b> fani bo'yicha hozircha testlar topilmadi!\n"
            "Admin panel orqali yangi testlar qo'shishingiz mumkin.",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    if subject_name == "Ona tili va adabiyot":
        if len(single_tests) >= 30 and len(text_tests) >= 15:
            selected_singles = random.sample(single_tests, 30)
            selected_texts = random.sample(text_tests, 15)
            chosen_tests = selected_singles + selected_texts
        else:
            selected_singles = random.sample(single_tests, min(30, len(single_tests)))
            selected_texts = random.sample(text_tests, min(15, len(text_tests)))
            chosen_tests = selected_singles + selected_texts

            remaining_tests = [
                test for test in all_tests
                if test not in chosen_tests
            ]
            extra_count = min(45 - len(chosen_tests), len(remaining_tests))
            if extra_count:
                extra_tests = random.sample(remaining_tests, extra_count)
                chosen_tests.extend(extra_tests)
    else:
        chosen_tests = random.sample(all_tests, min(45, len(all_tests)))

    async with async_session() as session:
        user_res = await session.execute(select(User).where(User.tg_id == callback.message.chat.id))
        user_obj = user_res.scalars().first()
        if not user_obj:
            new_user = User(tg_id=callback.message.chat.id, full_name=callback.from_user.full_name)
            session.add(new_user)
            await session.commit()

    serialized_tests = []
    for t in chosen_tests:
        serialized_tests.append({
            "id": t.id,
            "question_text": t.question_text,
            "question_type": "single" if _is_single_choice(t) else "text",
            "difficulty": t.difficulty or 1,
            "option_a": t.option_a,
            "option_b": t.option_b,
            "option_c": t.option_c,
            "option_d": t.option_d,
            "correct_answer": t.correct_answer,
            "explanation": t.explanation
        })

    await state.set_state(TestState.answering_tests)
    await state.update_data(
        subject=subject_name,
        tests=serialized_tests,
        current_index=0,
        user_answers={}
    )

    closed_count = sum(
        test["question_type"] == "single" for test in serialized_tests
    )
    open_count = len(serialized_tests) - closed_count
    start_text = (
        f"📖 <b>{subject_name}</b> fanidan UzBMB milliy sertifikat mock testi boshlandi!\n"
        f"🔹 Jami savollar: <b>{len(serialized_tests)} ta</b> "
        f"({closed_count} ta yopiq + {open_count} ta ochiq).\n\n"
    )
    if subject_name == "Ona tili va adabiyot" and (
        closed_count != 30 or open_count != 15
    ):
        start_text += (
            "ℹ️ Savollar bazasidagi taqsimot 30/15 talabiga mos emas; "
            "test mavjud savollar bilan davom etadi.\n\n"
        )
    start_text += "Birinchi savol yuklanmoqda..."
    await callback.message.edit_text(start_text, parse_mode="HTML")
    await callback.answer()
    
    await send_test_question(callback.message, state)


async def send_test_question(message: Message, state: FSMContext):
    data = await state.get_data()
    tests = data.get("tests", [])
    idx = data.get("current_index", 0)

    if idx >= len(tests):
        await finish_exam(message, state)
        return

    test = tests[idx]
    q_type = test["question_type"]
    diff = test.get("difficulty") or 1
    
    score_label = "1.3 ball" if diff == 1 else ("2.2 ball" if diff == 2 else "3.4 ball")
    section_info = "Yopiq test" if q_type == "single" else "Ochiq test"
    question_text = str(test["question_text"])
    caption_lines = [
        f"{idx + 1}-savol / {len(tests)} | {section_info} | "
        f"{diff}-daraja | {score_label}",
        f"❓ {question_text}",
    ]
    image_lines = [
        caption_lines[0],
        f"Savol: {question_text}",
    ]

    kb = []
    if q_type == "single":
        options = [
            ("A", test["option_a"]),
            ("B", test["option_b"]),
            ("C", test["option_c"]),
            ("D", test["option_d"])
        ]
        for key, val in options:
            if val:
                caption_lines.append(f"{key}) {val}")
                image_lines.append(f"{key}) {val}")
                kb.append([
                    InlineKeyboardButton(
                        text=f"{key}) {val[:35]}",
                        callback_data=f"ans_{key.lower()}"
                    )
                ])
    else:
        writing_prompt = "✍️ Ochiq savol: javobingizni matn ko'rinishida yuboring."
        caption_lines.append(writing_prompt)
        image_lines.append(
            "Ochiq savol: javobingizni matn ko'rinishida yuboring."
        )

    kb.append([InlineKeyboardButton(text="🏁 Testni tugatish", callback_data="finish_exam_request")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    caption = "\n\n".join(caption_lines)
    try:
        photo = await asyncio.to_thread(render_math_to_image, question_text)
    except Exception:
        logging.exception("Failed to render mock-test question %s as an image.", idx + 1)
        await message.answer(
            html.escape(caption, quote=False),
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    caption_limit = 1024
    await message.answer_photo(
        photo=photo,
        caption=html.escape(caption[:caption_limit], quote=False),
        parse_mode="HTML",
        reply_markup=keyboard
    )
    if len(caption) > caption_limit:
        await message.answer(
            html.escape(caption[caption_limit:], quote=False),
            parse_mode="HTML"
        )


@router.callback_query(TestState.answering_tests, F.data.startswith("ans_"))
async def process_callback_answer(callback: CallbackQuery, state: FSMContext):
    user_ans = callback.data.rsplit("_", 1)[1].strip().lower()
    data = await state.get_data()
    
    idx = data.get("current_index", 0)
    tests = data.get("tests", [])
    if idx >= len(tests) or tests[idx]["question_type"] != "single":
        await callback.answer("Bu javob tugmasi endi faol emas.", show_alert=True)
        return

    current_test = tests[idx]
    # Har bir xato belgilangan javobdan keyin xatolar bazasiga shu zahoti saqlash
    await _record_immediate_error(callback.message.chat.id, current_test, user_ans)

    user_answers = data.get("user_answers", {})
    user_answers[str(idx)] = user_ans
    await state.update_data(current_index=idx + 1, user_answers=user_answers)
    await callback.answer()
    await _delete_callback_message(callback)
    await send_test_question(callback.message, state)


@router.message(TestState.answering_tests)
async def process_text_answer(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Iltimos, javobingizni matn ko'rinishida yuboring.")
        return
    if message.text.startswith("/"):
        return
        
    user_ans = message.text.strip()
    data = await state.get_data()
    
    idx = data.get("current_index", 0)
    tests = data.get("tests", [])
    if idx >= len(tests):
        await finish_exam(message, state)
        return
    if tests[idx]["question_type"] == "single":
        await message.answer("Yopiq savol uchun javobni variant tugmalaridan tanlang.")
        return

    current_test = tests[idx]
    # Har bir xato belgilangan javobdan keyin xatolar bazasiga shu zahoti saqlash
    await _record_immediate_error(message.chat.id, current_test, user_ans)

    user_answers = data.get("user_answers", {})
    user_answers[str(idx)] = user_ans
    await state.update_data(current_index=idx + 1, user_answers=user_answers)
    
    await send_test_question(message, state)


@router.callback_query(TestState.answering_tests, F.data == "finish_exam_request")
async def request_finish_exam(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("tests"):
        await callback.answer("Faol test topilmadi.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, tugatish", callback_data="finish_exam_confirm_yes"),
            InlineKeyboardButton(text="❌ Yo'q, davom etish", callback_data="finish_exam_confirm_no")
        ]
    ])
    await callback.message.answer(
        "⚠️ <b>Rostdan ham testni muddatidan oldin yakunlamoqchimisiz?</b>\n"
        "<i>Hozirgacha ishlagan natijangiz va qilingan xatolar saqlanadi.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(TestState.answering_tests, F.data == "finish_exam_confirm_no")
async def cancel_finish_exam(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Test davom etmoqda.")
    await _delete_callback_message(callback)
    await send_test_question(callback.message, state)


@router.callback_query(TestState.answering_tests, F.data == "finish_exam_confirm_yes")
async def finish_exam_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Natija hisoblanmoqda...")
    await finish_exam(callback.message, state, is_manual_stop=True)


async def finish_exam(message: Message, state: FSMContext, is_manual_stop: bool = False):
    data = await state.get_data()
    await state.set_state(TestState.finishing)
    tests = data.get("tests", [])
    user_answers = data.get("user_answers", {})
    subject = data.get("subject")
    
    if not subject or not tests:
        logging.error("Cannot finish mock exam: missing subject or questions.")
        await message.answer(
            "⚠️ Test ma'lumotlari topilmadi. Iltimos, testni qaytadan boshlang.",
            reply_markup=get_subjects_keyboard(),
        )
        await state.clear()
        return

    answered_count = len(user_answers)
    is_completed = (not is_manual_stop) and (answered_count >= len(tests))

    correct_count = 0
    total_score = 0.0
    for i, test in enumerate(tests):
        user_answer = str(user_answers.get(str(i), "")).strip().lower()
        correct_answer = str(test["correct_answer"]).strip().lower()
        if user_answer and user_answer == correct_answer:
            correct_count += 1
            total_score += {1: 1.3, 2: 2.2, 3: 3.4}.get(
                test.get("difficulty") or 1,
                3.4
            )

    user_rank = None
    result_saved = False
    try:
        async with async_session() as session:
            user_res = await session.execute(
                select(User).where(User.tg_id == message.chat.id)
            )
            user_obj = user_res.scalars().first()

            if user_obj is not None:
                # 1. Barcha qilingan xatolar va yechilmagan savollarni UserError ga kiritish
                for i, test in enumerate(tests):
                    user_answer = str(user_answers.get(str(i), "")).strip().lower()
                    correct_answer = str(test["correct_answer"]).strip().lower()
                    if user_answer != correct_answer:
                        existing_err = await session.execute(
                            select(UserError).where(
                                (UserError.user_id == user_obj.id) &
                                (UserError.test_id == test["id"])
                            )
                        )
                        err_entry = existing_err.scalars().first()
                        if not err_entry:
                            session.add(
                                UserError(
                                    user_id=user_obj.id,
                                    test_id=test["id"],
                                    user_answer=user_answer if user_answer else "Belgilanmagan"
                                )
                            )

                # 2. TestResult ni to'liq yoki muddatidan oldin holati bilan saqlash
                new_result = TestResult(
                    user_id=user_obj.id,
                    subject=subject,
                    correct_count=correct_count,
                    answered_count=answered_count,
                    total_questions=len(tests),
                    score=round(total_score, 1),
                    is_completed=is_completed
                )
                session.add(new_result)
                await session.commit()
                result_saved = True

                # 3. Har bir testdan so'ng darhol yangilangan reytingdagi o'rnini hisoblash
                rank_query = await session.execute(
                    select(User.id, func.max(TestResult.score).label("max_score"))
                    .join(TestResult, User.id == TestResult.user_id)
                    .group_by(User.id)
                    .order_by(func.max(TestResult.score).desc())
                )
                all_ranks = rank_query.all()
                for r_idx, (u_id, max_s) in enumerate(all_ranks, 1):
                    if u_id == user_obj.id:
                        user_rank = r_idx
                        break

    except SQLAlchemyError:
        logging.exception("Failed to save mock-test result for Telegram user %s.", message.chat.id)

    status_badge = "🟢 <b>To'liq yakunlandi</b>" if is_completed else f"🟡 <b>Muddatidan oldin tugatildi ({answered_count} / {len(tests)} yechildi)</b>"
    rank_str = f"🏆 <b>Reytingdagi yangi o'rningiz:</b> #{user_rank}-o'rin\n" if user_rank else ""

    report = (
        f"📊 <b>MOCK TEST NATIJASI</b>\n\n"
        f"📖 Fan: <b>{subject}</b>\n"
        f"📌 Holat: {status_badge}\n"
        f"✅ To'g'ri javoblar: <b>{correct_count} ta</b>\n"
        f"❌ Noto'g'ri/Tashlab ketilgan: <b>{len(tests) - correct_count} ta</b>\n"
        f"⭐ To'plangan ball: <b>{round(total_score, 1)} ball</b>\n"
        f"{rank_str}\n"
        f"<i>Barcha xatolaringiz '⚠️ Xatolar Ustida Ishlash' bo'limida saqlandi.</i>"
    )
    if not result_saved:
        report += (
            "\n\n⚠️ Natija hisoblandi, ammo bazaga saqlashda xatolik yuz berdi."
        )
    
    await message.answer(report, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await state.clear()