# voice/moderation.py
# ─────────────────────────────────────────────
# Content Moderation for Voice Transcriptions
#
# WHY: Voice inputs can contain sensitive information or harmful content.
# Moderation scans transcripts to flag security events for review.
# This is a DETECTION system — it logs and flags but does NOT block,
# allowing users to still use voice features while maintaining audit trail.
#
# Scans for:
#   - Threats/violence keywords
#   - PII patterns (credit cards, SSNs, phone numbers, emails)
#   - Hate speech patterns
#
# Results are attached to response metadata for audit logging.
# ─────────────────────────────────────────────

import re
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """
    Result of content moderation scan.

    Attributes:
        is_clean: Whether content passed without flags
        flags: List of detected flag categories
        pii_detected: Whether PII patterns were found
        pii_types: Types of PII found (email, phone, credit_card, ssn)
        flagged_text: Original text snippets that triggered flags
        severity: Overall severity level (low, medium, high)
        scanned_at: ISO timestamp of scan
    """
    is_clean: bool = True
    flags: List[str] = field(default_factory=list)
    pii_detected: bool = False
    pii_types: List[str] = field(default_factory=list)
    flagged_text: List[str] = field(default_factory=list)
    severity: str = "low"
    scanned_at: str = ""

    def __post_init__(self):
        if not self.scanned_at:
            self.scanned_at = datetime.now(timezone.utc).isoformat()


# ── PII Detection Patterns ────────────────────

# Email addresses
_PII_EMAIL = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# US Phone numbers (various formats)
_PII_PHONE = re.compile(r'\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b')

# US Social Security Numbers
_PII_SSN = re.compile(r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b')

# Credit card numbers (basic Luhn-like patterns, 13-19 digits)
_PII_CREDIT_CARD = re.compile(r'\b(?:\d{4}[-.\s]?){3}\d{1,4}\b')

# IP addresses
_PII_IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


# ── Threat/Violence Keywords ──────────────────

_THREAT_KEYWORDS = [
    "kill", "murder", "bomb", "explosive", "weapon", "shoot",
    "suicide", "self-harm", "hurt myself", "end it all",
    "destroy", "attack", "threaten", "terrorism",
]

# ── Hate Speech Indicators ─────────────────────

_HATE_INDICATORS = [
    # General slur patterns (not listing actual slurs — pattern-based detection)
    # These catch common hate speech structures
    "hate.*group", "white.*supremac", "racial.*superior",
    "ethnic.*cleans", "genocide",
]


def _detect_pii(text: str) -> List[str]:
    """
    Detect personally identifiable information in text.

    Args:
        text: Text to scan

    Returns:
        List of PII types found
    """
    pii_types = []

    if _PII_EMAIL.search(text):
        pii_types.append("email")
    if _PII_PHONE.search(text):
        pii_types.append("phone")
    if _PII_SSN.search(text):
        pii_types.append("ssn")
    if _PII_CREDIT_CARD.search(text):
        pii_types.append("credit_card")
    if _PII_IP.search(text):
        pii_types.append("ip_address")

    return pii_types


def _detect_threats(text: str) -> List[str]:
    """
    Detect threat/violence keywords in text.

    Args:
        text: Lowercase text to scan

    Returns:
        List of matched threat keywords
    """
    text_lower = text.lower()
    matches = []

    for keyword in _THREAT_KEYWORDS:
        if keyword in text_lower:
            matches.append(keyword)

    return matches


def _detect_hate_speech(text: str) -> List[str]:
    """
    Detect hate speech patterns in text.

    Args:
        text: Text to scan

    Returns:
        List of matched hate speech patterns
    """
    text_lower = text.lower()
    matches = []

    for pattern in _HATE_INDICATORS:
        if re.search(pattern, text_lower):
            matches.append(pattern)

    return matches


def moderate_transcription(transcript: str) -> ModerationResult:
    """
    Scan a voice transcription for moderation flags.

    WHY: Called after successful transcription to detect and log
    security-relevant content. Results are attached to the response
    metadata but do NOT block the request.

    Args:
        transcript: Transcribed text from voice input

    Returns:
        ModerationResult with flags and severity assessment

    Example:
        result = moderate_transcription("Call me at 555-123-4567")
        # result.pii_detected = True
        # result.pii_types = ["phone"]
        # result.is_clean = False
    """
    if not transcript or not transcript.strip():
        return ModerationResult(is_clean=True)

    flags = []
    pii_types = []
    flagged_text = []
    severity = "low"

    # ── PII Detection ──
    pii_types = _detect_pii(transcript)
    if pii_types:
        flags.append("pii_detected")
        severity = "medium"
        logger.info(
            f"[voice/moderation] PII detected: types={pii_types} "
            f"text_length={len(transcript)}"
        )

    # ── Threat Detection ──
    threat_keywords = _detect_threats(transcript)
    if threat_keywords:
        flags.append("threat_keywords")
        severity = "high"
        flagged_text.extend(threat_keywords)
        logger.warning(
            f"[voice/moderation] threat keywords: {threat_keywords} "
            f"text_length={len(transcript)}"
        )

    # ── Hate Speech Detection ──
    hate_patterns = _detect_hate_speech(transcript)
    if hate_patterns:
        flags.append("hate_speech")
        severity = "high"
        flagged_text.extend(hate_patterns)
        logger.warning(
            f"[voice/moderation] hate speech patterns: {hate_patterns} "
            f"text_length={len(transcript)}"
        )

    is_clean = len(flags) == 0

    # Log scan result
    if is_clean:
        logger.debug(f"[voice/moderation] clean: text_length={len(transcript)}")
    else:
        logger.info(
            f"[voice/moderation] flagged: flags={flags} severity={severity} "
            f"text_length={len(transcript)}"
        )

    return ModerationResult(
        is_clean=is_clean,
        flags=flags,
        pii_detected=len(pii_types) > 0,
        pii_types=pii_types,
        flagged_text=flagged_text,
        severity=severity,
    )


def get_moderation_summary(results: List[ModerationResult]) -> dict:
    """
    Generate summary statistics from multiple moderation results.

    Args:
        results: List of ModerationResult objects

    Returns:
        Summary dict with counts and breakdown
    """
    total = len(results)
    flagged = sum(1 for r in results if not r.is_clean)
    high_severity = sum(1 for r in results if r.severity == "high")

    flag_counts = {}
    for result in results:
        for flag in result.flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    return {
        "total_scanned": total,
        "flagged_count": flagged,
        "flagged_pct": round(flagged / total * 100, 1) if total > 0 else 0,
        "high_severity_count": high_severity,
        "flag_breakdown": flag_counts,
    }
