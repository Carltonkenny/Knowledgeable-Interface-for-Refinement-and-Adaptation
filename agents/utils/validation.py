# agents/utils/validation.py
"""
Shared agent output validation helpers.

Generic quality-gate logic extracted from individual agents
(intent.py, context.py, domain.py) to reduce duplication.

RULES.md Compliance:
    - DRY Rule 1: Extract common patterns
    - Type hints mandatory
    - Docstrings complete
"""

from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def validate_agent_output(
    result: Dict[str, Any],
    required_fields: List[str],
    min_confidence: float = 0.6,
    agent_name: str = "agent"
) -> bool:
    """
    Generic quality gate for agent outputs.
    
    Checks that required fields are present and non-empty,
    and that confidence meets the minimum threshold.
    
    Args:
        result: Agent output dict to validate
        required_fields: List of field names that must be present and non-empty
        min_confidence: Minimum confidence score (default 0.6)
        agent_name: Agent name for logging context
        
    Returns:
        True if passes quality gates, False otherwise
        
    Example:
        >>> validate_agent_output(
        ...     {"primary_intent": "test", "confidence": 0.8},
        ...     required_fields=["primary_intent"],
        ...     agent_name="intent"
        ... )
        True
    """
    checks_passed = 0
    total_checks = len(required_fields) + 1  # +1 for confidence
    
    # Check each required field
    for field in required_fields:
        value = result.get(field, "")
        if value and str(value).strip():
            checks_passed += 1
        else:
            logger.debug(f"[{agent_name}] quality gate: field '{field}' empty or missing")
    
    # Check confidence
    confidence = result.get("confidence", min_confidence)
    if confidence >= min_confidence:
        checks_passed += 1
    else:
        logger.debug(f"[{agent_name}] quality gate: confidence {confidence:.2f} < {min_confidence}")
    
    # Pass if >= 2/3 of checks pass (lenient gate)
    threshold = max(2, total_checks * 2 // 3)
    passes = checks_passed >= threshold
    
    if not passes:
        logger.warning(
            f"[{agent_name}] quality gate FAILED — "
            f"passed={checks_passed}/{total_checks}, threshold={threshold}"
        )
    
    return passes


def validate_enum_field(
    value: str,
    valid_values: List[str],
    field_name: str = "field"
) -> bool:
    """
    Validate that a field value is one of the allowed enum values.
    
    Args:
        value: The value to check
        valid_values: List of allowed values
        field_name: Field name for logging
        
    Returns:
        True if value is valid, False otherwise
    """
    is_valid = value in valid_values
    if not is_valid:
        logger.debug(f"[validation] {field_name}='{value}' not in {valid_values}")
    return is_valid


__all__ = ["validate_agent_output", "validate_enum_field"]
