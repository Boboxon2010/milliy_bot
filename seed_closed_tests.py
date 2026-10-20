import asyncio
import re
from pathlib import Path

from sqlalchemy import select

from database.connection import async_session, init_db
from database.models import Test


SOURCE_FILES = {
    "Fizika": Path("fizika_200_ta_yopiq_test.txt"),
    "Matematika": Path(
        "matematika_fanidan_200_ta_yopiq_test_uzbmb_milliy_sertifikat_standartlari.txt"
    ),
    "Kimyo": Path("kimyo_200_ta_yopiq_test.txt"),
    "Ona tili va adabiyot": Path(
        "o_zbek_tili_va_adabiyot_fanidan_200_ta_yopiq_test_uzbmb_milliy_sertifikat_standartlari.txt"
    ),
}

VERIFIED_ANSWERS = {
    "Fizika": {
        1: "C", 2: "B", 3: "B", 4: "A", 5: "B", 6: "A", 7: "A", 8: "A",
        9: "B", 10: "B", 11: "A", 12: "B", 13: "A", 14: "B", 15: "A",
        16: "A", 17: "A", 18: "A", 19: "A", 20: "C", 21: "B", 22: "A",
        23: "A", 24: "A", 25: "B", 26: "A", 27: "A", 28: "C", 29: "B",
        30: "B", 31: "A", 32: "A", 33: "B", 34: "B", 35: "A", 36: "A",
        37: "A", 38: "A", 39: "A", 40: "A", 41: "B", 42: "C", 43: "A",
        44: "A", 45: "A", 46: "A", 47: "A", 48: "A", 49: "A", 50: "A",
    },
    "Kimyo": {
        question_number: "A"
        for question_number in range(1, 50)
        if question_number != 49
    },
}

QUESTION_LINE = re.compile(r"^\s*(\d+)\.\s*(.*)$")
OPTION_LINE = re.compile(r"^\s*([A-D])\)\s*(.*)$")
CHAPTER_LINE = re.compile(r"^\s*\d+\s*-\s*BOB\b", re.IGNORECASE)
ANSWER_LINE = re.compile(r"^\s*Javob\s*(?::|/)\s*([A-D])\b", re.IGNORECASE)
ANSWER_KEY_LINE = re.compile(r"\b(\d+)\s*[-:]\s*([A-D])\b", re.IGNORECASE)
ANSWER_KEY_MARKER = re.compile(
    r"(?:JAVOB(?:AR|LAR)?\s+KALITI|TESTLAR\s+JAVOBLARI\s+KALITI)",
    re.IGNORECASE,
)


def parse_questions(path: Path) -> dict[int, dict]:
    questions = {}
    current_question = None
    current_option = None

    for line in path.read_text(encoding="utf-8").splitlines():
        if ANSWER_KEY_MARKER.search(line):
            break

        question_match = QUESTION_LINE.match(line)
        option_match = OPTION_LINE.match(
            re.sub(r"^\s*Javob\s*/\s*", "", line, flags=re.IGNORECASE)
        )
        answer_match = ANSWER_LINE.match(line)

        if question_match:
            number = int(question_match.group(1))
            if number in questions:
                raise ValueError(f"{path}: duplicate question number {number}")
            questions[number] = {
                "question_text": question_match.group(2).strip(),
                "options": {},
            }
            current_question = number
            current_option = None
        elif option_match and current_question is not None:
            option = option_match.group(1).lower()
            if option in questions[current_question]["options"]:
                available_options = (
                    set("abcd") - set(questions[current_question]["options"])
                )
                if not available_options:
                    raise ValueError(
                        f"{path}: more than four options for question {current_question}"
                    )
                option = next(
                    candidate for candidate in "abcd" if candidate in available_options
                )
            questions[current_question]["options"][option] = option_match.group(2).strip()
            current_option = option
        elif answer_match:
            current_option = None
        elif (
            current_question is not None
            and current_option
            and line.strip()
            and line.strip() != "---"
            and not CHAPTER_LINE.match(line)
        ):
            questions[current_question]["options"][current_option] += "\n" + line.strip()
        elif line.strip() == "---" or CHAPTER_LINE.match(line):
            current_option = None

    return questions


def parse_answer_key(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8")
    marker = ANSWER_KEY_MARKER.search(text)
    if marker is None:
        raise ValueError(f"{path}: answer key section was not found")

    return {
        int(number): answer.lower()
        for number, answer in ANSWER_KEY_LINE.findall(text[marker.end() :])
    }


async def seed_closed_tests() -> None:
    await init_db()
    added_by_subject = {}

    async with async_session() as session:
        for subject, source_path in SOURCE_FILES.items():
            questions = parse_questions(source_path)
            source_answers = parse_answer_key(source_path)
            verified_answers = {
                **source_answers,
                **VERIFIED_ANSWERS.get(subject, {}),
            }
            missing_questions = set(questions) - set(verified_answers)
            if missing_questions:
                raise ValueError(
                    f"{source_path}: answer key missing for questions: {sorted(missing_questions)}"
                )

            added_count = 0
            for number in sorted(questions):
                answer = verified_answers[number]
                question = questions[number]
                options = question["options"]
                if set(options) != {"a", "b", "c", "d"}:
                    raise ValueError(
                        f"{source_path}: question {number} does not have exactly four options"
                    )
                if not question["question_text"]:
                    raise ValueError(f"{source_path}: question {number} has no question text")

                question_text = f"{number}. {question['question_text']}"
                existing = await session.scalar(
                    select(Test.id).where(
                        Test.subject == subject,
                        Test.question_text == question_text,
                    )
                )
                if existing is not None:
                    continue

                session.add(
                    Test(
                        subject=subject,
                        question_text=question_text,
                        question_type="single",
                        difficulty=1,
                        option_a=options["a"],
                        option_b=options["b"],
                        option_c=options["c"],
                        option_d=options["d"],
                        correct_answer=answer,
                        explanation="Javob mustaqil tekshirildi.",
                    )
                )
                added_count += 1

            added_by_subject[subject] = added_count

        await session.commit()

    for subject, count in added_by_subject.items():
        print(f"{subject}: {count} ta yangi test qo'shildi.")


if __name__ == "__main__":
    asyncio.run(seed_closed_tests())
