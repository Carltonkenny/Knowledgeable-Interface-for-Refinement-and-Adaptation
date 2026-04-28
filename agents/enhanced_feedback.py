# agents/enhanced_feedback.py
# Enhanced Feedback System for Conversation Flow

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_processing_feedback(
    orchestrator_decision: Dict[str, Any],
    session_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive feedback for user about processing steps
    
    Args:
        orchestrator_decision: Decision from Kira orchestrator
        session_result: Result from swarm processing (optional)
        
    Returns:
        Dictionary with feedback information for user
    """
    try:
        feedback = {
            "user_message": orchestrator_decision.get("user_facing_message", ""),
            "processing_steps": [],
            "agent_execution": [],
            "final_prompt": "",
            "improvement_notes": [],
            "status": "processing"
        }
        
        # Add agent execution details if available
        if session_result:
            # Extract agent execution information
            feedback["agent_execution"] = [
                f"Intent analysis completed",
                f"Context analysis completed", 
                f"Domain analysis completed"
            ]
            
            # Add improvement notes
            improvements = session_result.get('changes_made', [])
            if improvements:
                feedback["improvement_notes"] = [
                    f"Improvements made: {', '.join(improvements[:3])}"
                ]
                
            # Final prompt
            feedback["final_prompt"] = session_result.get('improved_prompt', '')
            feedback["status"] = "completed"
        
        # Add processing steps
        route = orchestrator_decision.get("route", "SWARM")
        if route == "CONVERSATION":
            feedback["processing_steps"] = ["Greetings response prepared"]
        elif route == "FOLLOWUP":
            feedback["processing_steps"] = ["Following up on previous request"]
        elif route == "CLARIFICATION":
            feedback["processing_steps"] = ["Seeking clarification"]
        elif route == "SWARM":
            feedback["processing_steps"] = [
                "Analyzing intent",
                "Evaluating context",
                "Identifying domain",
                "Generating improved prompt"
            ]
        
        logger.debug(f"[feedback] generated feedback for decision: {route}")
        return feedback
        
    except Exception as e:
        logger.error(f"[feedback] failed to generate feedback: {e}")
        return {
            "user_message": "Processing your request...",
            "processing_steps": ["Analyzing request"],
            "status": "processing"
        }

def finalize_conversation(
    final_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Finalize conversation with clear presentation
    
    Args:
        final_result: Result from prompt engineering
        
    Returns:
        Finalized conversation data with recommendations
    """
    try:
        # Extract quality score for recommendations
        quality_score = final_result.get("quality_score", {})
        overall_score = quality_score.get("overall", 0)
        
        # Generate recommendations based on quality
        recommendations = generate_recommendations(overall_score)
        
        # Build final presentation
        final_data = {
            "final_prompt": final_result.get("improved_prompt", ""),
            "improvement_explanation": final_result.get("changes_made", []),
            "quality_score": quality_score,
            "recommendations": recommendations,
            "latency_ms": final_result.get("agent_latencies", {}).get("prompt_engineer", 0)
        }
        
        logger.info(f"[feedback] finalized conversation with quality {overall_score}")
        return final_data
        
    except Exception as e:
        logger.error(f"[feedback] failed to finalize conversation: {e}")
        return {
            "final_prompt": "",
            "improvement_explanation": [],
            "quality_score": {},
            "recommendations": ["Check your request for clarity"],
            "latency_ms": 0
        }

def generate_recommendations(quality_score: float) -> List[str]:
    """
    Generate helpful recommendations based on prompt quality
    
    Args:
        quality_score: Overall quality score (0-5)
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    if quality_score < 2.5:
        recommendations.extend([
            "Consider adding more specific details to your request",
            "Include more context about your goals",
            "Specify desired outcomes more clearly"
        ])
    elif quality_score < 4.0:
        recommendations.extend([
            "Try making your request more action-oriented",
            "Consider specifying your target audience",
            "Add more concrete examples if relevant"
        ])
    else:
        recommendations.extend([
            "Great prompt! This should work well for your needs",
            "Consider sharing this with others for feedback",
            "This prompt is well-structured and clear"
        ])
        
    return recommendations
