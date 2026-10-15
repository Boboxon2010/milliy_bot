import json
import logging
import re
from utils.gemini_client import GEMINI_API_KEY, generate_text_async

if not GEMINI_API_KEY:
    logging.warning("⚠️ GEMINI_API_KEY topilmadi! .env faylini tekshiring.")


def _clean_json_text(text: str) -> str:
    """Markdown kod bloklarini tozalab, toza JSON matnini ajratib oladi."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Agar matn ichida JSON obyekti bo'lsa, uni qidirish
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def _calculate_level(percentage: float) -> str:
    if percentage >= 70:
        return "A+ (Maksimal imtiyoz)"
    elif percentage >= 65:
        return "A (Maksimal imtiyoz)"
    elif percentage >= 60:
        return "B+ (Yuqori daraja)"
    elif percentage >= 55:
        return "B (Yaxshi daraja)"
    elif percentage >= 50:
        return "C+ (O'rtacha daraja)"
    elif percentage >= 46:
        return "C (Qoniqarli)"
    else:
        return "Yetarli emas (Sertifikat berilmaydi)"


async def evaluate_essay_with_ai(topic: str, essay_text: str, essay_type: str = "situational") -> dict:
    """
    UzBMB (Milliy Sertifikat) ona tili va adabiyot mezonlari asosida
    inshoni professional baholash.
    Maksimal ball: 24 ball.
    """
    clean_essay = (essay_text or "").strip()
    words = clean_essay.split()
    word_count_est = len(words)

    # Dastlabki tezkor tekshiruv (juda qisqa yoki bo'sh matnlar uchun)
    if word_count_est < 25:
        return {
            "is_valid": False,
            "evaluation_error": False,
            "feedback": (
                f"⚠️ Yozilgan matn hajmi juda qisqa ({word_count_est} ta so'z). "
                "Milliy sertifikat talabiga ko'ra insho kamida 120-150 ta so'zdan iborat bo'lishi kerak."
            )
        }

    system_instruction = (
        "Siz UzBMB (Bilimni baholash agentligi - Davlat test markazi) Milliy Sertifikat "
        "ona tili va adabiyot fani bo'yicha bosh ekspert-baholovchisiz.\n"
        "Sizning vazifangiz taqdim etilgan insho (esse) matnini rasmiy 24 ballik mezonlar "
        "asosida xolis, aniq va talabchan baholash.\n"
        "Baholash 4 ta mezon bo'yicha amalga oshiriladi (har biri 0 dan 6 ballgacha):\n"
        "1. task_achievement: Mavzuning to'liq va chuqur ochib berilishi, topshiriq shartlariga mosligi (max 6 ball)\n"
        "2. coherence: Fikrlar izchilligi, mantiqiy bog'liqlik, abzaslarga to'g'ri bo'linishi (max 6 ball)\n"
        "3. vocabulary: Lug'at boyligi, badiiy-uslubiy vositalardan o'rinli foydalanish (max 6 ball)\n"
        "4. grammar: Grammatik qoidalar, imlo (orfografiya) va tinish belgilari (max 6 ball)\n\n"
        "Javobingizni FAQAT haqiqiy JSON formatida qaytaring, boshqa hech qanday so'z qo'shmang."
    )

    prompt = f"""
Quyidagi insho matnini baholang va natijani quyidagi JSON tuzilmasida bering:
{{
    "is_valid": true,
    "word_count": {word_count_est},
    "sentence_count": 12,
    "paragraph_count": 4,
    "score_total": 20.5,
    "percentage": 85.4,
    "level": "A (Maksimal imtiyoz)",
    "criteria": {{
        "task_achievement": "5.5 / 6",
        "coherence": "5.0 / 6",
        "vocabulary": "5.0 / 6",
        "grammar": "5.0 / 6"
    }},
    "strong_points": [
        "Inshoning ijobiy va kuchli jihatlari..."
    ],
    "weak_points": [
        "Aniq imlo, grammatik yoki uslubiy xatolar va ularning to'g'rilangan shakli..."
    ],
    "recommendations": [
        "Keyingi safar natijani oshirish bo'yicha amaliy tavsiyalar..."
    ],
    "feedback": "Umumiy xulosa"
}}

Agar matn mutlaqo mavzuga aloqador bo'lmasa, behayo yoki ma'nosiz so'zlar ketma-ketligi bo'lsa:
{{
    "is_valid": false,
    "feedback": "Rad etilishining aniq sababi..."
}}

[Esse Mavzusi va Topshirig'i]:
{topic}

[Esse Turi]:
{essay_type}

[Foydalanuvchi Inshosi]:
\"\"\"
{clean_essay}
\"\"\"
"""

    try:
        response_text = await generate_text_async(
            prompt=prompt,
            json_mode=True,
            system_instruction=system_instruction
        )
        cleaned_json = _clean_json_text(response_text)
        data = json.loads(cleaned_json)

        # Ma'lumotlarni to'ldirish va xatoliklardan himoyalash
        if not isinstance(data, dict):
            raise ValueError("Qaytgan JSON dict formatida emas.")

        if not data.get("is_valid", True):
            return {
                "is_valid": False,
                "feedback": data.get("feedback", "Matn insho talablariga javob bermaydi."),
            }

        # Standart maydonlar to'liqligini ta'minlash
        criteria = data.get("criteria", {})
        if not isinstance(criteria, dict):
            criteria = {}

        task_ach = criteria.get("task_achievement", "4.0 / 6")
        coherence = criteria.get("coherence", "4.0 / 6")
        vocab = criteria.get("vocabulary", "4.0 / 6")
        grammar = criteria.get("grammar", "4.0 / 6")

        score_total = data.get("score_total")
        if score_total is None:
            score_total = 16.0
        try:
            score_total = float(score_total)
        except (ValueError, TypeError):
            score_total = 16.0

        if score_total > 24.0:
            score_total = 24.0
        elif score_total < 0:
            score_total = 0.0

        percentage = data.get("percentage")
        if percentage is None:
            percentage = round((score_total / 24.0) * 100, 1)
        else:
            try:
                percentage = round(float(percentage), 1)
            except (ValueError, TypeError):
                percentage = round((score_total / 24.0) * 100, 1)

        level = data.get("level") or _calculate_level(percentage)

        return {
            "is_valid": True,
            "word_count": data.get("word_count", word_count_est),
            "sentence_count": data.get("sentence_count", max(1, len(re.split(r"[.!?]+", clean_essay)) - 1)),
            "paragraph_count": data.get("paragraph_count", max(1, len([p for p in clean_essay.split("\n") if p.strip()]))),
            "score_total": round(score_total, 1),
            "percentage": percentage,
            "level": level,
            "criteria": {
                "task_achievement": str(task_ach),
                "coherence": str(coherence),
                "vocabulary": str(vocab),
                "grammar": str(grammar),
            },
            "strong_points": data.get("strong_points", []),
            "weak_points": data.get("weak_points", []),
            "recommendations": data.get("recommendations", []),
            "feedback": data.get("feedback", "Insho tahlil qilindi."),
        }

    except json.JSONDecodeError:
        logging.exception("JSON decoding failed for essay evaluation.")
        return {
            "is_valid": False,
            "evaluation_error": True,
            "feedback": "⚠️ AI javobini qayta ishlashda xatolik yuz berdi. Iltimos, qayta yuborib ko'ring.",
        }
    except Exception as exc:
        logging.exception("Gemini evaluation error: %s", exc)
        return {
            "is_valid": False,
            "evaluation_error": True,
            "feedback": "⚠️ AI tekshirish tizimida vaqtinchalik xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.",
        }