# agents/autonomous.py
# ─────────────────────────────────────────────
# The conversational brain — handles all non-swarm interactions.
#
# Three responsibilities:
#   classify_message()    → Classifies input as CONVERSATION | NEW_PROMPT | FOLLOWUP
#                           Uses 1 LLM call with conversation history context.
#                           Falls back to CONVERSATION on any error.
#   handle_conversation() → Generates personality-driven chat replies.
#                           Uses 1 LLM call with PromptForge persona.
#                           Returns hardcoded fallback if LLM fails — never exposes errors.
#   handle_followup()     → Refines existing prompt based on user feedback.
#                           Uses 1 LLM call, skips full swarm (saves 3 LLM calls).
#                           Returns None if no previous prompt found → api.py treats as NEW_PROMPT.
#
# Guardrails:
#   - Messages < 10 chars → always CONVERSATION (prevents misclassification of "hi", "ok", etc.)
#   - Invalid classification → falls back to CONVERSATION
#   - Empty followup result → returns None, triggers full swarm as fallback
#
# Imports format_history() from utils.py to avoid duplication with conversation handlers.
# ─────────────────────────────────────────────
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_fast_llm
from utils import parse_json_response, format_history

logger = logging.getLogger(__name__)

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

    llm = get_fast_llm()

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