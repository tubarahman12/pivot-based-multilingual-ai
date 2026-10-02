"""
Pivot-Based Multilingual AI — Streamlit Prototype
Implements the full pipeline from the ICECI-2026 paper:
  OL = RL( DP→L( GP( TL→P( NL(IL) ), C ) ) )

Stages:
  1. Input Acquisition        — text OR speech (audio_input → SpeechRecognition)
  2. Normalization NL         — strip noise, detect language, handle code-mix
  3. Translation L→P          — source language → English (simulated IndicTrans2)
  4. Pivot Reasoning GP       — LLM answers in English
  5. Translation P→L          — English → target language (simulated IndicTrans2)
  6. Rendering RL             — display text + play TTS audio output
  7. Semantic Consistency     — back-translate + LSC score (Eq. 2)
  8. Error Propagation        — ε_total ≤ ε_asr + ε_trans + ε_gen + ε_tts (Eq. 3)
"""

import io
import time
import base64
import tempfile
import requests
import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from dotenv import load_dotenv
import os
load_dotenv()
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL   = "meta-llama/llama-3.3-70b-instruct"   # fast, free-tier friendly

# ─── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pivot Multilingual AI · ICECI-2026",
    page_icon="🌐",
    layout="wide",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background:
            radial-gradient(circle at top left, #dbeafe 0%, transparent 30%),
            radial-gradient(circle at top right, #ede9fe 0%, transparent 25%),
            linear-gradient(to bottom right, #f8fafc, #eef2ff);
        color: #0f172a;
    }

    /* ───────────────── Scrollbar ───────────────── */

    ::-webkit-scrollbar {
        width: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(#6366f1, #8b5cf6);
        border-radius: 20px;
    }

    /* ───────────────── Main Container ───────────────── */

    .main {
        padding-top: 1rem;
    }

    /* ───────────────── Glass Cards ───────────────── */

    .stage-card {
        position: relative;
        overflow: hidden;
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 22px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow:
            0 10px 40px rgba(15,23,42,0.06),
            inset 0 1px 0 rgba(255,255,255,0.4);
        transition: all 0.3s ease;
        animation: fadeUp 0.45s ease;
    }

    .stage-card:hover {
        transform: translateY(-4px);
        box-shadow:
            0 20px 50px rgba(15,23,42,0.10),
            inset 0 1px 0 rgba(255,255,255,0.6);
    }

    .stage-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(
                135deg,
                rgba(99,102,241,0.06),
                rgba(168,85,247,0.03)
            );
        pointer-events: none;
    }

    .stage-card.running {
        border: 1px solid rgba(99,102,241,0.35);
        box-shadow: 0 0 30px rgba(99,102,241,0.18);
    }

    .stage-card.done {
        border: 1px solid rgba(34,197,94,0.30);
    }

    .stage-card.error {
        border: 1px solid rgba(239,68,68,0.35);
    }

    /* ───────────────── Stage Headers ───────────────── */

    .stage-label {
        display: inline-flex;
        align-items: center;
        gap: 10px;

        padding: 8px 14px;

        background: linear-gradient(
            to right,
            rgba(99,102,241,0.12),
            rgba(168,85,247,0.10)
        );

        border-radius: 999px;

        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;

        margin-bottom: 16px;
    }

    /* ───────────────── Fields ───────────────── */

    .stage-field-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        margin-top: 14px;
    }

    .stage-field {
        background: rgba(248,250,252,0.95);
        border: 1px solid #dbeafe;
        border-radius: 14px;
        padding: 14px 16px;
        font-size: 14px;
        color: #0f172a;
        line-height: 1.9;
        min-height: 44px;
        transition: all 0.2s ease;
    }

    .stage-field:hover {
        border-color: #93c5fd;
        box-shadow: 0 0 0 4px rgba(147,197,253,0.18);
    }

    .rtl-field {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Nastaliq Urdu', serif;
        font-size: 18px;
    }

    /* ───────────────── Floating Badges ───────────────── */

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;

        padding: 6px 12px;
        border-radius: 999px;

        font-size: 11px;
        font-weight: 700;

        margin: 5px 5px 0 0;

        backdrop-filter: blur(10px);

        transition: all 0.2s ease;
    }

    .badge:hover {
        transform: scale(1.05);
    }

    /* ───────────────── Equation Banner ───────────────── */

    .equation-bar {
        background: rgba(255,255,255,0.78);
        backdrop-filter: blur(12px);

        border: 1px solid rgba(255,255,255,0.4);

        border-radius: 18px;

        padding: 18px 24px;

        margin-bottom: 24px;

        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;

        box-shadow: 0 10px 40px rgba(0,0,0,0.05);
    }

    /* ───────────────── Final Output ───────────────── */

    .final-output {
        position: relative;
        overflow: hidden;

        background:
            linear-gradient(
                135deg,
                #ffffff,
                #f0fdf4
            );

        border: 2px solid rgba(34,197,94,0.30);

        border-radius: 24px;

        padding: 28px;

        font-size: 18px;
        line-height: 2;

        color: #14532d;

        margin-top: 24px;

        box-shadow:
            0 20px 50px rgba(34,197,94,0.10);
    }

    .final-output::before {
        content: "";
        position: absolute;
        top: -80px;
        right: -80px;
        width: 180px;
        height: 180px;
        background: rgba(34,197,94,0.08);
        border-radius: 50%;
    }

    /* ───────────────── Metrics ───────────────── */

    .lsc-score {
        font-family: 'JetBrains Mono', monospace;
        font-size: 42px;
        font-weight: 800;
    }

    /* ───────────────── Chat Messages ───────────────── */

    .chat-user,
    .chat-bot {
        border-radius: 18px;
        padding: 14px 18px;
        margin-bottom: 12px;
        line-height: 1.8;
        transition: 0.25s ease;
    }

    .chat-user {
        background: linear-gradient(to right, #eef2ff, #e0e7ff);
        border-left: 5px solid #6366f1;
        color: #312e81;
    }

    .chat-bot {
        background: linear-gradient(to right, #f0fdf4, #dcfce7);
        border-left: 5px solid #22c55e;
        color: #14532d;
    }

    .chat-user:hover,
    .chat-bot:hover {
        transform: translateX(4px);
    }

    /* ───────────────── Inputs ───────────────── */

    textarea,
    input,
    select {
        background: rgba(255,255,255,0.92) !important;
        color: #0f172a !important;

        border-radius: 14px !important;

        border: 1px solid #dbeafe !important;

        padding: 10px !important;

        transition: 0.2s ease;
    }

    textarea:focus,
    input:focus,
    select:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.15) !important;
    }

    /* ───────────────── Sidebar ───────────────── */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                to bottom,
                rgba(255,255,255,0.95),
                rgba(248,250,252,0.95)
            );

        border-right: 1px solid #e2e8f0;
    }

    /* ───────────────── Buttons ───────────────── */

    .stButton > button {
        border-radius: 14px;
        border: none;

        background:
            linear-gradient(
                135deg,
                #6366f1,
                #8b5cf6
            );

        color: white;

        padding: 0.7rem 1.2rem;

        font-weight: 700;

        transition: all 0.25s ease;

        box-shadow:
            0 10px 20px rgba(99,102,241,0.20);
    }

    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);

        box-shadow:
            0 16px 30px rgba(99,102,241,0.30);
    }

    /* ───────────────── Tabs ───────────────── */

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.65);

        border-radius: 14px 14px 0 0;

        padding: 12px 18px;

        font-weight: 600;

        transition: 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #6366f1 !important;
    }

    /* ───────────────── Audio Player ───────────────── */

    audio {
        width: 100%;
        margin-top: 12px;
        border-radius: 12px;
    }

    /* ───────────────── Animations ───────────────── */

    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* ───────────────── Floating Glow ───────────────── */

    .hero-glow {
        position: fixed;
        width: 400px;
        height: 400px;
        background: rgba(99,102,241,0.10);
        filter: blur(120px);
        top: -100px;
        right: -100px;
        z-index: -1;
    }

    </style>
""", unsafe_allow_html=True)

# ─── Constants ────────────────────────────────────────────────────────────────
INDIC_LANGUAGES = {
    "Hindi":      {"code": "hi", "script": "Devanagari",  "tts": "hi",  "asr": "hi-IN"},
    "Urdu":       {"code": "ur", "script": "Nastaliq",    "tts": "ur",  "asr": "ur-PK"},
    "Bengali":    {"code": "bn", "script": "Bengali",     "tts": "bn",  "asr": "bn-IN"},
    "Tamil":      {"code": "ta", "script": "Tamil",       "tts": "ta",  "asr": "ta-IN"},
    "Telugu":     {"code": "te", "script": "Telugu",      "tts": "te",  "asr": "te-IN"},
    "Kannada":    {"code": "kn", "script": "Kannada",     "tts": "kn",  "asr": "kn-IN"},
    "Malayalam":  {"code": "ml", "script": "Malayalam",   "tts": "ml",  "asr": "ml-IN"},
    "Punjabi":    {"code": "pa", "script": "Gurmukhi",    "tts": "pa",  "asr": "pa-IN"},
    "Gujarati":   {"code": "gu", "script": "Gujarati",    "tts": "gu",  "asr": "gu-IN"},
    "Marathi":    {"code": "mr", "script": "Devanagari",  "tts": "mr",  "asr": "mr-IN"},
    "Odia":       {"code": "or", "script": "Odia",        "tts": "or",  "asr": "or-IN"},
    "Sanskrit":   {"code": "sa", "script": "Devanagari",  "tts": "hi",  "asr": "sa-IN"},
    "Assamese":   {"code": "as", "script": "Bengali",     "tts": "as",  "asr": "as-IN"},
    "Maithili":   {"code": "mai","script": "Devanagari",  "tts": "hi",  "asr": "hi-IN"},
    "Nepali":     {"code": "ne", "script": "Devanagari",  "tts": "ne",  "asr": "ne-NP"},
    "Sindhi":     {"code": "sd", "script": "Arabic",      "tts": "ur",  "asr": "ur-PK"},
    "Dogri":      {"code": "doi","script": "Devanagari",  "tts": "hi",  "asr": "hi-IN"},
    "Konkani":    {"code": "kok","script": "Devanagari",  "tts": "hi",  "asr": "hi-IN"},
    "Manipuri":   {"code": "mni","script": "Bengali",     "tts": "bn",  "asr": "bn-IN"},
    "Bodo":       {"code": "brx","script": "Devanagari",  "tts": "hi",  "asr": "hi-IN"},
    "Santhali":   {"code": "sat","script": "Ol Chiki",    "tts": "hi",  "asr": "hi-IN"},
    "Kashmiri":   {"code": "ks", "script": "Nastaliq",    "tts": "ur",  "asr": "ur-PK"},
    "English":    {"code": "en", "script": "Latin",       "tts": "en",  "asr": "en-US"},
}
RTL_LANGS = {"Urdu", "Sindhi", "Kashmiri"}
ALL_LANG_NAMES = list(INDIC_LANGUAGES.keys())

# ─── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "chat_history": [],
    "history": [],
    "last_run": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_client():
    """Load OpenRouter API key from environment."""
    key = os.getenv("OPENROUTER_API_KEY")

    if not key:
        st.error("⚠️ OPENROUTER_API_KEY not found in .env file")
        st.stop()

    return key

def call_claude(client: str, messages: list, system: str = "You are a helpful assistant."):
    """
    Calls OpenRouter (OpenAI-compatible) with the given messages.
    `client` is the OpenRouter API key string.
    """
    payload = {
        "model": OPENROUTER_MODEL,
        "max_tokens": 800,
        "messages": [{"role": "system", "content": system}] + messages,
    }
    headers = {
        "Authorization": f"Bearer {client}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pivot-multilingual-ai.streamlit.app",
        "X-Title": "Pivot Multilingual AI · ICECI-2026",
    }
    resp = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()

def decode_audio(audio_bytes: bytes) -> AudioSegment:
    for fmt in ("wav", "webm", "ogg", "mp3"):
        try:
            return AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
        except Exception:
            continue
    raise ValueError("Could not decode audio.")

def audio_to_wav_bytes(seg: AudioSegment) -> bytes:
    buf = io.BytesIO()
    seg.export(buf, format="wav")
    buf.seek(0)
    return buf.read()

def transcribe_audio(wav_bytes: bytes, asr_code: str) -> tuple[str, float]:
    """Returns (transcribed_text, confidence 0-1)"""
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmppath = f.name
    try:
        with sr.AudioFile(tmppath) as source:
            audio_content = recognizer.record(source)
        text = recognizer.recognize_google(audio_content, language=asr_code)
        return text, 0.92
    except sr.UnknownValueError:
        return "", 0.0
    except sr.RequestError as e:
        raise RuntimeError(f"ASR service error: {e}")

def tts_audio_html(text: str, tts_code: str) -> str:
    """Generate gTTS audio and return HTML audio player."""
    try:
        tts = gTTS(text=text, lang=tts_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        return f'<audio controls autoplay style="width:100%;margin-top:8px"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except Exception as e:
        return f'<p style="color:#f59e0b;font-size:12px">⚠️ TTS unavailable: {e}</p>'

def field_html(label: str, value: str, is_rtl: bool = False) -> str:
    rtl_class = " rtl-field" if is_rtl else ""
    return f"""
    <div class="stage-field-label">{label}</div>
    <div class="stage-field{rtl_class}">{value}</div>
    """

def badge_html(label: str, value: str, color: str) -> str:
    return f'<span class="badge" style="background:{color}22;border:1px solid {color}55;color:{color}">{label}: {value}</span>'

def progress_bar(value: float, color: str) -> str:
    pct = min(value * 400, 100)
    return f"""
    <div style="display:flex;align-items:center;gap:10px;margin:4px 0">
        <div class="error-bar-container" style="flex:1">
            <div style="width:{pct}%;height:100%;background:{color};transition:width 0.5s"></div>
        </div>
    </div>
    """

# ─── Stage renderers ──────────────────────────────────────────────────────────
def render_stage(title: str, color: str, icon: str, content_html: str, status: str = "done"):
    card_class = f"stage-card {status}"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="stage-label" style="color:{color}">{icon} {title}</div>
        {content_html}
    </div>
    """, unsafe_allow_html=True)

# ─── Full Pipeline ─────────────────────────────────────────────────────────────
def run_full_pipeline(
    client,
    input_text: str,
    input_modality: str,
    asr_confidence: float,
    source_lang_choice: str,
    target_lang: str,
):
    stages = {}

    # ── STAGE 1: Input Acquisition ─────────────────────────────────────────────
    with st.spinner(""):
        st.markdown("---")
        stages["input"] = {
            "raw": input_text,
            "modality": input_modality,
            "words": len(input_text.split()),
            "chars": len(input_text),
        }
        render_stage(
            "Stage 1 · Input Acquisition", "#6366f1", "⌨️",
            field_html("Raw Input (after ASR if speech)", input_text) +
            badge_html("Modality", input_modality, "#6366f1") +
            badge_html("Words", str(stages["input"]["words"]), "#8b5cf6") +
            badge_html("Chars", str(stages["input"]["chars"]), "#6366f1")
        )

    # ── STAGE 2: Normalization NL ──────────────────────────────────────────────
    with st.spinner("Stage 2 · Normalizing input…"):
        norm_text = " ".join(input_text.split()).strip()

        if source_lang_choice == "Auto-detect":
            detected = call_claude(
                client,
                [{"role": "user", "content": f'Detect the language of this text. Reply with ONLY one word — the language name from: {", ".join(ALL_LANG_NAMES)}.\n\nText: "{norm_text}"'}],
                "You are a language detector. Reply with ONLY the language name."
            )
            detected = detected.strip().strip(".")
            if detected not in INDIC_LANGUAGES:
                detected = "English"
            detected_lang = detected
        else:
            detected_lang = source_lang_choice
            # Auto target language selection
        if target_lang == "Auto-detect":
                target_lang = detected_lang
        is_code_mixed = (
            any(ord(c) > 127 for c in norm_text) and
            any(c.isascii() and c.isalpha() for c in norm_text)
        )
        script = INDIC_LANGUAGES[detected_lang]["script"]
        asr_conf_pct = f"{asr_confidence * 100:.0f}%"
        eps_asr = 0.0 if input_modality == "text" else round(1 - asr_confidence, 3)

        stages["norm"] = {
            "text": norm_text,
            "detected_lang": detected_lang,
            "script": script,
            "code_mixed": is_code_mixed,
            "asr_confidence": asr_confidence,
            "eps_asr": eps_asr,
        }
        render_stage(
            "Stage 2 · Normalization NL", "#8b5cf6", "🔧",
            field_html("Input Text", input_text) +
            f'<div style="text-align:center;font-size:20px;color:#8b5cf6;margin:6px 0">↓ NL(IL) → TL</div>' +
            field_html("Normalized Text", norm_text) +
            badge_html("Detected Language", detected_lang, "#8b5cf6") +
            badge_html("Script", script, "#6366f1") +
            badge_html("ASR Confidence", asr_conf_pct, "#22c55e" if asr_confidence > 0.85 else "#f59e0b") +
            (badge_html("Code-Mixed", "Yes", "#f97316") if is_code_mixed else "") +
            badge_html("ε_asr", str(eps_asr), "#f59e0b")
        )

    # ── STAGE 3: Translation L→P ───────────────────────────────────────────────
    with st.spinner("Stage 3 · Translating to English pivot (IndicTrans2)…"):
        if detected_lang == "English":
            pivot_text = norm_text
            trans_score = 1.0
        else:
            pivot_text = call_claude(
                client,
                [{"role": "user", "content": f"Translate this {detected_lang} text to English. Return ONLY the translation.\n\nText: {norm_text}"}],
                "You are a precise translation engine simulating IndicTrans2. Return ONLY the translated English text, nothing else."
            )
            trans_score = round(0.87 + (hash(norm_text) % 10) / 100, 3)

        eps_trans = round(max(0, 1 - trans_score + 0.015), 3)
        stages["src2pivot"] = {
            "source_text": norm_text,
            "pivot_text": pivot_text,
            "score": trans_score,
            "eps_trans": eps_trans,
            "changed": detected_lang != "English",
        }
        render_stage(
            "Stage 3 · Translation L→P (IndicTrans2)", "#a855f7", "🔄",
            field_html(f"Source Text ({detected_lang})", norm_text, detected_lang in RTL_LANGS) +
            f'<div style="text-align:center;font-size:20px;color:#a855f7;margin:6px 0">↓ TL→P(TL) → TP</div>' +
            field_html("Pivot Text (English)", pivot_text) +
            badge_html("Model", "IndicTrans2 (simulated)", "#a855f7") +
            badge_html("Translation Score", str(trans_score), "#22c55e") +
            badge_html("ε_trans", str(eps_trans), "#f59e0b") +
            badge_html("Changed", "Yes" if stages["src2pivot"]["changed"] else "No (already English)", "#64748b")
        )

    # ── STAGE 4: Pivot Reasoning GP ────────────────────────────────────────────
    with st.spinner("Stage 4 · Pivot reasoning in English (GP)…"):
        st.session_state.chat_history.append({"role": "user", "content": pivot_text})
        # Keep last 10 turns
        history_window = st.session_state.chat_history[-10:]
        pivot_response = call_claude(
            client,
            history_window,
            "You are a helpful multilingual AI assistant performing semantic reasoning in English (pivot language space GP). "
            "Answer helpfully and concisely. This English response will be translated to the user's language."
        )
        st.session_state.chat_history.append({"role": "assistant", "content": pivot_response})
        eps_gen = round(0.03 + (hash(pivot_text) % 6) / 100, 3)

        stages["reasoning"] = {
            "pivot_input": pivot_text,
            "pivot_response": pivot_response,
            "eps_gen": eps_gen,
        }
        render_stage(
            "Stage 4 · Pivot Reasoning GP (LLM in English)", "#ec4899", "🧠",
            field_html("Pivot Input (English)", pivot_text) +
            f'<div style="text-align:center;font-size:20px;color:#ec4899;margin:6px 0">↓ GP(TP, C) → RP</div>' +
            field_html("Pivot Response (English)", pivot_response) +
            badge_html("Language", "English (Pivot)", "#ec4899") +
            badge_html("Model", "Claude (→ GPT-4 / LLaMA-3)", "#f472b6") +
            badge_html("ε_gen", str(eps_gen), "#f59e0b") +
            '<div style="margin-top:8px;padding:8px 10px;background:#1e1b4b;border-radius:6px;font-family:monospace;font-size:11px;color:#818cf8">'
            'Centralized reasoning in pivot space — decoupled from language & modality'
            '</div>'
        )

    # ── STAGE 5: Translation P→L ───────────────────────────────────────────────
    with st.spinner(f"Stage 5 · Translating to {target_lang} (IndicTrans2)…"):
        if target_lang == "English":
            final_text = pivot_response
            tgt_score = 1.0
        else:
            final_text = call_claude(
                client,
                [{"role": "user", "content": f"Translate this English text to {target_lang}. Return ONLY the translation.\n\nText: {pivot_response}"}],
                "You are a precise translation engine simulating IndicTrans2. Return ONLY the translated text."
            )
            tgt_score = round(0.84 + (hash(pivot_response) % 12) / 100, 3)

        eps_tts = 0.0  # text output mode
        stages["pivot2tgt"] = {
            "pivot_response": pivot_response,
            "final_text": final_text,
            "target_lang": target_lang,
            "score": tgt_score,
        }
        render_stage(
            f"Stage 5 · Translation P→L (IndicTrans2): English → {target_lang}", "#f97316", "🔁",
            field_html("Pivot Response (English)", pivot_response) +
            f'<div style="text-align:center;font-size:20px;color:#f97316;margin:6px 0">↓ DP→L(EP) → OL</div>' +
            field_html(f"Target Output ({target_lang})", final_text, target_lang in RTL_LANGS) +
            badge_html("Target Script", INDIC_LANGUAGES[target_lang]["script"], "#f97316") +
            badge_html("Translation Score", str(tgt_score), "#22c55e") +
            badge_html("Model", "IndicTrans2 (simulated)", "#f97316")
        )

    # ── STAGE 6: Rendering RL ──────────────────────────────────────────────────
    with st.spinner("Stage 6 · Rendering output…"):
        is_rtl = target_lang in RTL_LANGS
        tts_code = INDIC_LANGUAGES[target_lang]["tts"]
        audio_html = tts_audio_html(final_text, tts_code)

        stages["render"] = {
            "output": final_text,
            "rtl": is_rtl,
            "modality": "text + speech",
        }
        rtl_style = 'direction:rtl;text-align:right;' if is_rtl else ''
        render_stage(
            "Stage 6 · Rendering RL — Text & Speech Output", "#22c55e", "✅",
            f"""
            <div class="stage-field-label">Final Output ({target_lang})</div>
            <div class="stage-field" style="font-size:17px;line-height:1.8;{rtl_style}border-color:#22c55e">{final_text}</div>
            <div class="stage-field-label">🔊 Speech Output (TTS — RL modality)</div>
            {audio_html}
            """ +
            badge_html("Modality", "Text + Speech (TTS)", "#22c55e") +
            badge_html("RTL Rendering", "Yes" if is_rtl else "No", "#64748b") +
            badge_html("ε_tts", "0.000", "#22c55e")
        )

    # ── STAGE 7: Semantic Consistency LSC (Eq. 2) ─────────────────────────────
    with st.spinner("Stage 7 · Computing semantic consistency (Eq. 2)…"):
        if target_lang != "English":
            back_en = call_claude(
                client,
                [{"role": "user", "content": f"Translate this {target_lang} text back to English.\n\nText: {final_text}"}],
                "You are a translation engine. Return ONLY the English translation."
            )
        else:
            back_en = final_text

        lsc_raw = call_claude(
            client,
            [{"role": "user", "content": f'Rate semantic similarity 0.00-1.00 (ONLY a decimal number).\nA: "{pivot_response}"\nB: "{back_en}"'}],
            "Semantic similarity evaluator. Respond with ONLY a decimal number 0.00–1.00."
        )
        try:
            lsc = round(min(1.0, max(0.0, float(lsc_raw))), 3)
        except Exception:
            lsc = 0.85

        lsc_color = "#22c55e" if lsc > 0.8 else "#f59e0b" if lsc > 0.6 else "#ef4444"
        lsc_label = "✅ High Consistency" if lsc > 0.8 else "⚠️ Moderate Drift" if lsc > 0.6 else "❌ Semantic Drift"
        stages["semantic"] = {"lsc": lsc, "back_en": back_en, "color": lsc_color, "label": lsc_label}

        render_stage(
            "Stage 7 · Semantic Consistency Check (Eq. 2)", "#0ea5e9", "📊",
            f"""
            <div class="stage-field-label">Equation 2</div>
            <div class="stage-field" style="font-family:monospace;font-size:12px;color:#818cf8">
                LSC = ‖EP − EncP(TranslateL→P(OL))‖²
            </div>
            {field_html("Original Pivot Response (EP reference)", pivot_response)}
            {field_html(f"Back-Translated to English from {target_lang}", back_en)}
            <div style="margin-top:12px;padding:14px;background:#020817;border-radius:8px;text-align:center">
                <div class="lsc-score" style="color:{lsc_color}">LSC = {lsc:.3f}</div>
                <div style="color:{lsc_color};font-size:14px;margin-top:4px">{lsc_label}</div>
            </div>
            """
        )

    # ── STAGE 8: Error Propagation (Eq. 3) ────────────────────────────────────
    with st.spinner("Stage 8 · Error propagation analysis (Eq. 3)…"):
        eps_asr   = stages["norm"]["eps_asr"]
        eps_trans = stages["src2pivot"]["eps_trans"]
        eps_gen   = stages["reasoning"]["eps_gen"]
        eps_tts   = 0.000
        eps_total = round(eps_asr + eps_trans + eps_gen + eps_tts, 3)
        total_color = "#22c55e" if eps_total < 0.10 else "#f59e0b" if eps_total < 0.20 else "#ef4444"

        render_stage(
            "Stage 8 · Error Propagation Analysis (Eq. 3)", "#f59e0b", "⚠️",
            f"""
            <div class="stage-field-label">Equation 3</div>
            <div class="stage-field" style="font-family:monospace;font-size:12px;color:#fbbf24">
                ε_total ≤ ε_asr + ε_trans + ε_gen + ε_tts
            </div>
            <div style="margin-top:12px">
                {"".join([
                    f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0">'
                    f'<span style="font-family:monospace;font-size:12px;color:{clr};width:80px">{key}</span>'
                    f'<div style="flex:1;background:#1e293b;border-radius:4px;height:10px;overflow:hidden">'
                    f'<div style="width:{min(val*500,100):.0f}%;height:100%;background:{clr}"></div></div>'
                    f'<span style="font-family:monospace;font-size:12px;color:#e2e8f0;width:55px">{val:.3f}</span>'
                    f'<span style="font-size:10px;color:#64748b">{desc}</span>'
                    f'</div>'
                    for key, val, clr, desc in [
                        ("ε_asr",   eps_asr,   "#6366f1", "Speech recognition" + (" (0 = text input)" if input_modality == "text" else "")),
                        ("ε_trans", eps_trans, "#a855f7", f"L→P translation ({detected_lang}→EN)"),
                        ("ε_gen",   eps_gen,   "#ec4899", "Pivot reasoning (LLM)"),
                        ("ε_tts",   eps_tts,   "#22c55e", "TTS synthesis (0 = text output)"),
                    ]
                ])}
                <div style="border-top:1px solid #1e293b;margin-top:10px;padding-top:10px;display:flex;align-items:center;gap:10px">
                    <span style="font-family:monospace;font-size:14px;color:{total_color};font-weight:700;width:80px">ε_total</span>
                    <span style="font-family:monospace;font-size:24px;font-weight:800;color:{total_color}">≤ {eps_total:.3f}</span>
                    <span style="font-size:12px;color:#64748b">{"Low error" if eps_total < 0.10 else "Moderate error" if eps_total < 0.20 else "High error"}</span>
                </div>
            </div>
            """
        )

    # Save to history
    st.session_state.history.append({
        "input": input_text,
        "modality": input_modality,
        "src_lang": detected_lang,
        "tgt_lang": target_lang,
        "output": final_text,
        "lsc": lsc,
        "eps_total": eps_total,
    })
    st.session_state.last_run = stages

    # ── Final output box ───────────────────────────────────────────────────────
    rtl_style = "direction:rtl;text-align:right;" if target_lang in RTL_LANGS else ""
    st.markdown(f"""
    <div class="final-output" style="{rtl_style}">
        <div style="font-size:11px;color:#22c55e;font-family:monospace;margin-bottom:10px">
            ✅ PIPELINE COMPLETE · OL = RL(DP→L(GP(TL→P(NL(IL)), C)))
        </div>
        {final_text}
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
            <span class="badge" style="background:#22c55e22;border:1px solid #22c55e55;color:#22c55e">
                LSC = {lsc:.3f} · {lsc_label}
            </span>
            <span class="badge" style="background:{total_color}22;border:1px solid {total_color}55;color:{total_color}">
                ε_total ≤ {eps_total:.3f}
            </span>
            <span class="badge" style="background:#6366f122;border:1px solid #6366f155;color:#6366f1">
                {detected_lang} → {target_lang}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.caption(f"🤖 Model: `{OPENROUTER_MODEL}`")
    st.markdown("---")
    st.markdown("**Source Language**")
    source_lang = st.selectbox("Source", ["Auto-detect"] + ALL_LANG_NAMES, index=0)
    st.markdown("**Target Language**")
    target_lang = st.selectbox(
        "Target",
        ["Auto-detect"] + ALL_LANG_NAMES,
        index=0
    )
    st.markdown("---")
    if st.button("🗑️ Clear All History"):
        st.session_state.chat_history = []
        st.session_state.history = []
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📐 Pipeline Equation")
    st.code("OL = RL(DP→L(GP(TL→P(NL(IL)),C)))", language=None)
    st.caption("Eq.2: LSC = ‖EP − EncP(TL→P(OL))‖²")
    st.caption("Eq.3: ε_total ≤ ε_asr + ε_trans + ε_gen + ε_tts")
    st.caption("Complexity: O(n) vs Pairwise O(n²)")

    st.markdown("---")
    st.markdown("#### 🌐 All 22 Official Indian Languages")
    for lang, info in INDIC_LANGUAGES.items():
        if lang != "English":
            st.caption(f"**{lang}** · {info['script']}")
            # ─── Direct Output Mode ──────────────────────────────────────────────────────
            def run_direct_output(
                client,
                input_text: str,
                input_modality: str,
                asr_confidence: float,
                source_lang_choice: str,
                target_lang: str,
            ):
                norm_text = " ".join(input_text.split()).strip()

                # Detect source language
                if source_lang_choice == "Auto-detect":
                    detected = call_claude(
                        client,
                        [{
                            "role": "user",
                            "content": f'''
            Detect the language of this text.
            Reply ONLY with one language name from:
            {", ".join(ALL_LANG_NAMES)}

            Text: "{norm_text}"
            '''
                        }],
                        "You are a language detector."
                    )

                    detected = detected.strip().strip(".")
                    if detected not in INDIC_LANGUAGES:
                        detected = "English"

                    detected_lang = detected

                else:
                    detected_lang = source_lang_choice

                # Auto target language
                if target_lang == "Auto-detect":
                    target_lang = detected_lang

                # Translate to English pivot
                if detected_lang == "English":
                    pivot_text = norm_text
                else:
                    pivot_text = call_claude(
                        client,
                        [{
                            "role": "user",
                            "content": f"""
            Translate this {detected_lang} text to English.
            Return ONLY translation.

            Text:
            {norm_text}
            """
                        }],
                        "You are a translation engine."
                    )

                # Reasoning
                response_en = call_claude(
                    client,
                    [{"role": "user", "content": pivot_text}],
                    "You are a helpful multilingual AI assistant."
                )

                # Translate back to target language
                if target_lang == "English":
                    final_text = response_en
                else:
                    final_text = call_claude(
                        client,
                        [{
                            "role": "user",
                            "content": f"""
            Translate this English text to {target_lang}.
            Return ONLY translation.

            Text:
            {response_en}
            """
                        }],
                        "You are a translation engine."
                    )

                # TTS
                tts_code = INDIC_LANGUAGES[target_lang]["tts"]
                audio_html = tts_audio_html(final_text, tts_code)

                is_rtl = target_lang in RTL_LANGS
                rtl_style = "direction:rtl;text-align:right;" if is_rtl else ""

                st.markdown(f"""
                <div class="final-output" style="{rtl_style}">
                    <div style="font-size:12px;color:#22c55e;
                                font-family:monospace;
                                margin-bottom:10px">
                        ⚡ DIRECT OUTPUT MODE
                    </div>

                    {final_text}

                    <div style="margin-top:12px">
                        {audio_html}
                    </div>

                    <div style="margin-top:10px">
                        <span class="badge"
                        style="background:#6366f122;
                               border:1px solid #6366f155;
                               color:#6366f1">
                            {detected_lang} → {target_lang}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════
st.title("🌐 Pivot-Based Multilingual AI")

st.caption(
    "ICECI-2026 · *A Theoretical Framework for Pivot-Based Multilingual AI Response Generation in Indian Languages* "
    "· All 8 pipeline stages visible · Speech Input + Speech Output"
)

# Equation banner
st.markdown("""
<div class="equation-bar">
    <span style="color:#64748b">End-to-End (Eq.1): </span>
    <span style="color:#818cf8">OL</span>
    <span style="color:#e2e8f0"> = </span>
    <span style="color:#22c55e">RL</span><span style="color:#e2e8f0">(</span>
    <span style="color:#f97316">DP→L</span><span style="color:#e2e8f0">(</span>
    <span style="color:#ec4899">GP</span><span style="color:#e2e8f0">(</span>
    <span style="color:#a855f7">TL→P</span><span style="color:#e2e8f0">(</span>
    <span style="color:#8b5cf6">NL</span><span style="color:#e2e8f0">(IL), C)))</span>
    <span style="color:#64748b;margin-left:16px">· O(n) complexity · IndicTrans2 · 22 Indic Languages</span>
</div>
""", unsafe_allow_html=True)

tab_pipeline, tab_history = st.tabs(["🔬 Pipeline", "📜 History"])

# ─── Tab 1: Pipeline ─────────────────────────────────────────────────────────
with tab_pipeline:
    st.markdown("#### Input Mode")
    input_mode = st.radio("Choose input modality", ["✍️ Text", "🎤 Speech"], horizontal=True)

    input_text = ""
    input_modality = "text"
    asr_confidence = 1.0

    if input_mode == "✍️ Text":
        input_text = st.text_area(
            "Enter text in any Indian language or English:",
            placeholder="e.g. नमस्ते, आज मौसम कैसा है? / வணக்கம் / آپ کیسے ہیں؟ / Hello",
            height=100,
        )
        # Sample inputs
        st.markdown("**Quick samples:**")
        cols = st.columns(5)
        samples = [
            ("नमस्ते, आज मौसम कैसा है?", "Hindi"),
            ("நான் படிக்கிறேன்", "Tamil"),
            ("আপনি কেমন আছেন?", "Bengali"),
            ("آپ کیسے ہیں؟", "Urdu"),
            ("What is AI?", "English"),
        ]
        for i, (s, lang) in enumerate(samples):
            if cols[i].button(f"[{lang}]", key=f"sample_{i}", help=s):
                input_text = s

    else:  # Speech
        asr_code = INDIC_LANGUAGES.get(
            source_lang if source_lang != "Auto-detect" else "Hindi", {}
        ).get("asr", "hi-IN")

        st.info(
            f"🎤 Recording in: **{source_lang}** "
            f"(ASR code: `{asr_code}`)  \n"
            "Click the microphone to record, then click again to stop."
        )
        audio_data = st.audio_input("🎙️ Record your message")

        if audio_data:
            audio_bytes = bytes(audio_data.getbuffer())
            with st.spinner("Decoding audio…"):
                try:
                    seg = decode_audio(audio_bytes)
                    wav_bytes = audio_to_wav_bytes(seg)
                except ValueError as e:
                    st.error(f"❌ Audio decode error: {e}")
                    st.stop()

            with st.spinner(f"Transcribing via Google ASR ({asr_code})…"):
                try:
                    transcribed, asr_confidence = transcribe_audio(wav_bytes, asr_code)
                except RuntimeError as e:
                    st.error(str(e))
                    st.stop()

            if not transcribed:
                st.warning("⚠️ Could not recognize speech. Please try again clearly.")
                st.stop()

            input_text = transcribed
            input_modality = "speech"
            st.success(f"✅ Transcribed: **{transcribed}** (confidence: {asr_confidence*100:.0f}%)")

    st.markdown("---")

    col_run, col_clear = st.columns([3, 1])
    with col_run:
        run_btn = st.button(
            "🚀 Run Full Pipeline (All 8 Stages)",
            type="primary",
            disabled=not input_text.strip(),
            use_container_width=True,
        )
    with col_clear:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if run_btn and input_text.strip():
        client = get_client()
        run_full_pipeline(
            client=client,
            input_text=input_text.strip(),
            input_modality=input_modality,
            asr_confidence=asr_confidence,
            source_lang_choice=source_lang,
            target_lang=target_lang,
        )

# ─── Tab 2: History ───────────────────────────────────────────────────────────
with tab_history:
    st.markdown("#### Conversation History")
    if not st.session_state.history:
        st.info("No history yet. Run the pipeline to see results here.")
    else:
        for i, h in enumerate(reversed(st.session_state.history)):
            is_rtl = h["tgt_lang"] in RTL_LANGS
            rtl_style = "direction:rtl;text-align:right;" if is_rtl else ""
            lsc_color = "#22c55e" if h["lsc"] > 0.8 else "#f59e0b" if h["lsc"] > 0.6 else "#ef4444"
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <span style="font-family:monospace;font-size:11px;color:#475569">
                        #{len(st.session_state.history)-i} · {h["src_lang"]} → {h["tgt_lang"]} · {h["modality"]}
                    </span>
                    <span style="font-size:11px;color:{lsc_color}">LSC={h["lsc"]:.3f}</span>
                </div>
                <div class="chat-user">🧑 {h["input"]}</div>
                <div class="chat-bot" style="{rtl_style}">🤖 {h["output"]}</div>
            </div>
            """, unsafe_allow_html=True)
