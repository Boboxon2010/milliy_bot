import asyncio
from database.connection import async_session, init_db
from database.models import Test

EXACT_MATH_TESTS = [
    # 1-QISM: Yopiq turdagi testlar (1 - 26)
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "1. a va b natural sonlar uchun a * b = 30 bo'lsa, a + 2b - 1 ifodaning eng kichik qiymatini toping.",
        "option_a": "16", "option_b": "12", "option_c": "15", "option_d": "31",
        "correct_answer": "C", "explanation": "a=6, b=5 bo'lganda a + 2b - 1 = 6 + 10 - 1 = 15."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "2. Hisoblang: 7,2(1) - 4,4(2) + 31/90.",
        "option_a": "3,1(3)", "option_b": "3,1(2)", "option_c": "2,1(3)", "option_d": "2,1(2)",
        "correct_answer": "B", "explanation": "Davrli kasrlarni oddiy kasrga o'tkazib hisoblanganda 3,1(2) hosil bo'ladi."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "3. Do'kon 3 kunda jami 175 kg kartoshka sotdi. Ikkinchi kun uchinchi kunga nisbatan 1,5 marta ko'p, birinchi kun esa ikkinchi kunga nisbatan 2,4 marta kam kartoshka sotgan. Do'kon birinchi kun necha kg kartoshka sotgan?",
        "option_a": "35", "option_b": "44", "option_c": "56", "option_d": "27",
        "correct_answer": "A", "explanation": "Tenglamalar tizimidan 1-kun 35 kg sotgani kelib chiqadi."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "4. Xonaga eni 2,4 m va bo'yi 4 m bo'lgan to'g'ri to'rtburchak shaklidagi gilam to'shalgan. Agar xonaning eni 4 m va bo'yi 6 m bo'lsa, gilam bilan qoplanmagan qism yuzini toping.",
        "option_a": "9,6", "option_b": "24", "option_c": "14,4", "option_d": "12,8",
        "correct_answer": "C", "explanation": "Xona yuzi: 24, gilam yuzi: 9,6. Qoplanmagan qism: 24 - 9,6 = 14,4."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "5. (2^20 + 2^18) / (2^19 - 2^17) ifodaning qiymatini hisoblang.",
        "option_a": "2", "option_b": "10/3", "option_c": "1/3", "option_d": "4",
        "correct_answer": "B", "explanation": "Surat va maxraj 2^17 ga qisqartirilib soddalashtiriladi."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "6. 3(x - 2) - 2(x - 3) = 5 - x tenglamani yeching.",
        "option_a": "-5", "option_b": "2.5", "option_c": "0", "option_d": "1",
        "correct_answer": "B", "explanation": "3x - 6 - 2x + 6 = 5 - x => 2x = 5 => x = 2.5."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "7. Arifmetika progressiyada a_1 = 3 va d = 4 bo'lsa, uning dastlabki 15 ta hadi yig'indisini toping.",
        "option_a": "390", "option_b": "465", "option_c": "510", "option_d": "420",
        "correct_answer": "B", "explanation": "S_15 = ((2*3 + 14*4)/2)*15 = 465."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "8. To'g'ri to'rtburchakning tomonlari nisbati 3:4 kabi, perimetri esa 56 sm. Uning yuzini toping.",
        "option_a": "144", "option_b": "192", "option_c": "108", "option_d": "216",
        "correct_answer": "B", "explanation": "Tomonlar 12 va 16, yuzi 12 * 16 = 192."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "9. |2x - 3| = 5 tenglamaning ildizlari ko'paytmasini toping.",
        "option_a": "-4", "option_b": "-2", "option_c": "2", "option_d": "4",
        "correct_answer": "A", "explanation": "Ildizlar: 4 va -1. Ko'paytmasi: 4 * (-1) = -4."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "10. f(x) = sqrt(5 - x) + 1/sqrt(x - 2) funksiyaning aniqlanish sohasini toping.",
        "option_a": "[2; 5]", "option_b": "(2; 5]", "option_c": "[2; 5)", "option_d": "(-inf; 5]",
        "correct_answer": "B", "explanation": "5 - x >= 0 va x - 2 > 0 shartlardan (2; 5] kelib chiqadi."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "11. 2x^2 - 7x + 3 = 0 kvadrat tenglama ildizlari kvadratlarining yig'indisini toping.",
        "option_a": "10.25", "option_b": "9.25", "option_c": "8.5", "option_d": "12",
        "correct_answer": "B", "explanation": "Viyet teoremasi orqali x_1^2 + x_2^2 = 9.25."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "12. sin(2a) / (1 + cos(2a)) ifodani soddalashtiring.",
        "option_a": "ctg(a)", "option_b": "tg(a)", "option_c": "sin(a)", "option_d": "cos(a)",
        "correct_answer": "B", "explanation": "Keltirilgan formulalar bo'yicha tg(a) ga teng."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "13. log_2(x - 1) + log_2(x + 2) = 2 tenglamaning ildizini toping.",
        "option_a": "-3", "option_b": "2", "option_c": "3", "option_d": "{2; -3}",
        "correct_answer": "B", "explanation": "Olinadigan ildizlardan x = 2 shartni qanoatlantiradi."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "14. 3^(x+1) + 3^(x-1) = 30 tenglamani yeching.",
        "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "0",
        "correct_answer": "B", "explanation": "3^x * (10/3) = 30 => 3^x = 9 => x = 2."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "15. ABC uchburchakda BD mediana 4 sm ga teng. Agar ABD uchburchakning perimetri 12 sm bo'lib, AD = BD bo'lsa, AB tomon uzunligini toping.",
        "option_a": "6", "option_b": "4", "option_c": "8", "option_d": "5",
        "correct_answer": "B", "explanation": "ABD perimetri = AB + AD + BD = 12 => AB + 4 + 4 = 12 => AB = 4."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "16. A_n^2 = 72 bo'lsa, n natural sonni toping.",
        "option_a": "8", "option_b": "9", "option_c": "10", "option_d": "12",
        "correct_answer": "B", "explanation": "n*(n-1) = 72 => n = 9."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "17. Qutida 8 ta oq va 8 ta qizil shar bor. Tasodifan olingan 2 ta sharning ikkalasi ham oq rangda bo'lishi ehtimolligini toping.",
        "option_a": "1/2", "option_b": "7/30", "option_c": "1/4", "option_d": "8/15",
        "correct_answer": "B", "explanation": "C(8,2)/C(16,2) = 28/120 = 7/30."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 3,
        "question_text": "18. f(x) = x^3 - 3x^2 + 5 funksiyaning lokal minimum nuqtasini toping.",
        "option_a": "x = 0", "option_b": "x = 2", "option_c": "x = 1", "option_d": "Ekstremumi yo'q",
        "correct_answer": "B", "explanation": "f'(x) = 3x(x-2) = 0. x = 2 da minimum."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "19. Integralni hisoblang: \\int_1^2 (3x^2 - 2x) dx.",
        "option_a": "3", "option_b": "4", "option_c": "5", "option_d": "6",
        "correct_answer": "B", "explanation": "Boshlang'ich funksiya x^3 - x^2. Natija: 4."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "20. a (3; -4) va b (1; 7) vektorlarning skalar ko'paytmasini toping.",
        "option_a": "-31", "option_b": "-25", "option_c": "25", "option_d": "31",
        "correct_answer": "B", "explanation": "3*1 + (-4)*7 = -25."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "21. z_1 = 3 + 4i va z_2 = 1 - 2i bo'lsa, z_1 + z_2 kompleks sonning modulini toping.",
        "option_a": "5", "option_b": "sqrt(20)", "option_c": "6", "option_d": "5*sqrt(2)",
        "correct_answer": "B", "explanation": "z_1 + z_2 = 4 + 2i, moduli sqrt(16+4) = sqrt(20)."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "22. Cheksiz kamayuvchi geometrik progressiyada b_1 = 12 va yig'indisi S = 18 bo'lsa, uning maxrajini toping.",
        "option_a": "2/3", "option_b": "1/3", "option_c": "1/2", "option_d": "3/4",
        "correct_answer": "B", "explanation": "S = b_1 / (1 - q) => q = 1/3."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 2,
        "question_text": "23. A = [[3, 5], [2, 4]] matritsaning determinantini toping.",
        "option_a": "22", "option_b": "2", "option_c": "-2", "option_d": "7",
        "correct_answer": "B", "explanation": "3*4 - 5*2 = 2."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "24. Aylanadagi markaziy burchak 70 gradusga teng. Shu markaziy burchakka tayanuvchi ichki chizilgan burchakni toping.",
        "option_a": "140 gradus", "option_b": "35 gradus", "option_c": "70 gradus", "option_d": "105 gradus",
        "correct_answer": "B", "explanation": "Ichki chizilgan burchak markaziy burchakning yarmi: 35 gradus."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 3,
        "question_text": "25. f(x) = 3sin(x) - 4cos(x) + 5 funksiyaning qiymatlar sohasini toping.",
        "option_a": "[-5; 5]", "option_b": "[0; 10]", "option_c": "[-10; 0]", "option_d": "[-5; 10]",
        "correct_answer": "B", "explanation": "Qiymatlar sohasi [0; 10]."
    },
    {
        "subject": "Matematika", "question_type": "single", "difficulty": 1,
        "question_text": "26. |x - 3| <= 4 tengsizlikning butun yechimlari sonini toping.",
        "option_a": "7", "option_b": "9", "option_c": "8", "option_d": "10",
        "correct_answer": "B", "explanation": "Butun yechimlar soni 9 ta."
    },

    # 2-QISM: Ochiq turdagi testlar (27 - 45)
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "27. 3^2026 sonini 7 ga bo'lgandagi qoldiqni toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "4", "explanation": "Qoldiqlar davri 6 ga teng. 2026 mod 6 = 4 => qoldiq 4."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "28. 5 ta o‘g‘il bola va 3 ta qiz bola bir qatorga shunday o‘tqazilishi kerakki, hech qanday ikki qiz yonma-yon o‘tirmasin. Buni necha xil usulda amalga oshirish mumkin?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "14400", "explanation": "120 * 120 = 14400."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "29. x = 2 (mod 3), x = 3 (mod 5) va x = 2 (mod 7) shartlarni qanoatlantiruvchi eng kichik musbat butun x sonini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "23", "explanation": "Shartni qanoatlantiruvchi eng kichik son 23."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "30. 0, 1, 2, 3, 4, 5 raqamlaridan raqamlari takrorlanmaydigan va 5 ga bo'linadigan nechta 4 xonali son tuzish mumkin?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "108", "explanation": "Jami 108 ta son."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "31. Tashqi ko‘rinishi bir xil bo‘lgan 9 ta tangadan bittasi qolganlaridan og‘irroq (soxta). Pallali tarozi yordamida og‘ir tangani aniq topish uchun eng kamida nechta o‘lchov kerak bo‘ladi?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "2", "explanation": "2 ta o'lchov yetarli."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "32. a va b parallel to'g'ri chiziqlardan nuqtalar olindi. a to'g'ri chiziqdan 5 ta, b to'g'ri chiziqdan 4 ta nuqta olindi. Bu nuqtalarni uchlari qilib jami nechta har xil uchburchak hosil qilish mumkin?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "70", "explanation": "40 + 30 = 70 ta uchburchak."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "33. f(x) = x^2 - 4x + 7 funksiyaning [0; 5] kesmadagi eng kichik qiymatini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "3", "explanation": "x = 2 nuqtada qiymat 3 ga teng."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "34. Teng yonli trapesiyaning asoslari 10 sm va 26 sm, diagonalining o'rtalarini tutashtiruvchi kesma uzunligini toping (sm).",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "8", "explanation": "(26 - 10) / 2 = 8 sm."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "35. Agar log_a(b) = 3 bo'lsa, log_(a^2)(b^3) + log_(b)(a) ifodaning qiymatini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "29/6", "explanation": "Hisob-kitob natijasi 29/6."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "36. Tenglamani yeching: sqrt(x + 2) = x.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "2", "explanation": "Ildiz x = 2."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "37. Rombning diagonallari 12 sm va 16 sm bo'lsa, uning tomonini toping (sm).",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "10", "explanation": "Tomoni 10 sm."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "38. 1 dan 100 gacha bo'lgan natural sonlar orasida 3 ga ham, 5 ga ham bo'linmaydigan sonlar nechta?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "53", "explanation": "Jami 53 ta."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "39. f(x) = ln(x^2 - 3x + 2) funksiyaning hosilasi x = 3 nuqtada nechaga teng?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "1.5", "explanation": "Hosilasi 1.5 ga teng."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "40. Sirtining yuzi 144*pi sm^2 bo'lgan sharning hajmini toping (javobni pi ga bo'lib yozing).",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "288", "explanation": "Hajm 288."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 1,
        "question_text": "41. To'g'ri burchakli uchburchakning gipotenuzasi 13 sm, katetlaridan biri 5 sm. Ikkinchi katetiga yopishgan o'tkir burchakning kosinusini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "5/13", "explanation": "Kosinusi 5/13."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 3,
        "question_text": "42. 7 ta kitobni 3 ta o'quvchiga, birinchi o'quvchiga 2 ta, ikkinchisiga 3 ta va uchinchisiga 2 ta kitob tushadigan qilib necha xil usulda tarqatish mumkin?",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "210", "explanation": "Tarqatish usullari soni 210."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 1,
        "question_text": "43. f(x) = 2x + 1 funksiya berilgan. f(f(f(1))) ning qiymatini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "15", "explanation": "Qiymati 15."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "44. x^2 - 5x + 6 = 0 va x^2 - 6x + 8 = 0 tenglamalarning umumiy ildizini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "2", "explanation": "Umumiy ildiz 2."
    },
    {
        "subject": "Matematika", "question_type": "open", "difficulty": 2,
        "question_text": "45. Markazi (2; -3) nuqtada va radiusi 5 sm bo'lgan aylananing tenglamasidan foydalanib, ushbu aylana y o'qini kesib o'tgan nuqtalarining koordinatalari yig'indisini toping.",
        "option_a": None, "option_b": None, "option_c": None, "option_d": None,
        "correct_answer": "-6", "explanation": "Koordinatalar yig'indisi -6."
    }
]

async def seed_exact():
    await init_db()
    async with async_session() as session:
        print("🔄 Aniq 45 ta matematika testlari bazaga yozilmoqda...")
        for item in EXACT_MATH_TESTS:
            test = Test(**item)
            session.add(test)
        await session.commit()
        print("✅ Matematika fanidan 45 ta test muvaffaqiyatli bazaga qo'shildi!")

if __name__ == "__main__":
    asyncio.run(seed_exact())