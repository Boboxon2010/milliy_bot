import asyncio
from database.connection import async_session
from database.models import Test

TESTS_DATA = [
    # 30 ta Yopiq testlar (single) misollari
    {
        "q": "Qaysi qatordagi so‘zda tutuq belgisi ajratish vazifasini bajargan?",
        "a": "Ma’rifat", "b": "Mo’jiza", "c": "Jur’at", "d": "Ma’sud",
        "cor": "C", "type": "single", "diff": 1, "exp": "Ma'rifat so'zida tutuq belgisi ajratish vazifasida."
    },
    {
        "q": "\"Sadoqatli do‘st har doim yoningda turadi\" gapidagi yasama so‘zlar turkumini aniqlang.",
        "a": "Ot, Sifat", "b": "Sifat, Ravish", "c": "Ot, Fe'l", "d": "Sifat, Ot",
        "cor": "A", "type": "single", "diff": 1, "exp": "Sadoqatli - sifat, do'st - ot."
    },
    {
        "q": "Qaysi qatorda faqat o‘zbekcha so‘zlar berilgan?",
        "a": "Qalam, daftar, kitob", "b": "Bilim, ona, yurak", "c": "Maktab, muallim, dars", "d": "Quyosh, oydin, chiroq",
        "cor": "B", "type": "single", "diff": 1, "exp": "Bilim, ona, yurak asl o'zbekcha."
    },
    {
        "q": "\"Yaxshilik qil, yomonlikdan qoch\" gapida antonimlar qaysi so'z turkumiga oid?",
        "a": "Ot", "b": "Sifat", "c": "Ravish", "d": "Fe'l",
        "cor": "A", "type": "single", "diff": 1, "exp": "Yaxshilik va yomonlik ot turkumiga oid."
    },
    {
        "q": "Qaysi gapda ravishdosh qatnashgan?",
        "a": "U kulib gapirdi.", "b": "Kelgan mehmonlarni kutib oldik.", "c": "O'qishni tugatish oson emas.", "d": "Kitob o'qiyotgan bola mening ukam.",
        "cor": "A", "type": "single", "diff": 1, "exp": "-ib ravishdosh yasagan."
    },
    # Kerakli miqdorda (30 tadan kam bo'lmagan yopiq va 15 tadan kam bo'lmagan ochiq testlarni shu yerga qo'shishingiz mumkin)
    # Misol tariqasida 15 ta ochiq test (text):
    {
        "q": "\"Kitob insonning eng yaqin do‘stidir\" gapidagi sifatning darajasini aniqlang.",
        "a": None, "b": None, "c": None, "d": None,
        "cor": "orttirma daraja", "type": "text", "diff": 2, "exp": "Orttirma daraja."
    },
    {
        "q": "\"O‘zbekiston vatanim manim\" deb boshlanuvchi she'riy asarning muallifi kim?",
        "a": None, "b": None, "c": None, "d": None,
        "cor": "abdulla oripov", "type": "text", "diff": 2, "exp": "Abdulla Oripov."
    },
    {
        "q": "O‘zbek alifbosida nechta unli harf mavjud?",
        "a": None, "b": None, "c": None, "d": None,
        "cor": "6", "type": "text", "diff": 2, "exp": "6 ta unli harf."
    }
]

async def seed():
    async with async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(Test).where(Test.subject == "Ona tili va adabiyot"))
        
        for t in TESTS_DATA:
            test_obj = Test(
                subject="Ona tili va adabiyot",
                question_text=t["q"],
                question_type=t["type"],
                difficulty=t["diff"],
                option_a=t["a"],
                option_b=t["b"],
                option_c=t["c"],
                option_d=t["d"],
                correct_answer=t["cor"].strip().lower(),
                explanation=t["exp"]
            )
            session.add(test_obj)
        await session.commit()
        print("✅ Testlar muvaffaqiyatli bazaga yuklandi!")

if __name__ == "__main__":
    asyncio.run(seed())