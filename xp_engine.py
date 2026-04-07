import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Constants for Tier Progression
TIERS = [
    {"name": "Bronze (Analyst)", "min_xp": 0},
    {"name": "Silver (Practitioner)", "min_xp": 500},
    {"name": "Gold (Architect)", "min_xp": 2000},
    {"name": "Kira-Class (Forge-Master)", "min_xp": 5000}
]

def get_tier_from_xp(total_xp: int) -> str:
    """Determine loyalty tier from total XP."""
    current_tier = TIERS[0]["name"]
    for tier in TIERS:
        if total_xp >= tier["min_xp"]:
            current_tier = tier["name"]
    return current_tier

def calculate_forge_xp(
    quality_score: Dict[str, float],
    domain: str,
    user_dominant_domains: List[str],
    current_streak: int,
    is_clarification_resolved: bool = False
) -> Dict[str, Any]:
    """
    Calculates the XP earned for a single prompt forge.
    Rewards High-Resolution Engineering (Quality, Mastery, Feedback, Consistency).
    
    Args:
        quality_score: Dict with specificity, clarity, actionability, overall (1-5)
        domain: The domain of the prompt just forged
        user_dominant_domains: The user's current top domains
        current_streak: Current day streak
        is_clarification_resolved: True if this prompt resolved a clarification loop
        
    Returns:
        Dict with total_xp_earned and a breakdown
    """
    xp_breakdown = {}
    total_xp = 0
    
    # 1. Base Quality XP (Overall Score x 10)
    overall_quality = quality_score.get("overall", 3.0)
    base_xp = int(overall_quality * 10)
    xp_breakdown["quality"] = base_xp
    total_xp += base_xp
    
    # 2. Polymath Bonus (Mastery)
    # If the user forged a high-quality prompt in a domain NOT in their dominant domains
    if domain.lower() not in [d.lower() for d in user_dominant_domains] and overall_quality >= 4.0:
        polymath_xp = 25
        xp_breakdown["polymath_bonus"] = polymath_xp
        total_xp += polymath_xp
        
    # 3. Teaching/Feedback Bonus
    # Engaging with Kira's clarification questions proves proactive teaching
    if is_clarification_resolved:
        teaching_xp = 15
        xp_breakdown["teaching_bonus"] = teaching_xp
        total_xp += teaching_xp
        
    # 4. Consistency Streak Multiplier
    multiplier = 1.0
    if current_streak >= 7:
        multiplier = 1.5
    elif current_streak >= 3:
        multiplier = 1.2
        
    if multiplier > 1.0:
        streak_bonus = int(total_xp * (multiplier - 1.0))
        xp_breakdown["streak_bonus"] = streak_bonus
        total_xp += streak_bonus
        
    return {
        "earned_xp": total_xp,
        "breakdown": xp_breakdown
    }
