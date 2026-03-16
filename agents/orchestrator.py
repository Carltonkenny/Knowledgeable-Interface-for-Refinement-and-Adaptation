# agents/orchestrator.py
# ─────────────────────────────────────────────
# Kira Orchestrator — LangGraph Node
#
# Kira is NOT just a router — she is a personality with routing capability.
# She is the face of PromptForge: direct, warm, slightly opinionated.
#
# Character Constants (from RULES.md — NEVER change):
# - Direct, warm, slightly opinionated — like a senior collaborator
# - NEVER says: "Certainly", "Great question", "Of course", etc.
# - NEVER asks more than ONE question per response
# - NEVER explains her process in detail
# - Speed is a personality trait — every interaction feels deliberate
#
# Technical Specs:
# - Model: Fast LLM (via Pollinations paid tier)
# - Max tokens: 150
# - Temperature: 0.1
# - Response time target: 300-500ms
#
# Routing Logic (in order):
# 1. message.length < 10 → CONVERSATION
# 2. pending_clarification → inject answer, fire swarm
# 3. Modification phrases → FOLLOWUP (1 LLM call)
# 4. ambiguity_score > 0.7 → CLARIFICATION (ask 1 question)
# 5. Otherwise → SWARM (4 agents)
# ─────────────────────────────────────────────

import os
import json
import time
import logging
import re
from typing import Any, Dict, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_fast_llm, get_llm
from utils import parse_json_response, format_history
from memory.langmem import query_langmem
from agents.prompts.orchestrator import build_orchestrator_prompt
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ═══ KIRA CHARACTER CONSTANTS — NEVER CHANGE ═══

KIRA_FORBIDDEN_PHRASES = [
    "Certainly",
    "Great question",
    "Of course",
    "I'd be happy to",
    "Let me help you",
    "No problem",
    "Sure!",
    "Absolutely",
    "Happy to help",
]

KIRA_MAX_TOKENS = 150
KIRA_TEMPERATURE = 0.1
KIRA_MAX_QUESTIONS = 1

# ═══ KIRA SYSTEM PROMPT ═══

KIRA_SYSTEM_PROMPT = f"""You are Kira, a prompt engineering orchestrator.

PERSONALITY:
- Direct, warm, slightly opinionated — like a senior collaborator
- You NEVER say: {", ".join(KIRA_FORBIDDEN_PHRASES)}
- You NEVER ask more than {KIRA_MAX_QUESTIONS} question(s) per response
- You NEVER explain your process in detail — you just do it
- Speed is a personality trait — keep responses snappy (2-4 sentences max)

YOUR JOB:
1. Read the user's message and context
2. Decide what to do:
   - CONVERSATION: User is being brief (<10 chars), greeting, or small talk
   - FOLLOWUP: User wants to modify their last prompt ("make it longer", "add detail")
   - CLARIFICATION: User's request is ambiguous — you need ONE clarifying question
   - SWARM: User wants a new prompt engineered — route to appropriate agents

3. Return structured JSON with your decision

RESPONSE FORMAT (valid JSON only):
{{
  "user_facing_message": "What the user sees immediately (2-4 sentences max)",
  "proceed_with_swarm": true/false,
  "agents_to_run": ["intent", "domain"],
  "clarification_needed": true/false,
  "clarification_question": "Your one question if clarification needed, else null",
  "skip_reasons": {{"context": "reason or null"}},
  "tone_used": "direct" | "casual" | "technical",
  "profile_applied": true/false
}}

ROUTING RULES (apply in order):
1. message.length < 10 → CONVERSATION (user is being brief)
2. Modification phrases detected → FOLLOWUP (1 LLM call, skip full swarm)
3. ambiguity_score > 0.7 → CLARIFICATION (ask ONE question)
4. Otherwise → SWARM (select agents based on confidence)

AGENT SELECTION LOGIC:
- Always run "intent" unless message is crystal clear
- Skip "context" if no session history (conversation_history is empty)
- Skip "domain" if user profile has domain at >85% confidence
- "prompt_engineer" ALWAYS runs (never skip) — but handled in workflow, not here

TONE ADAPTATION:
- If user_profile.preferred_tone = "casual" → use "casual"
- If user_profile.preferred_tone = "technical" → use "technical"
- Otherwise → use "direct" (default)
"""


# ═══ HELPER FUNCTIONS ═══

def detect_modification_phrases(message: str) -> bool:
    """
    Check if message contains modification phrases.
    Used for FOLLOWUP detection.
    
    Args:
        message: User's message
        
    Returns:
        True if modification detected, False otherwise
        
    Examples:
        >>> detect_modification_phrases("make it longer")
        True
        >>> detect_modification_phrases("write a story")
        False
    """
    modification_phrases = [
        "make it",
        "change it",
        "change the",
        "adjust",
        "modify",
        "add",
        "remove",
        "shorter",
        "longer",
        "better",
        "different",
        "more detail",
        "less formal",
        "more formal",
        "simplify",
        "expand",
    ]
    
    message_lower = message.lower()
    return any(phrase in message_lower for phrase in modification_phrases)


def calculate_ambiguity_score(message: str, history: List[Dict]) -> float:
    """
    Simple heuristic for ambiguity detection.
    Returns 0.0-1.0 (higher = more ambiguous).
    
    Args:
        message: User's message
        history: Conversation history
        
    Returns:
        Ambiguity score 0.0-1.0
        
    Scoring:
        - Short messages (<20 chars): +0.3
        - Questions (contains "?"): +0.2
        - Vague words: +0.3
        - No context (first message): +0.2
    """
    score = 0.0
    
    # Short messages are more ambiguous
    if len(message.strip()) < 20:
        score += 0.3
    
    # Questions are often ambiguous
    if "?" in message:
        score += 0.2
    
    # Vague words
    vague_words = ["something", "thing", "stuff", "whatever", "maybe", "perhaps", "anything"]
    if any(word in message.lower() for word in vague_words):
        score += 0.3
    
    # No context (first message)
    if len(history) == 0:
        score += 0.2
    
    return min(score, 1.0)


# ═══ ORCHESTRATOR NODE ═══

def orchestrator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kira orchestrator: reads profile + history, decides routing.
    
    This is the main entry point for Kira. It:
    1. Checks for pending clarification FIRST
    2. Reads user profile for tone adaptation
    3. Analyzes message for routing decision
    4. Returns structured JSON with decision
    
    Args:
        state: Current state dict with message and context
        
    Returns:
        Dict with orchestrator_decision and updated state fields
        
    Raises:
        Exception: If LLM call fails after retries (fallback to CONVERSATION)
    """
    start_time = time.time()
    
    try:
        llm = get_fast_llm()
        
        # Extract from state
        message = state.get("message", "")
        user_profile = state.get("user_profile", {})
        conversation_history = state.get("conversation_history", [])
        pending_clarification = state.get("pending_clarification", False)
        
        # ═══ CHECK FOR PENDING CLARIFICATION FIRST ═══
        if pending_clarification:
            logger.info(f"[kira] pending clarification — injecting answer, firing swarm")
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "orchestrator_decision": {
                    "user_facing_message": "Got it — let me work with that.",
                    "proceed_with_swarm": True,
                    "agents_to_run": ["intent", "domain"],
                    "clarification_needed": False,
                    "clarification_question": None,
                    "skip_reasons": {"context": "clarification just resolved"},
                    "tone_used": "direct",
                    "profile_applied": bool(user_profile),
                },
                "pending_clarification": False,  # Clear flag
                "proceed_with_swarm": True,
                "user_facing_message": "Got it — let me work with that.",
                "latency_ms": latency_ms,
            }
        
        # ═══ QUICK CHECKS (before LLM call) ═══
        
        # Check 1: Very brief input → CONVERSATION
        if len(message.strip()) < 10:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "orchestrator_decision": {
                    "user_facing_message": "Hey! What would you like to improve today?",
                    "proceed_with_swarm": False,
                    "agents_to_run": [],
                    "clarification_needed": False,
                    "clarification_question": None,
                    "skip_reasons": {},
                    "tone_used": "direct",
                    "profile_applied": False,
                },
                "user_facing_message": "Hey! What would you like to improve today?",
                "proceed_with_swarm": False,
                "latency_ms": latency_ms,
            }
        
        # Check 2: Modification phrases → FOLLOWUP
        is_followup = detect_modification_phrases(message)
        
        if is_followup:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "orchestrator_decision": {
                    "user_facing_message": "Got it — refining now.",
                    "proceed_with_swarm": True,
                    "agents_to_run": ["intent"],
                    "clarification_needed": False,
                    "clarification_question": None,
                    "skip_reasons": {},
                    "tone_used": "direct",
                    "profile_applied": False,
                },
                "user_facing_message": "Got it — refining now.",
                "proceed_with_swarm": True,
                "latency_ms": latency_ms,
            }
        
        # ═══ BUILD CONTEXT FOR LLM ═══

        # Query LangMem for user's past memories (BEFORE LLM call)
        langmem_context = []  # Default to empty if user_id not available
        langmem_user_id = state.get("user_id")
        if langmem_user_id:
            langmem_context = query_langmem(
                user_id=langmem_user_id,
                query=message,
                top_k=5
            )
        
        history_context = "\n".join([
            f"{t.get('role', 'USER').upper()}: {t.get('message', '')[:100]}"
            for t in conversation_history[-3:]
        ]) if conversation_history else "No previous conversation"

        profile_context = f"User's preferred tone: {user_profile.get('preferred_tone', 'not set')}" if user_profile else "No profile available"

        # ═══ FR-2: MEMORY CONTENT FOR KIRA (SPEC V1) ═══
        # Show Kira actual memory content, not just count
        if langmem_context:
            profile_context += f"\nPast memories: {len(langmem_context)} relevant memories found"
            # Add content preview for better routing decisions (handle edge cases)
            try:
                memory_preview = "\n".join([
                    f"  - {m.get('content', 'N/A')[:60] if m.get('content') else 'N/A'}... (quality: {(m.get('quality_score') or {}).get('overall', 0):.1f})"
                    for m in langmem_context[:3]  # Show top 3 only
                ])
                profile_context += f"\nRecent high-quality sessions:\n{memory_preview}"
                logger.debug(f"[kira] memory preview added: {len(langmem_context)} memories")
            except Exception as e:
                logger.warning(f"[kira] memory preview formatting failed: {e}")
                # Fallback: just show count
        else:
            logger.debug("[kira] no langmem context available")
        
        # Calculate ambiguity score
        ambiguity = calculate_ambiguity_score(message, conversation_history)

        # Build dynamic system prompt with user context
        # Context comes FIRST - model reads top to bottom
        try:
            system_prompt = build_orchestrator_prompt(
                user_profile=user_profile,
                langmem_memories=langmem_context,
                session_count=0,  # Would need session_count from state
                recent_quality_trend=None,  # Would need quality trend from state
            )
            logger.debug(f"[orchestrator] using dynamic prompt with {len(system_prompt)} chars")
        except Exception as e:
            logger.warning(f"[orchestrator] build_orchestrator_prompt failed, using fallback: {e}")
            system_prompt = KIRA_SYSTEM_PROMPT

        context = f"""Conversation history:
{history_context}

User profile:
{profile_context}

Current message: {message}

Analysis:
- Is followup modification: {is_followup}
- Ambiguity score: {ambiguity:.2f} (threshold: 0.7)
- Message length: {len(message)} chars

Decide routing and return JSON."""

        # ═══ CALL LLM ═══
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        # ═══ PARSE JSON RESPONSE ═══
        try:
            decision = json.loads(response.content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"[kira] JSON parse failed: {e}")
            # Fallback decision
            decision = {
                "user_facing_message": "Analyzing your request...",
                "proceed_with_swarm": True,
                "agents_to_run": ["intent"],
                "clarification_needed": False,
                "clarification_question": None,
                "skip_reasons": {},
                "tone_used": "direct",
                "profile_applied": False,
            }
        
        # ═══ VALIDATE REQUIRED FIELDS ═══
        required_fields = [
            "user_facing_message",
            "proceed_with_swarm",
            "agents_to_run",
            "clarification_needed",
        ]
        
        for field in required_fields:
            if field not in decision:
                logger.warning(f"[kira] missing field '{field}' — adding default")
                if field == "user_facing_message":
                    decision[field] = "Processing your request..."
                elif field == "proceed_with_swarm":
                    decision[field] = True
                elif field == "agents_to_run":
                    decision[field] = ["intent"]
                elif field == "clarification_needed":
                    decision[field] = False
        
        # ═══ CHECK FORBIDDEN PHRASES ═══
        user_message = decision["user_facing_message"]
        for phrase in KIRA_FORBIDDEN_PHRASES:
            if phrase.lower() in user_message.lower():
                logger.warning(f"[kira] forbidden phrase detected: '{phrase}'")
                # Replace with neutral alternative
                user_message = user_message.replace(phrase, "")
                decision["user_facing_message"] = user_message.strip()
        
        # ═══ APPLY TONE ADAPTATION ═══
        preferred_tone = user_profile.get("preferred_tone", "direct")
        if preferred_tone in ["casual", "technical", "direct"]:
            decision["tone_used"] = preferred_tone
        else:
            decision["tone_used"] = "direct"
        
        decision["profile_applied"] = bool(user_profile)
        
        # ═══ LOG DECISION ═══
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[kira] routing decision: "
            f"agents={decision['agents_to_run']}, "
            f"clarification={decision['clarification_needed']}, "
            f"tone={decision['tone_used']}, "
            f"latency={latency_ms}ms"
        )
        
        return {
            "orchestrator_decision": decision,
            "user_facing_message": decision["user_facing_message"],
            "proceed_with_swarm": decision["proceed_with_swarm"],
            "latency_ms": latency_ms,
        }
        
    except Exception as e:
        logger.error(f"[kira] orchestrator failed: {e}", exc_info=True)
        # Hard fallback — treat as CONVERSATION
        return {
            "orchestrator_decision": {
                "user_facing_message": "I'm here to help. What would you like to improve?",
                "proceed_with_swarm": False,
                "agents_to_run": [],
                "clarification_needed": False,
                "clarification_question": None,
                "skip_reasons": {"orchestrator": str(e)},
                "tone_used": "direct",
                "profile_applied": False,
            },
            "user_facing_message": "I'm here to help. What would you like to improve?",
            "proceed_with_swarm": False,
            "latency_ms": 0,
        }


__all__ = [
    "orchestrator_node",
    "KIRA_SYSTEM_PROMPT",
    "KIRA_FORBIDDEN_PHRASES",
    "KIRA_MAX_TOKENS",
    "KIRA_TEMPERATURE",
    "KIRA_MAX_QUESTIONS",
    "detect_modification_phrases",
    "calculate_ambiguity_score",
]
