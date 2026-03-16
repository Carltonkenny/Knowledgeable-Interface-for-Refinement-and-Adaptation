# agents/context/scorer.py
"""
Input Quality Scoring + Domain Signal Detection.

CONTAINS:
    1. QualityScore dataclass — Type-safe score representation
    2. QualityThresholds — Configurable thresholds
    3. score_input_quality() — Pre-routing quality assessment
    4. detect_domain_signals() — Lightweight domain hint detection

RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete
    - Pure functions (testable)
    - Configuration over hardcoding

DESIGN PRINCIPLE:
    score_input_quality() scores STRUCTURAL quality only.
    detect_domain_signals() detects DOMAIN hints separately.
    Domain Agent does the REAL classification (LLM-based).
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class QualityScore:
    """Type-safe representation of input quality score."""
    score: int  # 1-3
    word_count: int
    has_context: bool
    has_constraints: bool
    has_domain: bool
    recommendation: str  # "light" | "standard" | "full"


class QualityThresholds:
    """Configurable quality scoring thresholds."""
    
    WORD_COUNT_MODERATE: int = 15
    WORD_COUNT_RICH: int = 40
    
    CONTEXT_SIGNALS: List[str] = None
    CONSTRAINT_SIGNALS: List[str] = None
    DOMAIN_SIGNALS: List[str] = None
    
    def __init__(self):
        self.CONTEXT_SIGNALS = [
            "for ", "to ", "audience", "who ", "because", "so that",
            "targeting", "aimed at", "designed for", "users who"
        ]
        self.CONSTRAINT_SIGNALS = [
            "word", "sentence", "paragraph", "tone", "formal", "casual",
            "technical", "simple", "short", "long", "bullet", "list",
            "email", "script", "outline", "summary", "brief"
        ]
        self.DOMAIN_SIGNALS = [
            "python", "javascript", "api", "marketing", "essay", "blog",
            "instagram", "youtube", "email", "pitch", "resume", "react",
            "database", "sql", "startup", "product"
        ]


def score_input_quality(
    message: str,
    has_session_history: bool,
    thresholds: QualityThresholds = None
) -> QualityScore:
    """
    Score the quality of an incoming user message to determine pipeline depth.
    
    Called BEFORE routing to swarm. Prevents over-engineering thin inputs
    and ensures full pipeline fires only when warranted.
    
    Args:
        message: Raw user message string.
        has_session_history: Whether this user has prior session context.
        thresholds: Optional QualityThresholds instance. Uses defaults if None.
    
    Returns:
        QualityScore dataclass with:
            - score: int 1-3 (1=thin, 2=moderate, 3=rich)
            - word_count: int
            - has_context: bool
            - has_constraints: bool
            - has_domain: bool
            - recommendation: str ("light" | "standard" | "full")
    
    Pipeline behavior by score:
        1 (thin)     → Standard engineering. Add role, audience, basic constraints.
        2 (moderate) → Full pipeline. Some elements present, fill gaps.
        3 (rich)     → Full pipeline. Preserve user's structure, sharpen details.
    
    Example:
        >>> score = score_input_quality("fix my code", False)
        >>> score.score
        1
        >>> score.recommendation
        "light"
        
        >>> score = score_input_quality("write a 3-email cold outreach for SaaS...", True)
        >>> score.score
        3
        >>> score.recommendation
        "full"
    """
    if thresholds is None:
        thresholds = QualityThresholds()
    
    word_count = len(message.split())
    
    # Context signals
    has_context = _has_signal_words(message, thresholds.CONTEXT_SIGNALS)
    
    # Constraint signals
    has_constraints = _has_signal_words(message, thresholds.CONSTRAINT_SIGNALS)
    
    # Domain signals
    has_domain = _has_signal_words(message, thresholds.DOMAIN_SIGNALS)
    
    # Calculate score
    score = _calculate_score(word_count, has_context, has_constraints, has_domain)
    
    # Determine recommendation
    recommendation = _get_recommendation(score)
    
    return QualityScore(
        score=score,
        word_count=word_count,
        has_context=has_context,
        has_constraints=has_constraints,
        has_domain=has_domain,
        recommendation=recommendation
    )


def _has_signal_words(message: str, signals: List[str]) -> bool:
    """
    Check if message contains any signal words.
    
    Args:
        message: User message to analyze
        signals: List of signal words to check
        
    Returns:
        True if any signal word found, False otherwise
        
    Example:
        >>> _has_signal_words("write for my audience", ["for ", "audience"])
        True
    """
    message_lower = message.lower()
    return any(signal in message_lower for signal in signals)


def _calculate_score(
    word_count: int,
    has_context: bool,
    has_constraints: bool,
    has_domain: bool
) -> int:
    """
    Calculate quality score from signals.
    
    Args:
        word_count: Number of words in message
        has_context: Whether context signals present
        has_constraints: Whether constraint signals present
        has_domain: Whether domain signals present
        
    Returns:
        Quality score 1-3
        
    Scoring logic:
        - Start at 1 (thin)
        - +1 if word_count > 15
        - +1 if word_count > 40
        - Cap at 2 if has_context
        - Cap at 3 if has_constraints AND has_domain
    """
    score = 1  # Start thin
    
    if word_count > 15:
        score += 1
    if word_count > 40:
        score += 1
    if has_context:
        score = max(score, 2)
    if has_constraints and has_domain:
        score = max(score, 3)
    
    return min(score, 3)


def _get_recommendation(score: int) -> str:
    """
    Get pipeline recommendation from score.

    Args:
        score: Quality score 1-3

    Returns:
        Recommendation string

    Example:
        >>> _get_recommendation(1)
        'light'
        >>> _get_recommendation(3)
        'full'
    """
    return {1: "light", 2: "standard", 3: "full"}[score]


# ═══ DOMAIN SIGNAL DETECTION (SEPARATE FROM SCORING) ═════════════════════════

def detect_domain_signals(message: str) -> List[str]:
    """
    Detect domain hints from message — lightweight pre-check for routing.

    This is NOT the real domain classification — that's Domain Agent's job.
    This is a fast keyword-based hint for routing optimization.

    RULES.md:
    - Pure function (testable, no side effects)
    - Configuration over hardcoding
    - Fast path for routing decisions

    Use cases:
    - Skip Domain Agent if keyword confidence is already high
    - Pre-route to domain-specific prompt templates
    - Early personalization before full analysis

    Args:
        message: User's message

    Returns:
        List of domain hints: ["coding", "marketing", etc.] or []

    Example:
        >>> detect_domain_signals("write a FastAPI endpoint")
        ['coding']
        >>> detect_domain_signals("create an email sequence")
        ['marketing']
        >>> detect_domain_signals("hello")
        []
    """
    signals = []
    message_lower = message.lower()

    # Coding/tech signals
    coding_keywords = [
        "python", "javascript", "typescript", "java", "rust", "go",
        "fastapi", "flask", "django", "react", "vue", "angular",
        "api", "endpoint", "function", "method", "class", "interface",
        "database", "sql", "nosql", "mongodb", "postgresql", "mysql",
        "code", "script", "program", "debug", "deploy", "docker",
        "async", "await", "promise", "callback", "middleware", "router"
    ]
    if any(kw in message_lower for kw in coding_keywords):
        signals.append("coding")

    # Marketing/writing signals
    marketing_keywords = [
        "email", "newsletter", "outreach", "copy", "blog", "post",
        "sequence", "campaign", "audience", "readers", "subscribers",
        "cold email", "linkedin", "twitter", "social media",
        "pitch", "proposal", "presentation", "sales", "conversion"
    ]
    if any(kw in message_lower for kw in marketing_keywords):
        signals.append("marketing")

    # Data/analysis signals
    data_keywords = [
        "analyze", "data", "chart", "graph", "visualization",
        "statistics", "metrics", "dashboard", "report", "insights",
        "machine learning", "ml", "prediction", "model", "training"
    ]
    if any(kw in message_lower for kw in data_keywords):
        signals.append("data")

    # Creative signals
    creative_keywords = [
        "story", "poem", "script", "creative", "fiction",
        "character", "scene", "narrative", "dialogue", "plot",
        "novel", "short story", "screenplay", "verse"
    ]
    if any(kw in message_lower for kw in creative_keywords):
        signals.append("creative")

    # Academic/research signals
    academic_keywords = [
        "research", "paper", "thesis", "essay", "citation",
        "literature review", "methodology", "hypothesis", "study"
    ]
    if any(kw in message_lower for kw in academic_keywords):
        signals.append("academic")

    return signals
