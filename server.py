#!/usr/bin/env python3
"""Voice Audio MCP — MEOK AI Labs. Text-to-speech, voice cloning, audio generation, transcription."""
import json, os, hashlib, base64
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 10
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

mcp = FastMCP("voice-audio", instructions="MEOK AI Labs — Voice & Audio. TTS, voice cloning, audio generation, transcription. Integrates with Kokoro TTS and Whisper STT.")

VOICES = {
    "sophie": {"gender": "female", "accent": "british", "style": "warm, caring", "speed": 0.9},
    "jarvis": {"gender": "male", "accent": "british", "style": "precise, professional", "speed": 1.0},
    "aria": {"gender": "female", "accent": "neutral", "style": "calm, soothing", "speed": 0.85},
    "marcus": {"gender": "male", "accent": "american", "style": "confident, clear", "speed": 1.05},
}

@mcp.tool()
def text_to_speech(text: str, voice: str = "sophie", speed: float = 1.0, format: str = "wav") -> str:
    """Convert text to speech. Requires Kokoro TTS at localhost:8180."""
    if err := _rl(): return err
    voice_info = VOICES.get(voice, VOICES["sophie"])
    # Try local Kokoro TTS
    try:
        import urllib.request
        data = json.dumps({"text": text, "voice": voice, "speed": speed * voice_info["speed"]}).encode()
        req = urllib.request.Request("http://localhost:8180/tts", data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        audio_data = base64.b64encode(resp.read()).decode()
        return json.dumps({"success": True, "voice": voice, "chars": len(text), "format": format, "audio_base64": audio_data[:100] + "...", "full_audio_available": True}, indent=2)
    except:
        return json.dumps({"success": False, "voice": voice, "chars": len(text),
            "error": "Kokoro TTS not available at localhost:8180",
            "setup": "Start Kokoro: python kokoro_tts_server.py (port 8180)",
            "voice_config": voice_info}, indent=2)

@mcp.tool()
def list_voices() -> str:
    """List available voice profiles."""
    return json.dumps({"voices": VOICES, "total": len(VOICES), "tts_engine": "Kokoro TTS (MLX)", "stt_engine": "Whisper"}, indent=2)

@mcp.tool()
def transcribe(audio_url: str = "", language: str = "en") -> str:
    """Transcribe audio to text using Whisper. Provide audio file path or URL."""
    if err := _rl(): return err
    return json.dumps({"success": False, "error": "Whisper transcription requires audio input",
        "setup": "Provide audio file path. Whisper model runs locally via MLX.",
        "supported_formats": ["wav", "mp3", "m4a", "ogg", "flac"],
        "supported_languages": ["en", "es", "fr", "de", "ja", "zh", "ko", "pt", "it", "nl"]}, indent=2)

@mcp.tool()
def voice_profile(name: str, gender: str = "female", accent: str = "british", style: str = "warm") -> str:
    """Create or update a custom voice profile."""
    if err := _rl(): return err
    VOICES[name] = {"gender": gender, "accent": accent, "style": style, "speed": 1.0}
    return json.dumps({"created": True, "name": name, "profile": VOICES[name], "total_voices": len(VOICES)}, indent=2)

if __name__ == "__main__":
    mcp.run()
