# voice/__init__.py
# ─────────────────────────────────────────────
# Voice Production Hardening Module
#
# Production features for voice system:
#   - rate_limiter     → Redis-based per-endpoint rate limiting
#   - cost_tracker     → Cost tracking with budget enforcement
#   - metrics          → Observability metrics collection
#   - moderation       → Content moderation scanner
#   - audio_converter  → Audio format conversion utility
#
# RULES.md: <500 lines per file, type hints, docstrings
# ─────────────────────────────────────────────

from voice.rate_limiter import rate_limit, check_voice_rate_limit
from voice.cost_tracker import track_cost, check_budget, get_monthly_spend
from voice.metrics import record_voice_metric, get_voice_metrics
from voice.moderation import moderate_transcription, ModerationResult
from voice.audio_converter import convert_to_mp3

__all__ = [
    "rate_limit",
    "check_voice_rate_limit",
    "track_cost",
    "check_budget",
    "get_monthly_spend",
    "record_voice_metric",
    "get_voice_metrics",
    "moderate_transcription",
    "ModerationResult",
    "convert_to_mp3",
]
