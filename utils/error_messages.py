# utils/error_messages.py
# ─────────────────────────────────────────────
# Personality-Driven Error Messages — PromptForge v2.0
#
# Provides structured, user-friendly error messages with 3 tone variants:
#   - direct: Concise, no-nonsense (default for most users)
#   - casual: Friendly, conversational (for relaxed tone preference)
#   - formal: Professional, detailed (for enterprise/technical users)
#
# Usage:
#     from utils.error_messages import get_error_message, ErrorType
#     error = get_error_message(ErrorType.RATE_LIMIT, user_tone="casual", retry_after_minutes=5)
#     raise HTTPException(status_code=429, detail=error["full_message"])
#
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Logging integrated
# - No hardcoded secrets
# ─────────────────────────────────────────────

import logging
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """
    Enum of all error types in PromptForge.

    Each type maps to a structured error response with personality-driven messaging.
    """
    RATE_LIMIT = "rate_limit"
    AUTH_EXPIRED = "auth_expired"
    LLM_TIMEOUT = "llm_timeout"
    LLM_UNAVAILABLE = "llm_unavailable"
    INVALID_INPUT = "invalid_input"
    MEMORY_WRITE_FAILED = "memory_write_failed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    TRIAL_LIMIT_EXCEEDED = "trial_limit_exceeded"
    UNKNOWN = "unknown"


# ── Personality Tone Variants ─────────────────

PERSONALITY_TONES: Dict[ErrorType, Dict[str, Dict[str, str]]] = {
    ErrorType.RATE_LIMIT: {
        "direct": {
            "what": "You've hit the rate limit.",
            "why": "Too many requests in a short period. This keeps the service stable for everyone.",
            "action": "Wait a moment, then try again.",
        },
        "casual": {
            "what": "Whoa there — you're going a bit fast!",
            "why": "We cap requests to keep things smooth for everyone. Nothing personal, just keeping the servers happy.",
            "action": "Take a breather and retry in a bit.",
        },
        "formal": {
            "what": "Your request rate has exceeded the configured threshold.",
            "why": "Rate limiting is enforced to ensure equitable service availability and system stability.",
            "action": "Please wait before retrying. Additional requests during this window will not be processed.",
        },
    },
    ErrorType.AUTH_EXPIRED: {
        "direct": {
            "what": "Your session has expired.",
            "why": "Authentication tokens have a limited lifetime for security.",
            "action": "Log in again to get a new token.",
        },
        "casual": {
            "what": "Your session timed out — happens to the best of us.",
            "why": "Tokens don't last forever (security thing, you know?).",
            "action": "Just log back in and you're good to go.",
        },
        "formal": {
            "what": "Your authentication session has expired.",
            "why": "Security policy requires periodic re-authentication to protect your account.",
            "action": "Please re-authenticate by logging in with your credentials.",
        },
    },
    ErrorType.LLM_TIMEOUT: {
        "direct": {
            "what": "The AI took too long to respond.",
            "why": "Complex prompts can exceed the processing timeout (3 minutes).",
            "action": "Try a shorter prompt or retry.",
        },
        "casual": {
            "what": "The AI's thinking a bit too hard — timed out!",
            "why": "Some prompts are just too complex for the timeout window. The model's gears are still spinning.",
            "action": "Try simplifying your prompt a bit, or give it another shot.",
        },
        "formal": {
            "what": "The language model processing time exceeded the configured limit.",
            "why": "Complex prompt engineering operations may require extended processing that exceeds the 3-minute timeout threshold.",
            "action": "Consider simplifying your input or retrying the request.",
        },
    },
    ErrorType.LLM_UNAVAILABLE: {
        "direct": {
            "what": "The AI model is currently unavailable.",
            "why": "The LLM service may be down or experiencing high load.",
            "action": "Wait a moment and try again. If it persists, check status.",
        },
        "casual": {
            "what": "The AI's taking a quick break — not available right now.",
            "why": "Could be maintenance, high load, or a temporary hiccup on the provider's end.",
            "action": "Hang tight and retry in a minute or two.",
        },
        "formal": {
            "what": "The language model service is currently unavailable.",
            "why": "The upstream AI provider may be experiencing downtime, maintenance, or elevated traffic.",
            "action": "Please retry after a brief interval. If the issue persists, contact support.",
        },
    },
    ErrorType.INVALID_INPUT: {
        "direct": {
            "what": "Something's off with your input.",
            "why": "The prompt may be too short, too long, or contain invalid characters.",
            "action": "Check the input requirements and try again.",
        },
        "casual": {
            "what": "Hmm, that input didn't quite work.",
            "why": "Could be too short, too long, or just not in the right format.",
            "action": "Double-check the requirements and give it another go.",
        },
        "formal": {
            "what": "The provided input does not meet validation requirements.",
            "why": "Input must conform to specified constraints including length, format, and character requirements.",
            "action": "Please review the input specifications and resubmit.",
        },
    },
    ErrorType.MEMORY_WRITE_FAILED: {
        "direct": {
            "what": "Failed to save your session to memory.",
            "why": "A database or memory service write operation failed.",
            "action": "Your prompt still works — just the memory backup failed. You can continue using the service.",
        },
        "casual": {
            "what": "Couldn't save this to your memory — no big deal though.",
            "why": "Sometimes the memory service hiccups. Your prompt result is still good.",
            "action": "Keep going — this won't affect your current session.",
        },
        "formal": {
            "what": "Memory persistence operation failed.",
            "why": "A write operation to the conversational memory store encountered an error.",
            "action": "This does not affect your current request. Future sessions may have reduced personalization.",
        },
    },
    ErrorType.QUALITY_GATE_FAILED: {
        "direct": {
            "what": "The prompt quality check failed.",
            "why": "The generated prompt didn't meet minimum quality standards.",
            "action": "Try rephrasing your prompt with more detail or clarity.",
        },
        "casual": {
            "what": "The quality gate caught something — the output wasn't great.",
            "why": "Sometimes the AI generates prompts that don't meet our standards. We'd rather tell you than give you something mediocre.",
            "action": "Try again with a more detailed prompt.",
        },
        "formal": {
            "what": "The generated prompt did not pass quality assurance validation.",
            "why": "Quality gate evaluation determined the output does not meet minimum standards for specificity, clarity, or actionability.",
            "action": "Please provide additional context or detail in your input and retry.",
        },
    },
    ErrorType.TRIAL_LIMIT_EXCEEDED: {
        "direct": {
            "what": "You've used all your free trials.",
            "why": "Anonymous users get 2 trial improvements per 24 hours.",
            "action": "Sign up for a free account for unlimited improvements.",
        },
        "casual": {
            "what": "You've burned through your free trials — 2 per day is the limit for guests.",
            "why": "We give a taste of PromptForge for free, but unlimited runs need an account.",
            "action": "Create a free account and keep going!",
        },
        "formal": {
            "what": "Your anonymous trial usage limit has been reached.",
            "why": "Trial users are permitted 2 prompt improvements per 24-hour period.",
            "action": "Please register an account to continue using the service without limitations.",
        },
    },
    ErrorType.UNKNOWN: {
        "direct": {
            "what": "Something went wrong on our end.",
            "why": "An unexpected error occurred during processing.",
            "action": "Try again. If it keeps happening, let us know.",
        },
        "casual": {
            "what": "Oops — something broke on our end.",
            "why": "We hit an unexpected error. Our team gets notified automatically.",
            "action": "Give it another shot. If it keeps happening, reach out.",
        },
        "formal": {
            "what": "An unexpected error occurred during processing.",
            "why": "The system encountered an unhandled exception. This has been logged for investigation.",
            "action": "Please retry your request. If the issue persists, contact support with the error details.",
        },
    },
}


def get_error_message(
    error_type: ErrorType,
    user_tone: str = "direct",
    retry_after_minutes: Optional[int] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a personality-driven error message for the given error type.

    Args:
        error_type: The ErrorType enum value for the error
        user_tone: User's preferred tone from profile ('direct', 'casual', 'formal')
        retry_after_minutes: Optional retry time to include in the message
        extra_context: Additional context dict (e.g., {'signup_url': '...'})

    Returns:
        Dict with keys: error_type, what, why, action, full_message, retry_after_minutes, extra_context

    Example:
        error = get_error_message(
            ErrorType.RATE_LIMIT,
            user_tone="casual",
            retry_after_minutes=5,
        )
        raise HTTPException(status_code=429, detail=error["full_message"])
    """
    # Normalize tone — fallback to direct if invalid
    valid_tones = {"direct", "casual", "formal"}
    tone = user_tone if user_tone in valid_tones else "direct"

    # Get the tone-specific messages for this error type
    error_data = PERSONALITY_TONES.get(error_type, PERSONALITY_TONES[ErrorType.UNKNOWN])
    tone_data = error_data.get(tone, error_data["direct"])

    # Build the full message
    what = tone_data["what"]
    why = tone_data["why"]
    action = tone_data["action"]

    # Add retry info if applicable
    if retry_after_minutes:
        retry_text = f" Retry after {retry_after_minutes} minute{'s' if retry_after_minutes != 1 else ''}."
        action += retry_text

    # Add extra context if applicable (e.g., signup URL)
    if extra_context:
        if "signup_url" in extra_context:
            action += f" Sign up here: {extra_context['signup_url']}"

    full_message = f"{what} {why} {action}"

    result = {
        "error_type": error_type.value if isinstance(error_type, ErrorType) else str(error_type),
        "what": what,
        "why": why,
        "action": action,
        "full_message": full_message,
        "retry_after_minutes": retry_after_minutes,
        "tone_used": tone,
    }

    logger.info(f"[error_messages] {error_type.value} → tone={tone}")

    return result
