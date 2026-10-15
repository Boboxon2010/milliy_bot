import logging
from utils.gemini_client import GEMINI_API_KEY, generate_text_async


async def grade_essay_with_ai(topic: str, essay_text: str) -> str:
    if not GEMINI_API_KEY:
        return "❌ Xatolik: Gemini API kaliti topilmadi (.env faylini tekshiring)."

    prompt = f'''
Siz UzBMB (Bilimni baholash agentligi) Milliy Sertifikat imtihonlarining professional til va adabiyot/tarix bo'yicha qattiqqo'l ekspertisiz.

Quyidagi mavzu bo'yicha yozilgan esseni professional darajada tahlil qiling va baholang.

Mavzu: "{topic}"
Talaba yozgan esse:
"""
{essay_text}
"""

Iltimos, tahlilni quyidagi tuzilmada o'zbek tilida bering:
1. **Umumiy ball (24 balldan):** (Masalan: 19/24)
2. **Mezonlar bo'yicha qisqacha baho:**
   - Mavzuni ochib berish: (...)
   - Leksika va lug'at boyligi: (...)
   - Grammatika va imlo xatolari: (...)
   - Mantiqiy izchillik: (...)
3. **Asosiy xatolar va ularning tuzatilgan ko'rinishi:** (Agar imlo yoki grammatik xatolar bo'lsa ko'rsating)
4. **Maslahat va tavsiyalar:** (Keyingi safar esse yozishda nimaga e'tibor berish kerak)

Javobni aniq, tushunarli va ruhlantiruvchi, lekin talabchan ustoz ohangida yozing.
'''

    try:
        return await generate_text_async(prompt)
    except Exception as e:
        logging.exception("grade_essay_with_ai failed: %s", e)
        return f"❌ AI xizmatiga ulanishda xatolik yuz berdi: {str(e)}"