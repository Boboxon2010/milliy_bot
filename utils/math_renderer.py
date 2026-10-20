import io
import re
import textwrap
import logging
from collections.abc import Callable
from threading import Lock

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile

_RENDER_LOCK = Lock()


_FUNCTION_COMMANDS = {
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "cot": r"\cot",
    "ln": r"\ln",
    "log": r"\log",
}


def _format_math_functions(expression: str) -> str:
    return re.sub(
        r"(?<![A-Za-z])(?:sin|cos|tan|cot|ln|log)\(([^()]*)\)",
        lambda match: (
            f"{_FUNCTION_COMMANDS[match.group(0).split('(')[0]]}"
            rf"\left({match.group(1)}\right)"
        ),
        expression,
    )


def _format_plain_segment(
    text: str,
    register_math: Callable[[str], str],
) -> str:
    text = re.sub(
        r"\b([A-Za-z0-9]+)\s*/\s*(?:sqrt|√)\(([^()]*)\)",
        lambda match: register_math(
            rf"\frac{{{match.group(1)}}}"
            rf"{{\sqrt{{{match.group(2).replace('*', r'\cdot')}}}}}"
        ),
        text,
    )
    text = re.sub(
        r"((?:sin|cos|tan|cot|ln|log)\([^()]*\))\s*/\s*"
        r"(\((?:[^()]|\([^()]*\))*\))",
        lambda match: register_math(
            rf"\frac{{{_format_math_functions(match.group(1))}}}"
            rf"{{{_format_math_functions(match.group(2)[1:-1])}}}"
        ),
        text,
    )
    text = re.sub(
        r"\(([^()]*)\)\s*/\s*\(([^()]*)\)",
        lambda match: register_math(
            rf"\frac{{{match.group(1)}}}{{{match.group(2)}}}"
        ),
        text,
    )
    text = re.sub(
        r"∛\(([^()]*)\)",
        lambda match: register_math(rf"\sqrt[3]{{{match.group(1)}}}"),
        text,
    )
    text = re.sub(
        r"(?<!\\)\\int_(\{[^{}]+\}|[^\s^]+)\^(\{[^{}]+\}|[^\s,;.)]+)",
        lambda match: register_math(
            rf"\int_{{{match.group(1).strip('{}')}}}"
            rf"^{{{match.group(2).strip('{}')}}}"
        ),
        text,
    )
    text = re.sub(
        r"\\sqrt\{([^{}]+)\}",
        lambda match: register_math(rf"\sqrt{{{match.group(1)}}}"),
        text,
    )
    text = re.sub(
        r"\\frac\{([^{}]+)\}\{([^{}]+)\}",
        lambda match: register_math(
            rf"\frac{{{match.group(1)}}}{{{match.group(2)}}}"
        ),
        text,
    )
    text = re.sub(
        r"(?<![A-Za-z])log_([A-Za-z0-9]+|\([^()]*\)|\{[^{}]*\})",
        lambda match: register_math(
            rf"\log_{{{re.sub(r'([A-Za-z0-9]+)\^([A-Za-z0-9]+)', r'\1^{\2}', match.group(1).strip('(){}'))}}}"
        ),
        text,
    )
    text = re.sub(
        r"(?<![A-Za-z])(?:sqrt|√)\(([^()]*)\)",
        lambda match: register_math(
            rf"\sqrt{{{match.group(1).replace('*', r'\cdot')}}}"
        ),
        text,
    )

    text = re.sub(
        r"(?<![A-Za-z])(?:sin|cos|tan|cot|ln|log)\(([^()]*)\)",
        lambda match: register_math(_format_math_functions(match.group(0))),
        text,
    )
    text = re.sub(
        r"(?<![A-Za-z0-9$])\(([^()]*)\)\^([A-Za-z0-9]+)",
        lambda match: register_math(
            rf"\left({match.group(1)}\right)^{{{match.group(2)}}}"
        ),
        text,
    )

    def format_index_or_power(match: re.Match[str]) -> str:
        base, subscript, exponent = match.groups()
        if subscript is None and exponent is None:
            return match.group(0)
        formatted = base
        if subscript is not None:
            formatted += rf"_{{{subscript}}}"
        if exponent is not None:
            formatted += rf"^{{{exponent}}}"
        return register_math(formatted)

    text = re.sub(
        r"(?<![A-Za-z0-9$])([A-Za-z0-9]+)(?:_([A-Za-z0-9]+))?(?:\^([A-Za-z0-9]+))?",
        format_index_or_power,
        text,
    )
    text = re.sub(
        r"(?<![A-Za-z0-9$])([A-Za-z0-9]+)\s*/\s*([A-Za-z0-9]+)(?![A-Za-z0-9])",
        lambda match: register_math(
            rf"\frac{{{match.group(1)}}}{{{match.group(2)}}}"
        ),
        text,
    )
    tex_commands = {
        r"\pi": r"\pi",
        r"\infty": r"\infty",
        r"\times": r"\times",
        r"\cdot": r"\cdot",
        r"\le": r"\leq",
        r"\leq": r"\leq",
        r"\ge": r"\geq",
        r"\geq": r"\geq",
        r"\neq": r"\neq",
        r"\pm": r"\pm",
    }
    for command in sorted(tex_commands, key=len, reverse=True):
        latex = tex_commands[command]
        text = text.replace(command, register_math(latex))
    text = re.sub(
        r"(?<!\$)\s*\*\s*(?!\$)",
        lambda match: f" {register_math(r'\cdot')} ",
        text,
    )
    math_symbols = {
        "×": r"\times",
        "÷": r"\div",
        "≤": r"\leq",
        "≥": r"\geq",
        "≠": r"\neq",
        "∞": r"\infty",
        "π": r"\pi",
        "∫": r"\int",
    }
    for symbol, latex in math_symbols.items():
        text = text.replace(symbol, register_math(latex))
    text = re.sub(
        r"(?<![A-Za-z])pi(?![A-Za-z])",
        lambda _: register_math(r"\pi"),
        text,
    )
    return text


def format_math_text(text: str) -> str:
    """Format common plain-text and TeX-style math as Matplotlib math expressions."""
    text = re.sub(r"^\s*\d+\.\s*", "", text)
    segments = re.split(r"(\$[^$]*\$)", text)
    math_expressions: list[str] = []

    def register_math(expression: str) -> str:
        marker = f"\ue000{chr(0xE100 + len(math_expressions))}\ue001"
        math_expressions.append(expression)
        return marker

    formatted = "".join(
        segment if segment.startswith("$") and segment.endswith("$")
        else _format_plain_segment(segment, register_math)
        for segment in segments
    )
    for index, expression in enumerate(math_expressions):
        marker = f"\ue000{chr(0xE100 + index)}\ue001"
        formatted = formatted.replace(marker, f"${expression}$")
    return formatted


def render_math_to_image(question_text: str) -> BufferedInputFile:
    """
    Masala matni yoki misolning matematik ko'rinishini yuqori sifatli rasmga aylantiradi.
    Har qanday xatolikda avtomatik oddiy matn ko'rinishiga o'tib, rasmni kafolatli yaratadi.
    """
    clean_text = (question_text or "").strip()
    
    # 1. Matnni formatlash
    try:
        formatted_text = format_math_text(clean_text)
    except Exception:
        formatted_text = clean_text

    wrapped_text = "\n".join(
        line
        for paragraph in formatted_text.splitlines() or [""]
        for line in (textwrap.wrap(
            paragraph,
            width=70,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""])
    )
    line_count = max(1, wrapped_text.count("\n") + 1)
    figure_height = max(1.6, 0.45 * line_count + 0.6)

    with _RENDER_LOCK, matplotlib.rc_context({
        "mathtext.fontset": "stix",
        "font.family": "STIXGeneral",
    }):
        fig, ax = plt.subplots(figsize=(11, figure_height))
        ax.axis("off")
        
        try:
            # Mathtext bilan render qilishga urinish
            ax.text(
                0.03,
                0.94,
                wrapped_text,
                fontsize=18,
                linespacing=1.5,
                wrap=True,
                va="top",
                ha="left",
                color="#111111",
            )
        except Exception:
            # Agar mathtext xatosi bersa, oddiy xavfsiz matn bilan render qilish
            ax.clear()
            ax.axis("off")
            plain_wrapped = "\n".join(
                line
                for paragraph in clean_text.splitlines() or [""]
                for line in (textwrap.wrap(paragraph, width=70) or [""])
            )
            plain_wrapped = plain_wrapped.replace("\\", r"\\").replace("$", r"\$")
            ax.text(
                0.03,
                0.94,
                plain_wrapped,
                fontsize=18,
                linespacing=1.5,
                wrap=True,
                va="top",
                ha="left",
                color="#111111",
            )

        fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

        image_buffer = io.BytesIO()
        try:
            try:
                fig.savefig(
                    image_buffer,
                    format="png",
                    dpi=180,
                    bbox_inches="tight",
                    pad_inches=0.25,
                    facecolor="white",
                )
            except Exception:
                logging.warning(
                    "Math rendering failed during PNG export; using plain text.",
                    exc_info=True,
                )
                image_buffer = io.BytesIO()
                ax.clear()
                ax.axis("off")
                plain_wrapped = "\n".join(
                    line
                    for paragraph in clean_text.splitlines() or [""]
                    for line in (textwrap.wrap(paragraph, width=70) or [""])
                )
                plain_wrapped = plain_wrapped.replace("\\", r"\\").replace("$", r"\$")
                ax.text(
                    0.03,
                    0.94,
                    plain_wrapped,
                    fontsize=18,
                    linespacing=1.5,
                    wrap=True,
                    va="top",
                    ha="left",
                    color="#111111",
                )
                fig.savefig(
                    image_buffer,
                    format="png",
                    dpi=180,
                    bbox_inches="tight",
                    pad_inches=0.25,
                    facecolor="white",
                )
        finally:
            plt.close(fig)

    return BufferedInputFile(image_buffer.getvalue(), filename="question.png")
