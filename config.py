"""
config.py — App-wide constants, language data, API wrappers.

Translation:  IndicTrans2  (ai4bharat/indictrans2-indic-en-1B  &  indictrans2-en-indic-1B)
LLM / reasoning / chatbot / proofreading:  OpenRouter (openai/gpt-4o-mini)
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# API credentials
# ─────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN", "")

# Surface missing-key warnings immediately in the terminal
if not OPENROUTER_API_KEY:
    print("⚠️  WARNING: OPENROUTER_API_KEY not set in .env")
if not HUGGING_FACE_TOKEN:
    print("⚠️  WARNING: HUGGING_FACE_TOKEN not set in .env")

# ─────────────────────────────────────────────
# OpenRouter (LLM only — NOT used for translation)
# ─────────────────────────────────────────────
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL    = "openai/gpt-4o-mini"   # namespaced form required on OpenRouter

# ─────────────────────────────────────────────
# IndicTrans2 model IDs  (loaded lazily in pipeline.py)
# ─────────────────────────────────────────────
INDICTRANS_INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-1B"   # Indic → English
INDICTRANS_EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-1B"   # English → Indic

# ─────────────────────────────────────────────
# IndicTrans2 — Flores-200 language codes
# https://github.com/AI4Bharat/IndicTrans2#supported-languages
# ─────────────────────────────────────────────
INDIC_LANG_CODE: dict[str, str] = {
    "Assamese":          "asm_Beng",
    "Bengali":           "ben_Beng",
    "Bodo":              "brx_Deva",
    "Dogri":             "dgo_Deva",
    "Gujarati":          "guj_Gujr",
    "Hindi":             "hin_Deva",
    "Kannada":           "kan_Knda",
    "Kashmiri":          "kas_Arab",
    "Konkani":           "kok_Deva",
    "Maithili":          "mai_Deva",
    "Malayalam":         "mal_Mlym",
    "Manipuri (Meitei)": "mni_Beng",
    "Marathi":           "mar_Deva",
    "Nepali":            "npi_Deva",
    "Odia":              "ory_Orya",
    "Punjabi":           "pan_Guru",
    "Sanskrit":          "san_Deva",
    "Santali":           "sat_Olck",
    "Sindhi":            "snd_Arab",
    "Tamil":             "tam_Taml",
    "Telugu":            "tel_Telu",
    "Urdu":              "urd_Arab",
    "English":           "eng_Latn",
}

# ─────────────────────────────────────────────
# 22 Official Indian Languages — UI metadata
# ─────────────────────────────────────────────
INDIAN_LANGUAGES: dict[str, dict] = {
    "Assamese":          {"code": "as-IN",  "script": "Bengali",    "flag": "🇮🇳"},
    "Bengali":           {"code": "bn-IN",  "script": "Bengali",    "flag": "🇮🇳"},
    "Bodo":              {"code": "brx-IN", "script": "Devanagari", "flag": "🇮🇳"},
    "Dogri":             {"code": "doi-IN", "script": "Devanagari", "flag": "🇮🇳"},
    "Gujarati":          {"code": "gu-IN",  "script": "Gujarati",   "flag": "🇮🇳"},
    "Hindi":             {"code": "hi-IN",  "script": "Devanagari", "flag": "🇮🇳"},
    "Kannada":           {"code": "kn-IN",  "script": "Kannada",    "flag": "🇮🇳"},
    "Kashmiri":          {"code": "ks-IN",  "script": "Arabic",     "flag": "🇮🇳"},
    "Konkani":           {"code": "kok-IN", "script": "Devanagari", "flag": "🇮🇳"},
    "Maithili":          {"code": "mai-IN", "script": "Devanagari", "flag": "🇮🇳"},
    "Malayalam":         {"code": "ml-IN",  "script": "Malayalam",  "flag": "🇮🇳"},
    "Manipuri (Meitei)": {"code": "mni-IN", "script": "Bengali",    "flag": "🇮🇳"},
    "Marathi":           {"code": "mr-IN",  "script": "Devanagari", "flag": "🇮🇳"},
    "Nepali":            {"code": "ne-IN",  "script": "Devanagari", "flag": "🇮🇳"},
    "Odia":              {"code": "or-IN",  "script": "Odia",       "flag": "🇮🇳"},
    "Punjabi":           {"code": "pa-IN",  "script": "Gurmukhi",   "flag": "🇮🇳"},
    "Sanskrit":          {"code": "sa-IN",  "script": "Devanagari", "flag": "🇮🇳"},
    "Santali":           {"code": "sat-IN", "script": "Ol Chiki",   "flag": "🇮🇳"},
    "Sindhi":            {"code": "sd-IN",  "script": "Arabic",     "flag": "🇮🇳"},
    "Tamil":             {"code": "ta-IN",  "script": "Tamil",      "flag": "🇮🇳"},
    "Telugu":            {"code": "te-IN",  "script": "Telugu",     "flag": "🇮🇳"},
    "Urdu":              {"code": "ur-PK",  "script": "Nastaliq",   "flag": "🇮🇳"},
}

LANG_NAMES: list[str] = list(INDIAN_LANGUAGES.keys())

# ─────────────────────────────────────────────
# CSS Styles
# ─────────────────────────────────────────────
APP_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&family=Noto+Sans+Devanagari&family=Noto+Sans+Tamil&family=Noto+Sans+Bengali&display=swap" rel="stylesheet">
<style>
    .chat-message-user {
        background: #DCF8C6;
        padding: 10px 14px;
        border-radius: 18px 18px 4px 18px;
        margin: 6px 0;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
        color: #000;
    }
    .chat-message-bot {
        background: #F1F0F0;
        padding: 10px 14px;
        border-radius: 18px 18px 18px 4px;
        margin: 6px 0;
        max-width: 80%;
        color: #000;
    }
    .pivot-stage {
        background: #f8f9fa;
        border-left: 4px solid #4CAF50;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin: 6px 0;
        font-size: 14px;
        color: #333;
    }
    .pivot-stage-label {
        font-weight: bold;
        color: #4CAF50;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .error-bound {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        margin: 4px 0;
    }
</style>
"""

# ─────────────────────────────────────────────
# OpenRouter API wrapper  (LLM calls ONLY)
# ─────────────────────────────────────────────
def call_openrouter(
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 800,
    retries: int = 2,
    timeout: int = 60,
):
    """Call the OpenRouter chat completions endpoint with retry logic.

    Used ONLY for: language detection, pivot reasoning, proofreading, chatbot.
    All translation is handled by IndicTrans2 (see pipeline.py).
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    for attempt in range(retries):
        try:
            resp = requests.post(
                OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"].strip(), None
            else:
                if attempt == retries - 1:
                    return None, f"❌ OpenRouter {resp.status_code}: {resp.text[:200]}"
            time.sleep(1)
        except requests.exceptions.Timeout:
            time.sleep(1)
        except Exception as exc:
            if attempt == retries - 1:
                return None, f"❌ Request error: {exc}"
            time.sleep(1)
    return None, "❌ OpenRouter API call failed after retries."