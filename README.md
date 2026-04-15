# Voice Audio

> By [MEOK AI Labs](https://meok.ai) — MEOK AI Labs — Voice & Audio. Transcription, analysis, language detection, and duration estimation.

Voice Audio MCP — MEOK AI Labs. Transcription, audio analysis, language detection, and duration estimation.

## Installation

```bash
pip install voice-audio-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install voice-audio-mcp
```

## Tools

### `transcribe_audio`
Transcribe audio to text using Whisper STT. Supports local files and multiple languages.

**Parameters:**
- `audio_path` (str)
- `language` (str)
- `model_size` (str)
- `timestamps` (bool)

### `analyze_audio`
Analyze audio or text for speech characteristics: word count, speaking rate, silence ratio, and complexity.

**Parameters:**
- `audio_path` (str)
- `text_content` (str)

### `detect_language`
Detect the language of text using statistical analysis of word patterns and n-grams.

**Parameters:**
- `text` (str)

### `estimate_duration`
Estimate audio duration for text or word count at a given speaking rate, accounting for natural pauses.

**Parameters:**
- `text` (str)
- `word_count` (int)
- `speaking_rate_wpm` (int)
- `include_pauses` (bool)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/voice-audio-mcp](https://github.com/CSOAI-ORG/voice-audio-mcp)
- **PyPI**: [pypi.org/project/voice-audio-mcp](https://pypi.org/project/voice-audio-mcp/)

## License

MIT — MEOK AI Labs
