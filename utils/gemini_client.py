import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Modellar ustuvorligi va fallback ro'yxati
DEFAULT_FALLBACK_MODELS = [
    GEMINI_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
]

# Takroriy modellarni olib tashlash
MODELS_TO_TRY = []
for m in DEFAULT_FALLBACK_MODELS:
    if m and m not in MODELS_TO_TRY:
        MODELS_TO_TRY.append(m)

http_options = types.HttpOptions(
    retry_options=types.HttpRetryOptions(
        attempts=3,
        initial_delay=1,
        max_delay=4,
        exp_base=2,
        jitter=0.2,
    )
)

client = (
    genai.Client(api_key=GEMINI_API_KEY, http_options=http_options)
    if GEMINI_API_KEY
    else None
)


def generate_text(prompt: str, json_mode: bool = False) -> str:
    """Sinxron matn yaratish (fallback modellari bilan)."""
    if client is None:
        raise RuntimeError("GEMINI_API_KEY topilmadi. .env faylini tekshiring.")

    config = None
    if json_mode:
        config = types.GenerateContentConfig(response_mime_type="application/json")

    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            if response.text:
                return response.text
        except (errors.APIError, Exception) as exc:
            logging.warning("Model %s da xatolik yuz berdi: %s. Zaxira model tekshirilmoqda...", model_name, exc)
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise ValueError("Gemini API bo'sh javob qaytardi.")


async def generate_text_async(prompt: str, json_mode: bool = False, system_instruction: str | None = None) -> str:
    """Asinxron matn yaratish (fallback modellari bilan)."""
    if client is None:
        raise RuntimeError("GEMINI_API_KEY topilmadi. .env faylini tekshiring.")

    config_kwargs = {}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            if response.text:
                return response.text
        except (errors.APIError, Exception) as exc:
            logging.warning("Model %s da xatolik yuz berdi: %s. Zaxira model tekshirilmoqda...", model_name, exc)
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise ValueError("Gemini API bo'sh javob qaytardi.")
