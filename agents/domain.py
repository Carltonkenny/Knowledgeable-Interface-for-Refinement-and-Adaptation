# agents/domain.py
# ─────────────────────────────────────────────
# Domain Agent — Third agent in the swarm
#
# Classifies WHAT field/domain the prompt belongs to.
# Identifies the specific craft, discipline, and prompt engineering patterns that apply.
#
# Input:  state['raw_prompt'] (user's original prompt)
# Output: state['domain_analysis'] with fields:
#   - primary_domain    → Precise field name
#   - sub_domain        → Specific discipline within that field
#   - relevant_patterns → Prompt engineering patterns to apply
#   - complexity        → "simple" | "moderate" | "complex"
#
# Skip Condition: User profile has domain at >85% confidence
# Uses fast LLM (nova-fast, 400 tokens, temp 0.1)
# ─────────────────────────────────────────────

import time
import logging
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_fast_llm
from state import AgentState
from utils import parse_json_response

logger = logging.getLogger(__name__)

# ── OpenTelemetry Tracing ────────────────────
try:
    from middleware.otel_tracing import get_tracer
except ImportError:
    def get_tracer(name="promptforge"):
        class _NoopSpan:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def set_attribute(self, k, v): pass
        class _NoopTracer:
            def start_as_current_span(self, name): return _NoopSpan()
        return _NoopTracer()

# ═══ DISCIPLINE PERSONA MAPPING ═══════════════
# This map transforms Kira's voice based on the detected domain.
DISCIPLINE_PERSONA_MAP = {
    "technical architecture": "Precision-Guided, High-Resolution, Low-Fluff. Focus on scalability, security, and clear system boundaries. Use structured bullet points.",
    "full-stack development": "Pragmatic and execution-focused. Prioritize elegant code architecture and modern best practices.",
    "data intelligence": "Analytical, statistical, and hyper-logical. Focus on data integrity, edge-case math, and clear query structures.",
    "creative synthesis": "Exploratory, metaphoric, and narrative-driven. Encourage out-of-the-box conceptualization and fluid structures.",
    "strategic business": "ROI-focused, concise, and executive. Speak in frameworks, KPIs, and actionable outcomes.",
    "instructional design": "Clear, step-by-step, and empathetic. Focus on readability and preventing cognitive overload for the reader.",
    "persona engineering": "Psychological and behavioral. Focus on underlying motivations, tone of voice, and character consistency.",
    "security & research": "Paranoid, loophole-focused, and rigorous. Prioritize threat modeling, strict constraints, and edge-case testing.",
    "legal & compliance": "Meticulous, risk-averse, and highly structured. Focus on exact definitions, edge cases, and strict liability constraints.",
    "project management": "Organized, timeline-focused, and dependency-aware. Priority on unblocking resources and clear milestones.",
    "scientific computing": "Rigorous, peer-review oriented, and objective. Focus on methodological soundness and variables.",
    "meta-prompting": "Recursive, abstract, and highly analytical. Optimize for LLM attention decay, chain-of-thought, and few-shot efficiency."
}

# ═══ SYSTEM PROMPT ════════════════════════════

SYSTEM_PROMPT = """You are a High-Fidelity Domain Architect. Your task is to classify engineering requests into a professional Discipline Taxonomy.

CHOOSE THE BEST FIT FROM THIS TAXONOMY:
1.  Technical Architecture (Distributed systems, API Design, Cloud Infra)
2.  Full-Stack Development (React, Next.js, Backend, Frameworks)
3.  Data Intelligence (DS/ML, SQL, Data Engineering, Analytics)
4.  Creative Synthesis (Copywriting, Brand Storytelling, Prose)
5.  Strategic Business (Product GTM, SaaS Strategy, KPI Frameworks)
6.  Instructional Design (SOPs, Tutorials, Technical Documentation)
7.  Persona Engineering (Behavior simulation, Role-assignment)
8.  Security & Research (Vulnerability analysis, Pentesting, Audit)
9.  Legal & Compliance (GDPR, SOX, Contract logic)
10. Project Management (Agile, Resource Allocation, Timelines)
11. Scientific Computing (Bio-tech, Physics, Mathematical modeling)
12. Meta-Prompting (System prompts, prompt chain optimization)

Always respond with ONLY this JSON:
{
  "primary_domain": "One of the 12 categories above",
  "sub_domain": "A specific discipline (e.g. 'PostgreSQL Optimizer')",
  "relevant_patterns": ["Patterns like role_assignment, chain_of_thought, etc."],
  "complexity": "simple or moderate or complex",
  "confidence": 0.0-1.0
}
"""


# ═══ DOMAIN AGENT NODE ═══════════════════════

def domain_agent(state: AgentState) -> Dict[str, Any]:
    """
    Identifies user's domain expertise and relevant patterns.
    
    Skip Condition: User profile has domain confidence > 85%
    
    Args:
        state: Current AgentState with raw_prompt and user_profile
        
    Returns:
        Dict with domain_analysis, was_skipped, skip_reason, latency_ms
    """
    start_time = time.time()
    
    # ═══ CHECK SKIP CONDITION ═══
    user_profile = state.get("user_profile", {})
    domain_confidence = user_profile.get("domain_confidence", 0.0)
    
    if domain_confidence > 0.85:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[domain] skipped — high confidence ({domain_confidence:.2f})")
        return {
            "domain_analysis": None,  # None for skipped/failed, merge_dict will ignore
            "was_skipped": True,
            "skip_reason": f"domain confidence {domain_confidence:.2f} > 0.85",
            "latency_ms": latency_ms,
        }
    
    # ═══ RUN DOMAIN ANALYSIS ═══
    try:
        tracer = get_tracer("promptforge.agent")
        with tracer.start_as_current_span("agent.domain") as span:
            span.set_attribute("agent.skip_checked", True)

            llm = get_fast_llm()

            # Support both 'raw_prompt' and 'message' field names
            prompt = state.get('raw_prompt', state.get('message', ''))

            # Extract dominant domains from profile for context
            dominant_domains = user_profile.get("dominant_domains", [])
            domains_context = f"User's past domains: {', '.join(dominant_domains)}" if dominant_domains else "No domain history available"

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"{domains_context}\n\nIdentify the domain of: {prompt}")
            ]

            response = llm.invoke(
                messages,
                config={
                    "tags": ["domain_agent", "swarm"],
                    "metadata": {"agent": "domain"},
                },
            )
            result = parse_json_response(response.content, agent_name="domain")

            latency_ms = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency_ms

            # Inject the Persona Overlay based on primary_domain
            primary_domain = result.get('primary_domain', 'general').lower()
            persona_overlay = DISCIPLINE_PERSONA_MAP.get(primary_domain, "")
            result["persona_overlay"] = persona_overlay

            logger.info(f"[domain] domain={primary_domain} confidence={result.get('confidence', 0):.2f} latency={latency_ms}ms")

            return {
                "domain_analysis": result,
                "was_skipped": False,
                "skip_reason": None,
                "latency_ms": latency_ms,
                "agents_run": ["domain"],
                "agent_latencies": {"domain": latency_ms}
            }

    except Exception as e:
        logger.error(f"[domain] failed: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "domain_analysis": None,  # None signals failure, merge_dict will ignore
            "was_skipped": False,
            "skip_reason": None,
            "latency_ms": latency_ms,
        }


# ═══ VALIDATION FUNCTION ═════════════════════

def validate_domain_output(result: Dict[str, Any]) -> bool:
    """
    Validate domain agent output meets quality gates.
    
    Quality Gates:
    1. primary_domain is non-empty and not generic
    2. At least 1 relevant pattern identified
    3. Confidence >= 0.6
    
    Args:
        result: Domain agent output dict
        
    Returns:
        True if passes quality gates, False otherwise
    """
    generic_domains = ["general", "unknown", "other", "generic", "chat", "misc"]
    
    # Gate 1: Domain is specific
    primary_domain = result.get("primary_domain", "").lower()
    is_specific = primary_domain and primary_domain not in generic_domains
    
    # Gate 2: Has patterns
    patterns = result.get("relevant_patterns", [])
    has_patterns = len(patterns) >= 1
    
    # Gate 3: Reasonable confidence
    confidence = result.get("confidence", 0.0)
    reasonable_confidence = confidence >= 0.6
    
    passes = sum([is_specific, has_patterns, reasonable_confidence]) >= 2
    
    if not passes:
        logger.warning(f"[domain] quality gate failed — specific={is_specific}, patterns={has_patterns}, confidence={confidence:.2f}")
    
    return passes
