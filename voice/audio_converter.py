# voice/audio_converter.py
# ─────────────────────────────────────────────
# Audio Format Conversion for Voice APIs
#
# WHY: Pollinations Whisper API works best with MP3 16kHz mono audio.
# Browsers record in various formats (webm, mp4, wav, ogg). Converting
# before sending improves transcription accuracy and reduces API errors.
#
# Conversion: webm, mp4, wav, ogg → MP3 16kHz mono
# Fallback: If conversion fails, send original format anyway
#
# Uses pydub (lightweight, wraps ffmpeg internally)
# Install: pip install pydub
# ─────────────────────────────────────────────

import io
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────

# Target format for optimal Whisper transcription
TARGET_SAMPLE_RATE = 16000  # 16kHz — Whisper's native sample rate
TARGET_CHANNELS = 1         # Mono
TARGET_BITRATE = "64k"      # 64kbps — good quality for speech
TARGET_FORMAT = "mp3"

# Maximum output size (10MB — same as upload limit)
MAX_OUTPUT_SIZE_BYTES = 10 * 1024 * 1024


def convert_to_mp3(
    audio_data: bytes,
    original_format: str = "unknown"
) -> Tuple[bytes, str, bool]:
    """
    Convert audio data to MP3 16kHz mono for optimal Whisper transcription.

    WHY: Called before sending to Pollinations Whisper API. Improves
    transcription accuracy by ensuring consistent input format.

    Args:
        audio_data: Raw audio bytes
        original_format: Original format hint (e.g., "webm", "mp4", "wav")

    Returns:
        Tuple of (converted_audio_bytes, output_format, was_converted)
        - If conversion succeeds: (mp3_bytes, "mp3", True)
        - If conversion fails: (original_bytes, original_format, False)

    Example:
        audio_bytes = await audio.read()
        converted, fmt, did_convert = convert_to_mp3(audio_bytes, "webm")
        # Send 'converted' to Whisper API
    """
    # If already MP3, no conversion needed
    if original_format.lower() in ("mp3", "mpeg", "mpga"):
        logger.debug(f"[voice/audio_converter] already MP3, skipping conversion")
        return audio_data, "mp3", False

    # Try conversion
    try:
        converted_data = _convert_with_pydub(audio_data, original_format)
        if converted_data and len(converted_data) > 0:
            logger.info(
                f"[voice/audio_converter] converted {original_format} → MP3 "
                f"({len(audio_data)} → {len(converted_data)} bytes)"
            )
            return converted_data, "mp3", True
    except ImportError:
        logger.warning(
            "[voice/audio_converter] pydub not installed — skipping conversion. "
            "Install with: pip install pydub"
        )
    except Exception as e:
        logger.error(f"[voice/audio_converter] conversion failed: {e}")

    # Fallback: return original data
    logger.info(
        f"[voice/audio_converter] using original format: {original_format} "
        f"({len(audio_data)} bytes)"
    )
    return audio_data, original_format, False


def _convert_with_pydub(audio_data: bytes, original_format: str) -> bytes:
    """
    Internal conversion using pydub.

    Args:
        audio_data: Raw audio bytes
        original_format: Format string for pydub (e.g., "webm", "wav")

    Returns:
        Converted MP3 bytes

    Raises:
        ImportError: If pydub not installed
        Exception: On conversion failure
    """
    # Lazy import — only needed when conversion is actually required
    from pydub import AudioSegment

    # Map content types to pydub format strings
    format_map = {
        "audio/webm": "webm",
        "webm": "webm",
        "audio/mp4": "mp4",
        "mp4": "mp4",
        "audio/m4a": "mp4",
        "m4a": "mp4",
        "audio/wav": "wav",
        "wav": "wav",
        "audio/x-wav": "wav",
        "audio/ogg": "ogg",
        "ogg": "ogg",
        "audio/opus": "ogg",  # Opus is usually in Ogg container
        "opus": "ogg",
    }

    pydub_format = format_map.get(original_format.lower(), original_format.lower())

    # Load audio from bytes
    audio = AudioSegment.from_file(
        io.BytesIO(audio_data),
        format=pydub_format
    )

    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(TARGET_CHANNELS)

    # Resample to 16kHz
    if audio.frame_rate != TARGET_SAMPLE_RATE:
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)

    # Export as MP3
    output = io.BytesIO()
    audio.export(
        output,
        format=TARGET_FORMAT,
        bitrate=TARGET_BITRATE,
        parameters=["-codec:a", "libmp3lame"]
    )

    converted_data = output.getvalue()

    # Safety check: don't return oversized output
    if len(converted_data) > MAX_OUTPUT_SIZE_BYTES:
        raise ValueError(
            f"Converted audio too large: {len(converted_data)} bytes "
            f"(max: {MAX_OUTPUT_SIZE_BYTES})"
        )

    return converted_data


def get_audio_info(audio_data: bytes, format_hint: str = "unknown") -> dict:
    """
    Extract audio metadata for logging/debugging.

    Args:
        audio_data: Raw audio bytes
        format_hint: Original format hint

    Returns:
        Dict with duration_ms, size_bytes, format, sample_rate, channels
    """
    info = {
        "size_bytes": len(audio_data),
        "format": format_hint,
        "duration_ms": 0,
        "sample_rate": 0,
        "channels": 0,
    }

    try:
        from pydub import AudioSegment

        format_map = {
            "audio/webm": "webm", "webm": "webm",
            "audio/mp4": "mp4", "mp4": "mp4", "m4a": "mp4",
            "audio/wav": "wav", "wav": "wav",
            "audio/ogg": "ogg", "ogg": "ogg", "opus": "ogg",
        }
        pydub_format = format_map.get(format_hint.lower(), format_hint.lower())

        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=pydub_format)
        info["duration_ms"] = len(audio)
        info["sample_rate"] = audio.frame_rate
        info["channels"] = audio.channels
    except ImportError:
        info["error"] = "pydub not installed"
    except Exception as e:
        info["error"] = str(e)

    return info
