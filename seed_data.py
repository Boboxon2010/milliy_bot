import asyncio
from database.connection import async_session, init_db
from database.models import Test

UZBMB_REAL_MOCK_TESTS = [
    # --- MATEMATIKA (Ochiq va Murakkab masalalar) ---
    {
        "subject": "Matematika",
        "question_type": "open",
        "difficulty": 3,
        "question_text": "📐 **Ochiq masala (Javobni raqam ko'rinishida yozing):**\n\nTeng yonli uchburchakning yon tomoni 10 cm ga, asosiga tushirilgan balandligi 8 cm ga teng. Ushbu uchburchakka ichki chizilgan aylana radiusini (cm) toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "3",
        "explanation": "Asosning yarmi: sqrt(10^2 - 8^2) = 6 cm. Asos = 12 cm. Yuzasi S = 1/2 * 12 * 8 = 48. Yarim perimetr p = (10+10+12)/2 = 16. Ichki chizilgan aylana radiusi r = S/p = 48/16 = 3."
    },
    {
        "subject": "Matematika",
        "question_type": "single",
        "difficulty": 2,
        "question_text": "📊 **Yopiq test:**\n\nlog_2(x^2 - 3x + 6) = 3 tenglamaning ildizlari yig'indisini toping.",
        "option_a": "3", "option_b": "-3", "option_c": "2", "option_d": "6",
        "correct_answer": "A",
        "explanation": "x^2 - 3x + 6 = 2^3 => x^2 - 3x - 2 = 0. Viyet teoremasiga ko'ra ildizlar yig'indisi x_1 + x_2 = 3."
    },

    # --- ONA TILI VA ADABIYOT (Matn ustida ishlash va Moslashtirish) ---
    {
        "subject": "Ona tili va adabiyot",
        "question_type": "matching",
        "difficulty": 3,
        "question_text": "🔗 **Moslashtirish testi:**\n\nBadiiy asarlar va ularning mualliflarini to'g'ri moslashtiring:\n1. \"O'tkan kunlar\"\n2. \"Kecha va kunduz\"\n3. \"Sarabbor\"\n\nA) Abdulhamid Cho'lpon\nB) Abdulla Qodiriy\nC) Oybek\n\n*Javobni quyidagi shaklda kiriting (Masalan: 1-B, 2-A, 3-C)*",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "1-B, 2-A, 3-C",
        "explanation": "1 - \"O'tkan kunlar\" (Abdulla Qodiriy - B), 2 - \"Kecha va kunduz\" (Cho'lpon - A), 3 - \"Navoiy/Sarabbor\" (Oybek - C)."
    },
    {
        "subject": "Ona tili va adabiyot",
        "question_type": "open",
        "difficulty": 2,
        "question_text": "✍️ **Matnli ochiq topshiriq:**\n\nQuyidagi gapdagi imlo xatosi bilan yozilgan so'zning **TO'G'RI** ko'rinishini yozing:\n\n\"Tadbirkorlar yig'ilishida ko'plab tashabbuskor va minnatdor kammagallar ishtirok etishdi.\"",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "kambag'allar",
        "explanation": "Imlo qoidasiga ko'ra 'kammagallari' emas, 'kambag'allar' shakli to'g'ri yoziladi."
    },

    # --- TARIX (Moslashtirish va Xronologiya) ---
    {
        "subject": "Tarix",
        "question_type": "matching",
        "difficulty": 2,
        "question_text": "📜 **Tarixiy Voqea va Sana Mosligi:**\n\n1. Amir Temur Movarounnahr amiri deb e'lon qilinishi\n2. Janggi loy (Loy jangi)\n3. Anqara jangi\n\nA) 1365-yil\nB) 1370-yil\nC) 1402-yil",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "1-B, 2-A, 3-C",
        "explanation": "1365 - Loy jangi (A), 1370 - Balx qurultoyi va amir deb e'lon qilinishi (B), 1402 - Anqara jangi (C)."
    }
]

async def seed_data():
    await init_db()
    async with async_session() as session:
        for item in UZBMB_REAL_MOCK_TESTS:
            test = Test(**item)
            session.add(test)
            
        await session.commit()
        print("✅ UzBMB Milliy sertifikatning barcha savol turlari (Yopiq, Ochiq, Moslashtirish) bazaga yuklandi!")

if __name__ == "__main__":
    asyncio.run(seed_data())