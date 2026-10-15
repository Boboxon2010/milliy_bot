import random


THEMES = (
    "Ta'lim va texnologiyalar",
    "Atrof-muhit va ekologiya",
    "Sog'liqni saqlash va sport",
    "Karyera va biznes",
    "Madaniyat va san'at",
    "Ijtimoiy muammolar va oila",
    "Turizm va sayohat",
    "Shaxsiy rivojlanish va psixologiya",
    "Infratuzilma va transport",
    "Kiberxavfsizlik va innovatsiyalar",
)

TASK_FORMATS = (
    (
        "Xat / elektron xat",
        "Siz «{theme}» sohasida faoliyat yurituvchi tashkilot yoki mas'ul shaxsga "
        "rasmiy murojaat yozishingiz kerak. Ushbu yo'nalishda muammo yoki taklifingiz bor.",
        (
            "Sohadagi aniq muammo yoki ehtiyojni batafsil bayon qiling.",
            "Bu holat kundalik hayotingizga yoki jamoangizga qanday ta'sir qilishini tushuntiring.",
            "Muammoni hal etish bo'yicha amaliy taklif yoki talablaringizni bildiring.",
        ),
    ),
    (
        "Hisobot",
        "Sizdan «{theme}» bo'yicha hududingizda yoki tashkilotingizda amalga oshirilgan "
        "ishlar va ularning natijalari haqida tahliliy hisobot tayyorlash so'raldi.",
        (
            "Erishilgan ijobiy natijalar va muvaffaqiyatlarni ko'rsating.",
            "Aniqlangan kamchiliklar, to'siqlar va muammolarni tahlil qiling.",
            "Vaziyatni yaxshilash va muammolar takrorlanishining oldini olish uchun tavsiyalar bering.",
        ),
    ),
    (
        "Loyiha taklifi",
        "Siz «{theme}» sohasini rivojlantirishga qaratilgan yangi loyiha ishlab chiqdingiz "
        "va uni qo'llab-quvvatlash uchun taklif taqdim etmoqchisiz.",
        (
            "Loyiha mazmunini bayon qiling va nima uchun bu soha uchun dolzarb ekanini asoslang.",
            "Amalga oshirish bosqichlari hamda zarur resurslarni (mablag', mutaxassislar, jihozlar) ko'rsating.",
            "Kutilayotgan natijalar va loyihaning uzoq muddatli foydasini tahlil qiling.",
        ),
    ),
    (
        "Maqola",
        "Siz yoshlar yoki mutaxassislar uchun mo'ljallangan nashrda «{theme}» haqidagi "
        "dolzarb qarashlarni yorituvchi tahliliy maqola yozishingiz kerak.",
        (
            "Sohadagi muhim tendensiyalar va ijobiy jihatlarni ochib bering.",
            "Mavjud stereotiplar, xavf-xatarlar yoki salbiy oqibatlarni tanqidiy tahlil qiling.",
            "Jamiyat va insonlar bu yo'nalishdan samarali foydalanishi uchun tavsiyalar bering.",
        ),
    ),
)


def _build_topic(index: int) -> str:
    task_name, context_template, bullet_points = TASK_FORMATS[index % len(TASK_FORMATS)]
    theme = THEMES[index % len(THEMES)]
    context = context_template.format(theme=theme)
    points = "\n".join(f"• {point}" for point in bullet_points)
    return (
        f"{task_name} — {theme}\n"
        f"Vaziyat: {context}\n"
        f"Topshiriq:\n{points}"
    )


ESSAY_TOPICS = tuple(_build_topic(index) for index in range(20))


def get_random_essay_topics() -> list[str]:
    return random.sample(ESSAY_TOPICS, 2)
