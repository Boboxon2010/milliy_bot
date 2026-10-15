def calculate_math_score(correct_tests: list, total_questions: int = 45) -> dict:
    """
    UzBMB Nizomi bo'yicha 45 ta matematik savolning ballarini hisoblaydi:
    - 1-daraja (16 ta) × 1.3 ball = 20.8
    - 2-daraja (16 ta) × 2.2 ball = 35.2
    - 3-daraja (13 ta) × 3.4 ball = 44.0
    Jami max: 100 ball
    """
    togri_1 = sum(1 for t in correct_tests if getattr(t, 'difficulty', 1) == 1)
    togri_2 = sum(1 for t in correct_tests if getattr(t, 'difficulty', 1) == 2)
    togri_3 = sum(1 for t in correct_tests if getattr(t, 'difficulty', 1) == 3)

    raw_score = round((togri_1 * 1.3) + (togri_2 * 2.2) + (togri_3 * 3.4), 1)
    percentage = round((raw_score / 100.0) * 100, 1)

    # Daraja va Imtiyozlarni aniqlash
    if percentage >= 70:
        level = "A+"
        main_benefit = "Maksimal ball beriladi (Imtihondan ozod etiladi)"
        mandatory_benefit = "To'liq 11 ball (Maksimal)"
    elif percentage >= 65:
        level = "A"
        main_benefit = "Maksimal ball beriladi (Imtihondan ozod etiladi)"
        mandatory_benefit = "To'liq 11 ball (Maksimal)"
    elif percentage >= 60:
        level = "B+"
        main_benefit = "Proporsional hisoblanadi (Yuqori ball)"
        mandatory_benefit = "To'liq 11 ball (Maksimal)"
    elif percentage >= 55:
        level = "B"
        main_benefit = "Proporsional hisoblanadi"
        mandatory_benefit = "To'liq 11 ball (Maksimal)"
    elif percentage >= 50:
        level = "C+"
        main_benefit = "Proporsional hisoblanadi"
        mandatory_benefit = "To'liq 11 ball (Maksimal)"
    elif percentage >= 46:
        level = "C"
        main_benefit = "Proporsional hisoblanadi"
        mandatory_benefit = "To'liq 11 ball (Maksimal)"
    else:
        level = "Sertifikat berilmaydi"
        main_benefit = "Imtiyoz berilmaydi (46% dan past)"
        mandatory_benefit = "Imtiyoz berilmaydi"

    return {
        "togri_1": togri_1,
        "togri_2": togri_2,
        "togri_3": togri_3,
        "raw_score": raw_score,
        "percentage": percentage,
        "level": level,
        "main_benefit": main_benefit,
        "mandatory_benefit": mandatory_benefit
    }