from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Mock Test Yechish"), KeyboardButton(text="✍️ Esse AI")],
            [KeyboardButton(text="📊 Mening Natijalarim"), KeyboardButton(text="⚠️ Xatolar Ustida Ishlash")],
            [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="👤 Profil")],
            [KeyboardButton(text="ℹ️ Ma'lumot")]
        ],
        resize_keyboard=True
    )

def get_subjects_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Ona tili va adabiyot", callback_data="subj_Ona tili va adabiyot")],
        [InlineKeyboardButton(text="📐 Matematika", callback_data="subj_Matematika")],
        [InlineKeyboardButton(text="⚛️ Fizika", callback_data="subj_Fizika")],
        [InlineKeyboardButton(text="🧪 Kimyo", callback_data="subj_Kimyo")],
        [InlineKeyboardButton(text="📜 Tarix", callback_data="subj_Tarix")],
        [InlineKeyboardButton(text="🇬🇧 Ingliz tili", callback_data="subj_Ingliz tili")]
    ])

def get_essay_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Yangi esse yozish", callback_data="essay_new_menu")],
        [InlineKeyboardButton(text="📚 Mening mavzularim (Tarix)", callback_data="essay_my_topics")],
        [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="essay_back_menu")]
    ])

def get_essay_types_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Opinion (Fikr-mulohaza)", callback_data="essay_opinion")],
        [InlineKeyboardButton(text="⚖️ Discuss Both Sides (Ikkala tomon)", callback_data="essay_both")],
        [InlineKeyboardButton(text="🛠 Problem & Solution (Muammo-Yechim)", callback_data="essay_solution")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="essay_back_menu")]
    ])