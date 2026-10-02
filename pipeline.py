"""
pipeline.py — All AI/NLP logic.

Translation backbone : IndicTrans2 (ai4bharat) with IndicProcessor pre/post-processing.
LLM calls            : OpenRouter (reasoning / detection / proofreading / chatbot).

Install dependencies:
    pip install torch transformers
    pip install git+https://github.com/VarunGumma/IndicTransToolkit.git
"""

import json
from difflib import ndiff
from typing import Optional

import streamlit as st
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor
from huggingface_hub import login as hf_login

from config import (
    call_openrouter,
    LANG_NAMES,
    INDIC_LANG_CODE,
    INDICTRANS_INDIC_EN_MODEL,
    INDICTRANS_EN_INDIC_MODEL,
    HUGGING_FACE_TOKEN,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ─────────────────────────────────────────────
# IndicTrans2 — lazy model loading (cached)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner="🤗 Loading IndicTrans2 models (first run only)…")
def _load_indictrans_models() -> dict:
    """
    Load both IndicTrans2 checkpoints + IndicProcessor once per Streamlit session.
    Requires HUGGING_FACE_TOKEN in .env if the model repo is access-restricted.
    """
    if HUGGING_FACE_TOKEN:
        hf_login(token=HUGGING_FACE_TOKEN, add_to_git_credential=False)

    # ── Indic → English ──────────────────────
    tok_ie = AutoTokenizer.from_pretrained(
        INDICTRANS_INDIC_EN_MODEL, trust_remote_code=True
    )
    mod_ie = AutoModelForSeq2SeqLM.from_pretrained(
        INDICTRANS_INDIC_EN_MODEL,
        trust_remote_code=True,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    ).to(DEVICE)
    mod_ie.eval()

    # ── English → Indic ──────────────────────
    tok_ei = AutoTokenizer.from_pretrained(
        INDICTRANS_EN_INDIC_MODEL, trust_remote_code=True
    )
    mod_ei = AutoModelForSeq2SeqLM.from_pretrained(
        INDICTRANS_EN_INDIC_MODEL,
        trust_remote_code=True,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    ).to(DEVICE)
    mod_ei.eval()

    # ── IndicProcessor (shared, inference mode) ──
    ip = IndicProcessor(inference=True)

    return {
        "indic_en": (tok_ie, mod_ie),
        "en_indic": (tok_ei, mod_ei),
        "processor": ip,
        "device": DEVICE,
    }


# ─────────────────────────────────────────────
# Core IndicTrans2 inference
# ─────────────────────────────────────────────

def _indictrans_translate(
    sentences: list[str],
    src_flores: str,
    tgt_flores: str,
    direction: str,          # "indic_en"  or  "en_indic"
) -> list[str]:
    """
    Translate a batch of sentences using IndicTrans2 + IndicProcessor.

    Args:
        sentences   : List of input strings.
        src_flores  : Flores-200 source code, e.g. "hin_Deva".
        tgt_flores  : Flores-200 target code, e.g. "eng_Latn".
        direction   : "indic_en" or "en_indic".

    Returns:
        List of translated strings (same length as input).
        Falls back to input sentences on any error.
    """
    try:
        models    = _load_indictrans_models()
        tokenizer, model = models[direction]
        ip        = models["processor"]
        device    = models["device"]

        # Step 1 — IndicProcessor pre-processing
        batch = ip.preprocess_batch(
            sentences,
            src_lang=src_flores,
            tgt_lang=tgt_flores,
        )

        # Step 2 — Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(device)

        # Step 3 — Generate
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )

        # Step 4 — Decode
        decoded = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )

        # Step 5 — IndicProcessor post-processing (entity replacement etc.)
        translations = ip.postprocess_batch(decoded, lang=tgt_flores)
        return translations

    except Exception as exc:
        print(f"⚠️  IndicTrans2 error ({direction} | {src_flores}→{tgt_flores}): {exc}")
        return sentences   # graceful fallback — return originals


def _translate_single(text: str, src_flores: str, tgt_flores: str, direction: str) -> str:
    """Convenience wrapper: translate one string, return one string."""
    results = _indictrans_translate([text], src_flores, tgt_flores, direction)
    return results[0] if results else text


# ─────────────────────────────────────────────
# Public translation helpers
# ─────────────────────────────────────────────

def indic_to_english(
    text: str, source_lang: str
) -> tuple[Optional[str], Optional[str], float]:
    """
    Translate any supported Indian language → English via IndicTrans2.

    Returns:
        (translated_text, error_message, confidence)
        confidence = 1.0 for English pass-through, 0.9 for model output.
    """
    if source_lang.lower() == "english":
        return text, None, 1.0

    src_flores = INDIC_LANG_CODE.get(source_lang)
    if not src_flores:
        return None, f"❌ Unknown source language: {source_lang}", 0.0

    tgt_flores = INDIC_LANG_CODE["English"]          # eng_Latn
    translated = _translate_single(text, src_flores, tgt_flores, "indic_en")
    return translated, None, 0.9


def english_to_indic(
    text: str, target_lang: str
) -> tuple[Optional[str], Optional[str]]:
    """
    Translate English → any supported Indian language via IndicTrans2.

    Returns:
        (translated_text, error_message)
    """
    if target_lang.lower() == "english":
        return text, None

    tgt_flores = INDIC_LANG_CODE.get(target_lang)
    if not tgt_flores:
        return None, f"❌ Unknown target language: {target_lang}"

    src_flores = INDIC_LANG_CODE["English"]          # eng_Latn
    translated = _translate_single(text, src_flores, tgt_flores, "en_indic")
    return translated, None


# ─────────────────────────────────────────────
# Pivot Pipeline (Tab 3)
# ─────────────────────────────────────────────

def detect_language(text: str) -> str:
    """Use the LLM to identify which of the 22 Indian languages (or English) the text is in."""
    lang_list = ", ".join(LANG_NAMES) + ", English"
    content, _ = call_openrouter(
        [
            {
                "role": "system",
                "content": (
                    f"You are a language detector. Identify the language of the text from: {lang_list}. "
                    "Reply with ONLY the language name, nothing else."
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    return (content or "Unknown").strip()


def pivot_reasoning(
    pivot_text: str, context: list
) -> tuple[Optional[str], Optional[str]]:
    """Stage 4 — GP: Central AI reasoning in English pivot space via OpenRouter."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful multilingual AI assistant. "
                "You reason and respond in English (pivot language). "
                "Be concise, accurate, and culturally sensitive for Indian language users."
            ),
        }
    ] + context + [{"role": "user", "content": pivot_text}]
    return call_openrouter(messages, temperature=0.7)


def semantic_consistency_check(original: str, back_translated: str) -> float:
    """Equation (2): LSC — semantic consistency score [0.0, 1.0] via LLM."""
    content, _ = call_openrouter(
        [
            {
                "role": "system",
                "content": (
                    "You are a semantic similarity evaluator. "
                    "Score the semantic similarity of two texts from 0.0 to 1.0. "
                    "Reply with ONLY a decimal number."
                ),
            },
            {"role": "user", "content": f"Text 1: {original}\n\nText 2: {back_translated}"},
        ],
        temperature=0,
    )
    try:
        return float((content or "0.75").strip())
    except Exception:
        return 0.75


def full_pivot_pipeline(
    user_input: str,
    source_lang: str,
    target_lang: str,
    chat_context: list,
) -> dict:
    """
    Full pipeline: OL = RL( DP→L( GP( TL→P( NL(IL) ), C ) ) )  — Eq. (1)

    Stage 3 (TL→P)  : IndicTrans2  — source language → English
    Stage 4 (GP)    : OpenRouter LLM — reasoning in English pivot
    Stage 5 (DP→L)  : IndicTrans2  — English → target language
    """
    result: dict = {
        "stages":        [],
        "final_output":  "",
        "pivot_text":    "",
        "pivot_response":"",
        "detected_lang": source_lang,
        "semantic_score":None,
        "error":         None,
        "error_bounds":  {},
    }

    # ── Stage 2: Normalization ────────────────
    normalized = user_input.strip()
    result["stages"].append({
        "label": "Stage 2 — Normalization (NL)",
        "content": normalized,
        "icon": "🔧",
    })

    # ── Auto language detection ───────────────
    if source_lang == "Auto-detect":
        with st.spinner("🔍 Detecting language…"):
            detected = detect_language(normalized)
        result["detected_lang"] = detected
        source_lang = detected if detected in LANG_NAMES else "English"
        result["stages"].append({
            "label": "Language Detection",
            "content": f"Detected: **{detected}**",
            "icon": "🔍",
        })

    # ── Stage 3: Indic → English (IndicTrans2) ──
    with st.spinner(f"🔄 IndicTrans2: {source_lang} → English…"):
        pivot_text, err, trans_conf = indic_to_english(normalized, source_lang)
    if err:
        result["error"] = err
        return result
    result["pivot_text"] = pivot_text
    result["error_bounds"]["ε_trans"] = round(1 - trans_conf, 2)
    result["stages"].append({
        "label":   f"Stage 3 — IndicTrans2 ({source_lang} → English)",
        "content": pivot_text,
        "icon":    "🔄",
    })

    # ── Stage 4: Pivot reasoning (OpenRouter) ──
    with st.spinner("🧠 Reasoning in English pivot space…"):
        pivot_response, err = pivot_reasoning(pivot_text, chat_context)
    if err:
        result["error"] = err
        return result
    result["pivot_response"] = pivot_response
    result["error_bounds"]["ε_gen"] = 0.05
    result["stages"].append({
        "label":   "Stage 4 — Pivot Reasoning (English, OpenRouter)",
        "content": pivot_response,
        "icon":    "🧠",
    })

    # ── Stage 5: English → target (IndicTrans2) ──
    with st.spinner(f"🔄 IndicTrans2: English → {target_lang}…"):
        final_output, err = english_to_indic(pivot_response, target_lang)
    if err:
        result["error"] = err
        return result
    result["final_output"] = final_output
    result["error_bounds"]["ε_tts"] = 0.0
    result["stages"].append({
        "label":   f"Stage 5 — IndicTrans2 (English → {target_lang})",
        "content": final_output,
        "icon":    "🌐",
    })

    # ── Semantic consistency check (Eq. 2) ───
    with st.spinner("🔎 Semantic consistency check…"):
        back_translated, _, _conf = indic_to_english(final_output, target_lang)
        if back_translated:
            result["semantic_score"] = semantic_consistency_check(
                pivot_response, back_translated
            )

    # ── Error propagation (Eq. 3) ────────────
    eb = result["error_bounds"]
    eb["ε_asr"]   = 0.0
    eb["ε_total"] = round(
        eb["ε_asr"] + eb["ε_trans"] + eb["ε_gen"] + eb["ε_tts"], 2
    )

    return result


# ─────────────────────────────────────────────
# Urdu Speech Writer Helpers (Tab 1)
# ─────────────────────────────────────────────

def translate_to_urdu(text: str) -> str:
    """
    Translate arbitrary text → Urdu via IndicTrans2.
    Skips translation if text is already predominantly Urdu/Arabic script.
    For non-English Indic input: uses two-hop  Indic → English → Urdu.
    """
    if not text or not text.strip():
        return ""

    # Already Urdu/Arabic script?
    urdu_chars = sum(1 for ch in text if "\u0600" <= ch <= "\u06FF")
    if urdu_chars / max(1, len(text)) > 0.3:
        return text

    detected_lang = detect_language(text)

    if detected_lang.lower() == "english" or detected_lang not in LANG_NAMES:
        # English → Urdu (single hop)
        result, err = english_to_indic(text, "Urdu")
    else:
        # Indic → English → Urdu (two hops via pivot)
        eng_text, err, _ = indic_to_english(text, detected_lang)
        if err or not eng_text:
            return text
        result, err = english_to_indic(eng_text, "Urdu")

    return result if (result and not err) else text


def proofread_urdu(
    urdu_text: str, source_text: str = ""
) -> tuple[Optional[dict], Optional[str]]:
    """
    Proofread Urdu text via OpenRouter LLM.

    Returns:
        ({"corrected": str, "changes": list}, error_str | None)
    """
    sys_prompt = (
        "You are an expert Urdu copyeditor. "
        "Correct spelling, spacing, punctuation and obvious word errors. "
        "Return ONLY valid JSON with no markdown fences: "
        '{"corrected":"...", "changes":[{"from":"x","to":"y","reason":"z"}]}'
    )
    content, err = call_openrouter(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": f"Original Urdu:\n{urdu_text}\n\nReference source:\n{source_text}"},
        ]
    )
    if err:
        return None, err
    # Strip accidental markdown code fences
    clean = (content or "").strip()
    for fence in ("```json", "```"):
        clean = clean.strip(fence)
    clean = clean.strip()
    try:
        parsed = json.loads(clean)
        return {
            "corrected": parsed.get("corrected", "").strip(),
            "changes":   parsed.get("changes", []),
        }, None
    except Exception:
        return {"corrected": clean, "changes": []}, None


def diff_text(old: str, new: str) -> str:
    """Return a markdown word-level diff between two strings."""
    out = []
    for token in ndiff(old.split(), new.split()):
        if token.startswith("+ "):
            out.append(f"**{token[2:]}**")
        elif token.startswith("- "):
            out.append(f"~~{token[2:]}~~")
        elif token.startswith("? "):
            continue
        else:
            out.append(token[2:])
    return " ".join(out)


# ─────────────────────────────────────────────
# Chatbot (Tab 2)
# ─────────────────────────────────────────────

def chatbot_reply(messages: list, language: str) -> str:
    """Generate a chatbot reply in the specified language via OpenRouter."""
    lang_instruction = {
        "Urdu":    "Always respond in Urdu only, using Nastaliq script.",
        "English": "Always respond in English only.",
        "Auto":    "Detect the user's language and respond in the same language.",
    }
    system_msg = {
        "role": "system",
        "content": (
            "You are a helpful assistant specialising in Urdu writing. "
            f"{lang_instruction.get(language, '')}"
        ),
    }
    content, _ = call_openrouter([system_msg] + messages, temperature=0.7)
    return content or "❌ Sorry, couldn't get a response."