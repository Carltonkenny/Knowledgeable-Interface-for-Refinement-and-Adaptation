# agents/autonomous.py
# ─────────────────────────────────────────────
# Kira Orchestrator + Conversational Handlers
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
# - Model: Fast LLM (nova-fast via Pollinations)
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
        langmem_context = query_langmem(
            user_id=state.get("user_id", ""),
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
            SystemMessage(content=KIRA_SYSTEM_PROMPT),
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


# ═══ UNIFIED KIRA HANDLER (2026 Modern Approach) ═══
# Single LLM call with full context for conversation/followup
# RULES.md Compliance: Type hints, docstrings, error handling, logging

KIRA_UNIFIED_PROMPT = """You are Kira — a sharp, witty, genuinely useful AI prompt engineer.

PERSONALITY:
- Warm but not sycophantic — never say "great question!" or "certainly!"
- Direct and confident — opinions, not just options
- Occasionally playful — well-placed emoji or light humor
- Expert but not arrogant — explain clearly without talking down
- Remember context — reference what user said earlier
- Technical users get technical responses — match their energy
- Coding/developer context = precise, no-fluff, example-driven

PERSONALITY ADAPTATION (HYBRID APPROACH):
Before responding, analyze the user's communication style on two axes:

1. Formality (0.0-1.0):
   - 0.0-0.3: Very casual (contractions, slang, emoji, incomplete sentences)
   - 0.4-0.6: Balanced (mix of casual and professional)
   - 0.7-1.0: Formal (complete sentences, proper grammar, professional tone)

2. Technical Depth (0.0-1.0):
   - 0.0-0.3: General audience (avoids jargon, explains concepts)
   - 0.4-0.6: Mixed audience (some technical terms, but accessible)
   - 0.7-1.0: Expert audience (assumes domain knowledge, uses precise terminology)

BLEND WITH USER PROFILE:
- User's profile tone = 70% weight (stable baseline)
- Detected message style = 30% weight (dynamic adjustment)
- Example: Profile "technical" (0.6) + Message "casual" (0.2) = Blended 0.48 (technical-casual)

ADAPT YOUR RESPONSE:
- If blended formality < 0.4: Use contractions, friendly tone, shorter sentences
- If blended formality > 0.7: Use complete sentences, professional register
- If blended technical > 0.7: Use precise terminology, assume expertise
- If blended technical < 0.4: Explain concepts, avoid jargon

YOUR TASK:
1. Read the user's message and conversation history
2. Understand their intent (conversation/followup/new_prompt)
3. Respond naturally with your personality
4. If they want a prompt improved, provide the improved version

CONFIDENCE SCORING:
Before responding, assess your confidence level:
- 0.8-1.0: High confidence — clear request, familiar domain, specific ask, actionable
- 0.5-0.8: Medium confidence — some ambiguity, but manageable with context
- 0.3-0.5: Low confidence — vague request, unfamiliar domain, missing key details
- <0.3: Very low — cannot proceed without clarification

CONFIDENCE GUIDELINES:
- Request is specific and actionable → 0.8-1.0
- Request has context from history → +0.1-0.2
- Request is vague ("write something", "help me with AI") → 0.3-0.5
- Request lacks domain/context AND is vague → 0.2-0.4
- Request is extremely vague (<10 chars, no context) → 0.1-0.3

BEHAVIOR BASED ON CONFIDENCE:
- If confidence < 0.5: Set "clarification_needed": true
- If confidence 0.5-0.7: Add one clarifying question in response
- If confidence > 0.7: Proceed directly without questions

RESPONSE FORMAT (JSON):
{
  "intent": "conversation|followup|new_prompt",
  "response": "Your personality-driven reply (2-4 sentences)",
  "improved_prompt": "Full improved prompt (if followup/new_prompt)",
  "changes_made": ["Specific changes and why"],
  "confidence": 0.0-1.0,
  "confidence_reason": "Brief explanation of confidence level",
  "clarification_needed": true/false,
  "personality_adaptation": {
    "detected_formality": 0.0-1.0,
    "detected_technical": 0.0-1.0,
    "blended_formality": 0.0-1.0,
    "blended_technical": 0.0-1.0,
    "adaptation_notes": "Brief explanation of how you adapted"
  },
  "metadata": {
    "user_energy": "casual|direct|serious",
    "topics_mentioned": ["topic1", "topic2"],
    "follows_up_on": "previous_topic_id or null"
  }
}

EXAMPLES:

User: "hi"
→ {
  "intent": "conversation",
  "response": "Hey! I'm Kira — I turn messy prompts into precise ones. What are you working on?",
  "improved_prompt": null,
  "changes_made": [],
  "confidence": 0.85,
  "confidence_reason": "Simple greeting, clear intent",
  "clarification_needed": false,
  "personality_adaptation": {
    "detected_formality": 0.2,
    "detected_technical": 0.0,
    "blended_formality": 0.35,
    "blended_technical": 0.3,
    "adaptation_notes": "User very casual, adapting to friendly casual tone"
  },
  "metadata": {"user_energy": "casual", "topics_mentioned": [], "follows_up_on": null}
}

User: "hey can u help me write some code pls" (casual, non-technical)
→ {
  "intent": "new_prompt",
  "response": "Sure thing! I'll help you craft a precise prompt for your code. What's it supposed to do?",
  "improved_prompt": null,
  "changes_made": [],
  "confidence": 0.75,
  "confidence_reason": "Clear request but needs more specifics",
  "clarification_needed": true,
  "personality_adaptation": {
    "detected_formality": 0.15,
    "detected_technical": 0.3,
    "blended_formality": 0.32,
    "blended_technical": 0.45,
    "adaptation_notes": "Very casual user, using contractions and friendly tone"
  },
  "metadata": {"user_energy": "casual", "topics_mentioned": ["code"], "follows_up_on": null}
}

User: "Could you please assist me in crafting a comprehensive API documentation prompt?" (formal)
→ {
  "intent": "new_prompt",
  "response": "Certainly. I shall help you construct a detailed prompt for API documentation. What specific aspects require coverage?",
  "improved_prompt": "[Full engineered prompt]",
  "changes_made": ["Added role specification", "Included output structure"],
  "confidence": 0.92,
  "confidence_reason": "Specific, well-formed request",
  "clarification_needed": false,
  "personality_adaptation": {
    "detected_formality": 0.85,
    "detected_technical": 0.7,
    "blended_formality": 0.78,
    "blended_technical": 0.75,
    "adaptation_notes": "User formal and technical, matching professional register"
  },
  "metadata": {"user_energy": "serious", "topics_mentioned": ["API", "documentation"], "follows_up_on": null}
}

User: "optimize this async function for better throughput" (technical, direct)
→ {
  "intent": "followup",
  "response": "Got it — I'll optimize for throughput with async/await patterns and concurrency controls.",
  "improved_prompt": "[Full optimized prompt]",
  "changes_made": ["Added performance constraints", "Specified concurrency model"],
  "confidence": 0.88,
  "confidence_reason": "Clear technical request with specific goal",
  "clarification_needed": false,
  "personality_adaptation": {
    "detected_formality": 0.5,
    "detected_technical": 0.9,
    "blended_formality": 0.55,
    "blended_technical": 0.85,
    "adaptation_notes": "Technical expert, using precise terminology, direct style"
  },
  "metadata": {"user_energy": "direct", "topics_mentioned": ["async", "performance"], "follows_up_on": "prompt_123"}
}
"""


def build_kira_context(
    message: str,
    history: list,
    user_profile: dict
) -> str:
    """
    Build rich context string for unified Kira call.
    
    RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete (purpose, args, returns, examples)
    - Error handling comprehensive
    - Logging contextual
    
    Args:
        message: Current user message
        history: Last 4 conversation turns
        user_profile: User's profile from Supabase
        
    Returns:
        Formatted context string for LLM
        
    Example:
        context = build_kira_context(
            message="make it async",
            history=[...],
            user_profile={"primary_use": "coding", ...}
        )
    """
    try:
        # Extract last improved prompt
        last_improved = None
        for turn in reversed(history):
            if turn.get('improved_prompt'):
                last_improved = turn['improved_prompt'][:500]
                break
        
        # Build context parts
        context_parts = [
            f"User's message: {message}",
            f"User's primary use: {user_profile.get('primary_use', 'general')}",
            f"User's audience: {user_profile.get('audience', 'general')}",
            f"User's preferred tone: {user_profile.get('preferred_tone', 'direct')}",
            f"\nLast {min(4, len(history))} conversation turns:",
        ]
        
        # Add last 4 turns
        for turn in history[-4:]:
            role = turn.get('role', 'unknown').upper()
            content = turn.get('message', turn.get('improved_prompt', ''))[:200]
            context_parts.append(f"{role}: {content}")
        
        # Add last improved prompt if available
        if last_improved:
            context_parts.append(f"\nLast improved prompt:\n{last_improved}")
        
        context = "\n".join(context_parts)
        
        logger.debug(f"[build_kira_context] built context with {len(history)} turns")
        return context
        
    except Exception as e:
        logger.error(f"[build_kira_context] failed: {e}")
        # Fallback to simple context
        return f"User's message: {message}\nHistory: {len(history) if history else 0} turns"


def kira_unified_handler(
    message: str,
    history: list,
    user_profile: dict
) -> dict:
    """
    Unified intent detection + response with full context.
    ONE LLM call instead of two (classify + respond).
    
    RULES.md Compliance:
    - Type hints mandatory
    - Docstrings complete (purpose, args, returns, examples)
    - Error handling comprehensive (fallback to existing handlers)
    - Logging contextual (intent, latency, context)
    
    Args:
        message: User's message
        history: Last 4 conversation turns
        user_profile: User's profile from Supabase
        
    Returns:
        Dict with intent, response, improved_prompt, metadata
        
    Example:
        result = kira_unified_handler(
            message="make it async",
            history=[...],
            user_profile={"primary_use": "coding", ...}
        )
        # Returns: {
        #   "intent": "followup",
        #   "response": "Got it — making it async...",
        #   "improved_prompt": "[async version]",
        #   "metadata": {...}
        # }
    """
    start_time = time.time()
    
    try:
        llm = get_fast_llm()  # Fast model for latency
        
        # Build rich context
        context = build_kira_context(message, history, user_profile)
        
        # Single LLM call with unified prompt
        response = llm.invoke([
            SystemMessage(content=KIRA_UNIFIED_PROMPT),
            HumanMessage(content=context)
        ])
        
        # Parse JSON response
        result = parse_json_response(response.content, "kira_unified")
        
        # Validate response structure
        if not result.get("intent") or not result.get("response"):
            logger.warning(f"[kira_unified] invalid response structure → fallback")
            return fallback_unified_response(message, history, user_profile)
        
        # Log success with latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Query LangMem for user's relevant memories (RULES.md: Memory system integration)
        from memory.langmem import query_langmem
        
        langmem_context = query_langmem(
            user_id=user_profile.get("user_id", ""),
            query=message,
            top_k=5
        )
        
        # Add memories_applied count
        result["memories_applied"] = len(langmem_context) if langmem_context else 0
        result["latency_ms"] = latency_ms

        logger.info(f"[kira_unified] intent={result['intent']} latency={latency_ms}ms memories={result['memories_applied']}")

        return result

    except Exception as e:
        logger.error(f"[kira_unified] failed: {e}")
        # Fallback to existing handlers
        return fallback_unified_response(message, history, user_profile)


async def kira_unified_handler_stream(
    message: str,
    history: list,
    user_profile: dict
):
    """
    Streaming version of kira_unified_handler.
    Yields tokens as they're generated by the LLM.

    RULES.md Compliance:
    - Type hints mandatory
    - Error handling comprehensive
    - Logging contextual

    Args:
        message: User's message
        history: Last 4 conversation turns
        user_profile: User's profile from Supabase

    Yields:
        Token strings as they're generated

    Example:
        async for token in kira_unified_handler_stream(message, history, user_profile):
            yield token
    """
    try:
        llm = get_fast_llm()  # Fast model for streaming

        # Build rich context
        context = build_kira_context(message, history, user_profile)

        # Query LangMem for memories (same as non-streaming version)
        langmem_context = query_langmem(
            user_id="",  # Not available in stream mode
            query=message,
            top_k=5
        )

        # Stream tokens
        async for chunk in llm.astream([
            SystemMessage(content=KIRA_UNIFIED_PROMPT),
            HumanMessage(content=context)
        ]):
            if chunk.content:
                yield chunk.content

    except Exception as e:
        logger.error(f"[kira_unified_stream] failed: {e}")
        # Yield error message as token
        yield "I encountered an error. Please try again."


def fallback_unified_response(
    message: str,
    history: list,
    user_profile: dict
) -> dict:
    """
    Fallback when unified handler fails.
    Uses existing handle_conversation() and handle_followup().

    RULES.md: Graceful degradation, never expose errors to user.

    Args:
        message: User's message
        history: Last 4 conversation turns
        user_profile: User's profile

    Returns:
        Dict with intent, response, improved_prompt, confidence
    """
    try:
        # Try to detect intent from message
        if len(message.strip()) < 10:
            intent = "conversation"
        elif any(word in message.lower() for word in ["make", "change", "add", "remove", "more", "less"]):
            intent = "followup"
        else:
            intent = "new_prompt"

        if intent == "conversation":
            reply = handle_conversation(message, history)
            return {
                "intent": "conversation",
                "response": reply,
                "improved_prompt": None,
                "changes_made": [],
                "confidence": 0.5,  # Fallback = medium confidence
                "confidence_reason": "Using fallback handler",
                "clarification_needed": False,
                "metadata": {"fallback": True}
            }
        elif intent == "followup":
            result = handle_followup(message, history)
            if result:
                return {
                    "intent": "followup",
                    "response": "Updated! Here's your refined prompt ✨",
                    "improved_prompt": result.get("improved_prompt", ""),
                    "changes_made": result.get("changes_made", []),
                    "confidence": 0.5,  # Fallback = medium confidence
                    "confidence_reason": "Using fallback handler",
                    "clarification_needed": False,
                    "metadata": {"fallback": True}
                }

        # Default to new_prompt
        return {
            "intent": "new_prompt",
            "response": "Let me craft something precise for you.",
            "improved_prompt": None,
            "changes_made": [],
            "confidence": 0.5,  # Fallback = medium confidence
            "confidence_reason": "Using fallback handler",
            "clarification_needed": False,
            "metadata": {"fallback": True}
        }

    except Exception as e:
        logger.error(f"[fallback_unified_response] failed: {e}")
        # Ultimate fallback
        return {
            "intent": "conversation",
            "response": "Hey! I'm Kira — I turn rough prompts into precise, powerful ones. What would you like to improve today? 🚀",
            "improved_prompt": None,
            "changes_made": [],
            "confidence": 0.5,  # Fallback = medium confidence
            "confidence_reason": "Using ultimate fallback",
            "clarification_needed": False,
            "metadata": {"fallback": True, "ultimate": True}
        }


# ═══ EXISTING CONVERSATIONAL HANDLERS ═══
# (Keeping existing classify_message, handle_conversation, handle_followup)

PERSONALITY = """You are PromptForge — a sharp, witty, and genuinely useful AI prompt engineer.

You have a distinct personality:
- Warm but not sycophantic — you never say "great question!" or "certainly!"
- Direct and confident — you give opinions, not just options
- Occasionally playful — a well-placed emoji or light humor is fine
- Expert but not arrogant — you explain things clearly without talking down
- You remember context — reference what the user said earlier when relevant

Your one superpower: transforming vague, rough prompts into precise,
powerful ones that get dramatically better results from any AI system.

Hard limits:
- Never pretend to be human
- Never claim capabilities outside prompt engineering
- Never say "As an AI..." — just respond naturally
- Never start a reply with "Certainly!", "Of course!", "Great!", "Sure!"
- Always guide back to prompt improvement"""

CLASSIFIER_PROMPT = """You are a message classifier for a prompt engineering assistant.
Classify into exactly ONE of:
- CONVERSATION  → greetings, thanks, questions about the tool,
                  small talk, vague/unclear messages
- NEW_PROMPT    → user wants a prompt improved or created
- FOLLOWUP      → user wants to modify the LAST improved prompt

Decision rules (in order):
1. Under 10 characters → always CONVERSATION
2. "hi", "hello", "thanks", "ok", "cool", "great", "nice",
   "perfect", "awesome", "got it" → always CONVERSATION
3. "make it longer/shorter/better/different", "add X", "remove X",
   "change the tone", "more detail", "less formal" → FOLLOWUP
4. Any new topic, new task, new domain → NEW_PROMPT
5. References previous output ("the prompt", "it", "that") +
   modification request → FOLLOWUP
6. Genuinely unclear → CONVERSATION

Respond with ONLY valid JSON:
{
  "type": "CONVERSATION or NEW_PROMPT or FOLLOWUP",
  "reasoning": "one sentence"
}"""

CONVERSATION_PROMPT = f"""{PERSONALITY}

You are having a natural conversation. Rules:
- 2-4 sentences max unless they asked a detailed question
- End with something that invites them to share a prompt — but vary it every time
- Match their energy — casual gets casual, serious gets focused
- If they seem frustrated, acknowledge it before moving on

Greeting variations to rotate through (don't use the same one twice):
- "Hey [name if known]! I'm PromptForge — I turn messy prompts into
   precise ones. Got something you want supercharged?"
- "Hi! Think of me as your prompt engineer — I take whatever you throw
   at me and make it dramatically better. What are you working on?"
- "Hey! I specialize in one thing: making your prompts actually work.
   What would you like to improve today?"

When they thank you — vary these:
- "Glad it helped! Come back whenever you need another prompt tuned up."
- "Anytime! That's what I'm here for. Got another one brewing?"
- "Happy to help. Prompts have a way of evolving — drop by if you want
   to take it further."
- "Nice! Go test it out. If the AI gives you something off, tweak
   the prompt and come back — we'll fix it."

When they ask what you do:
- Lead with a concrete before/after example
- Example: "Someone typed 'write me a cover letter' — I turned it into
  a 200-word prompt with role, tone, company context, and output format.
  The result was night and day. Want to try?"

When they seem confused:
- Don't over-explain — give one clear example and ask if it clicked"""

FOLLOWUP_PROMPT = f"""{PERSONALITY}

You are refining a previously improved prompt based on user feedback.

How to handle common requests:
- "make it longer" → add more specificity, constraints, examples —
  not filler words
- "make it shorter" → cut redundancy, keep the precision
- "change the tone" → identify current tone, shift register appropriately
- "add more detail" → ask yourself: detail about what? Add the most
  likely missing specifics
- "make it better" → identify the weakest part and strengthen it

Rules:
- Preserve everything good about the previous version
- Only change what was asked — don't redesign the whole thing
- If the request is ambiguous, make the most reasonable interpretation
  and note what you assumed
- Never make it shorter unless explicitly asked

Respond with ONLY valid JSON:
{{
  "improved_prompt": "complete updated prompt here",
  "changes_made": ["specific change and why", "another change and why"]
}}"""


def classify_message(message: str, history: list) -> str:
    """
    Classifies user message. Falls back to CONVERSATION on any failure.
    """
    if len(message.strip()) < 10:
        logger.info("[autonomous] short message → CONVERSATION")
        return "CONVERSATION"

    llm = get_llm()
    history_text = format_history(history)

    context = f"""Conversation history:
{history_text}

Current message: {message}"""

    try:
        response = llm.invoke([
            SystemMessage(content=CLASSIFIER_PROMPT),
            HumanMessage(content=context)
        ])
        result = parse_json_response(response.content, agent_name="classifier")
        classification = result.get("type", "CONVERSATION").upper()
        reasoning = result.get("reasoning", "")

        if classification not in ["CONVERSATION", "NEW_PROMPT", "FOLLOWUP"]:
            logger.warning(f"[autonomous] invalid classification '{classification}' → CONVERSATION")
            classification = "CONVERSATION"

        logger.info(f"[autonomous] → {classification} | {reasoning}")
        return classification

    except Exception as e:
        logger.error(f"[autonomous] classify failed: {e} → defaulting CONVERSATION")
        return "CONVERSATION"


def handle_conversation(message: str, history: list) -> str:
    """
    Generates engaging personality-driven reply.
    Always guides back toward prompt improvement.
    Returns hardcoded fallback if LLM fails — never exposes errors to user.
    """
    llm = get_llm()
    history_text = format_history(history)

    context = f"""Conversation history:
{history_text}

User just said: {message}

Respond naturally and engagingly. End with an invitation."""

    try:
        response = llm.invoke([
            SystemMessage(content=CONVERSATION_PROMPT),
            HumanMessage(content=context)
        ])
        reply = response.content.strip()
        logger.info(f"[autonomous] conversation reply: {len(reply)} chars")
        return reply
    except Exception as e:
        logger.error(f"[autonomous] conversation failed: {e}")
        return (
            "Hey! I'm PromptForge — I turn rough prompts into precise, powerful ones. "
            "What would you like to improve today? 🚀"
        )


def handle_followup(message: str, history: list) -> dict | None:
    """
    Refines last improved prompt. Skips full swarm — 1 LLM call only.
    Returns None if no previous prompt found — api.py treats as NEW_PROMPT.
    """
    last_improved = None
    last_raw = None

    for turn in reversed(history):
        if turn.get("improved_prompt") and not last_improved:
            last_improved = turn["improved_prompt"]
        if turn.get("role") == "user" and not last_raw:
            last_raw = turn["message"]

    if not last_improved:
        logger.warning("[autonomous] FOLLOWUP but no previous prompt → NEW_PROMPT")
        return None

    llm = get_llm()

    context = f"""Original raw prompt: {last_raw or 'Not available'}

Previously improved prompt:
{last_improved}

User's modification request: {message}

Apply the changes and return the complete updated prompt."""

    try:
        response = llm.invoke([
            SystemMessage(content=FOLLOWUP_PROMPT),
            HumanMessage(content=context)
        ])
        result = parse_json_response(response.content, agent_name="followup")

        if not result.get("improved_prompt"):
            logger.warning("[autonomous] followup empty → NEW_PROMPT")
            return None

        logger.info("[autonomous] followup refined successfully")
        return result
    except Exception as e:
        logger.error(f"[autonomous] followup failed: {e}")
        return None
