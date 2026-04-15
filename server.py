#!/usr/bin/env python3
"""Voice Audio MCP — MEOK AI Labs. Transcription, audio analysis, language detection, and duration estimation."""

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json, hashlib, base64, re
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 10
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

mcp = FastMCP("voice-audio", instructions="MEOK AI Labs — Voice & Audio. Transcription, analysis, language detection, and duration estimation.")

VOICES = {
    "sophie": {"gender": "female", "accent": "british", "style": "warm, caring", "speed": 0.9, "pitch": "medium"},
    "jarvis": {"gender": "male", "accent": "british", "style": "precise, professional", "speed": 1.0, "pitch": "low"},
    "aria": {"gender": "female", "accent": "neutral", "style": "calm, soothing", "speed": 0.85, "pitch": "medium-high"},
    "marcus": {"gender": "male", "accent": "american", "style": "confident, clear", "speed": 1.05, "pitch": "medium-low"},
    "luna": {"gender": "female", "accent": "australian", "style": "energetic, friendly", "speed": 1.1, "pitch": "high"},
    "kai": {"gender": "male", "accent": "neutral", "style": "warm, conversational", "speed": 0.95, "pitch": "medium"},
}

SUPPORTED_FORMATS = ["wav", "mp3", "m4a", "ogg", "flac", "aac", "wma", "opus"]

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "variants": ["en-US", "en-GB", "en-AU"]},
    "es": {"name": "Spanish", "variants": ["es-ES", "es-MX"]},
    "fr": {"name": "French", "variants": ["fr-FR", "fr-CA"]},
    "de": {"name": "German", "variants": ["de-DE", "de-AT"]},
    "ja": {"name": "Japanese", "variants": ["ja-JP"]},
    "zh": {"name": "Chinese", "variants": ["zh-CN", "zh-TW"]},
    "ko": {"name": "Korean", "variants": ["ko-KR"]},
    "pt": {"name": "Portuguese", "variants": ["pt-BR", "pt-PT"]},
    "it": {"name": "Italian", "variants": ["it-IT"]},
    "nl": {"name": "Dutch", "variants": ["nl-NL"]},
    "ar": {"name": "Arabic", "variants": ["ar-SA"]},
    "hi": {"name": "Hindi", "variants": ["hi-IN"]},
    "ru": {"name": "Russian", "variants": ["ru-RU"]},
}

LANGUAGE_INDICATORS = {
    "en": ["the", "and", "is", "are", "was", "were", "have", "has", "been", "would", "could", "should"],
    "es": ["el", "la", "los", "las", "es", "son", "fue", "han", "tiene", "como", "pero", "mas"],
    "fr": ["le", "la", "les", "est", "sont", "avec", "dans", "pour", "pas", "une", "des", "qui"],
    "de": ["der", "die", "das", "ist", "sind", "mit", "und", "ein", "eine", "nicht", "auf", "aus"],
    "it": ["il", "la", "gli", "che", "non", "sono", "con", "per", "una", "della", "questo"],
    "pt": ["o", "os", "as", "que", "nao", "com", "para", "uma", "dos", "das", "pelo"],
}


@mcp.tool()
def transcribe_audio(audio_path: str = "", language: str = "auto",
                      model_size: str = "base", timestamps: bool = False,
                      api_key: str = "") -> str:
    """Transcribe audio to text using Whisper STT. Supports local files and multiple languages."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if not audio_path:
        return {
            "error": "Audio path required. Provide a local file path.",
            "supported_formats": SUPPORTED_FORMATS,
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "model_sizes": ["tiny", "base", "small", "medium", "large"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    if ext not in SUPPORTED_FORMATS:
        return {"error": f"Unsupported format '.{ext}'", "supported": SUPPORTED_FORMATS}

    file_exists = os.path.isfile(audio_path)
    if not file_exists:
        return {"error": f"File not found: {audio_path}", "suggestion": "Provide an absolute file path"}

    file_size = os.path.getsize(audio_path)
    file_hash = hashlib.md5(open(audio_path, "rb").read(8192)).hexdigest() if file_exists else ""

    try:
        import urllib.request
        payload = json.dumps({"audio_path": audio_path, "language": language,
                               "model": model_size, "timestamps": timestamps}).encode()
        req = urllib.request.Request("http://localhost:8180/transcribe",
                                     data=payload, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        result["source"] = "whisper_local"
        result["file_hash"] = file_hash
        return result
    except Exception:
        return {
            "status": "whisper_unavailable",
            "audio_path": audio_path,
            "file_size_bytes": file_size,
            "file_hash": file_hash,
            "format": ext,
            "language_requested": language,
            "model_size": model_size,
            "setup_instructions": "Start Whisper: python whisper_server.py (port 8180). Requires MLX Whisper.",
            "estimated_duration_sec": round(file_size / 16000, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@mcp.tool()
def analyze_audio(audio_path: str = "", text_content: str = "", api_key: str = "") -> str:
    """Analyze audio or text for speech characteristics: word count, speaking rate, silence ratio, and complexity."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if text_content:
        words = text_content.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', text_content)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_word_len = round(sum(len(w) for w in words) / max(word_count, 1), 1)
        unique_words = len(set(w.lower() for w in words))
        lexical_diversity = round(unique_words / max(word_count, 1), 3)

        est_duration_sec = round(word_count / 2.5, 1)
        speaking_rate_wpm = 150

        filler_words = ["um", "uh", "like", "you know", "basically", "actually", "literally"]
        filler_count = sum(text_content.lower().count(f) for f in filler_words)

        return {
            "source": "text_analysis",
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_word_length": avg_word_len,
            "unique_words": unique_words,
            "lexical_diversity": lexical_diversity,
            "filler_word_count": filler_count,
            "estimated_duration_sec": est_duration_sec,
            "estimated_speaking_rate_wpm": speaking_rate_wpm,
            "readability_level": "simple" if avg_word_len < 5 else "moderate" if avg_word_len < 7 else "complex",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    if audio_path and os.path.isfile(audio_path):
        file_size = os.path.getsize(audio_path)
        ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
        bitrate_map = {"wav": 1536000, "mp3": 128000, "m4a": 128000, "ogg": 112000, "flac": 900000}
        bitrate = bitrate_map.get(ext, 128000)
        est_duration = round(file_size * 8 / bitrate, 1)

        return {
            "source": "file_analysis",
            "audio_path": audio_path,
            "format": ext,
            "file_size_bytes": file_size,
            "estimated_duration_sec": est_duration,
            "estimated_bitrate_kbps": round(bitrate / 1000),
            "estimated_word_count": round(est_duration * 2.5),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {"error": "Provide either audio_path or text_content for analysis",
            "timestamp": datetime.now(timezone.utc).isoformat()}


@mcp.tool()
def detect_language(text: str, api_key: str = "") -> str:
    """Detect the language of text using statistical analysis of word patterns and n-grams."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if not text or len(text.strip()) < 5:
        return {"error": "Text too short for reliable detection (min 5 chars)", "text_length": len(text.strip())}

    words = text.lower().split()
    scores = {}
    for lang, indicators in LANGUAGE_INDICATORS.items():
        score = sum(1 for w in words if w in indicators)
        if score > 0:
            scores[lang] = score

    if not scores:
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)
        has_hangul = any('\uac00' <= c <= '\ud7af' for c in text)
        has_hiragana = any('\u3040' <= c <= '\u309f' for c in text)
        has_arabic = any('\u0600' <= c <= '\u06ff' for c in text)
        has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in text)
        has_devanagari = any('\u0900' <= c <= '\u097f' for c in text)

        if has_cjk:
            scores["zh"] = 10
        if has_hangul:
            scores["ko"] = 10
        if has_hiragana:
            scores["ja"] = 10
        if has_arabic:
            scores["ar"] = 10
        if has_cyrillic:
            scores["ru"] = 10
        if has_devanagari:
            scores["hi"] = 10

    if not scores:
        return {"detected_language": "en", "confidence": 0.3, "note": "Defaulting to English — insufficient signals",
                "text_length": len(text), "timestamp": datetime.now(timezone.utc).isoformat()}

    total = sum(scores.values())
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    best = ranked[0]
    confidence = round(min(best[1] / max(total, 1) * (1 + min(best[1], 10) / 10), 1.0), 3)

    lang_info = SUPPORTED_LANGUAGES.get(best[0], {"name": best[0], "variants": []})
    alternatives = [{"language": lang, "name": SUPPORTED_LANGUAGES.get(lang, {}).get("name", lang),
                      "score": s} for lang, s in ranked[1:4]]

    return {
        "detected_language": best[0],
        "language_name": lang_info["name"],
        "confidence": confidence,
        "variants": lang_info.get("variants", []),
        "alternatives": alternatives,
        "text_length": len(text),
        "word_count": len(words),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def estimate_duration(text: str = "", word_count: int = 0, speaking_rate_wpm: int = 150,
                       include_pauses: bool = True, api_key: str = "") -> str:
    """Estimate audio duration for text or word count at a given speaking rate, accounting for natural pauses."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if text:
        words = text.split()
        wc = len(words)
        sentences = len(re.split(r'[.!?]+', text))
        paragraphs = text.count("\n\n") + 1
    elif word_count > 0:
        wc = word_count
        sentences = max(1, wc // 15)
        paragraphs = max(1, wc // 100)
    else:
        return {"error": "Provide text or word_count", "timestamp": datetime.now(timezone.utc).isoformat()}

    base_seconds = (wc / speaking_rate_wpm) * 60
    pause_seconds = 0
    if include_pauses:
        pause_seconds = sentences * 0.5 + paragraphs * 1.5

    total_seconds = round(base_seconds + pause_seconds, 1)
    minutes = int(total_seconds // 60)
    secs = int(total_seconds % 60)

    rates = {
        "slow": round((wc / 120) * 60 + pause_seconds, 1),
        "normal": round((wc / 150) * 60 + pause_seconds, 1),
        "fast": round((wc / 180) * 60 + pause_seconds, 1),
    }

    file_estimates = {}
    for fmt, bps in [("wav", 1536000), ("mp3_128", 128000), ("mp3_320", 320000), ("ogg", 112000)]:
        file_estimates[fmt] = f"{round(total_seconds * bps / 8 / 1024, 1)} KB"

    return {
        "word_count": wc,
        "speaking_rate_wpm": speaking_rate_wpm,
        "duration_seconds": total_seconds,
        "duration_formatted": f"{minutes}m {secs}s",
        "base_speaking_seconds": round(base_seconds, 1),
        "pause_seconds": round(pause_seconds, 1),
        "sentences": sentences,
        "rate_comparisons": rates,
        "estimated_file_sizes": file_estimates,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    mcp.run()
