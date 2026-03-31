# agents/quality_gate.py
# ─────────────────────────────────────────────
# Multi-Criteria Quality Gate for Prompt Engineer
#
# Evaluates improved prompts using multiple criteria:
# 1. Semantic similarity (not too different from original)
# 2. Information density (more signal, less noise)
# 3. Constraint coverage (from context analysis)
# 4. Specificity score (named entities, numbers, specifics)
# 5. LLM-as-Judge evaluation
#
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual
# ─────────────────────────────────────────────

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Quality evaluation report with scores and feedback."""
    overall: float  # 0.0-5.0
    scores: Dict[str, float]  # Individual metric scores
    feedback: List[str]  # Human-readable feedback
    should_retry: bool  # Whether to retry generation
    retry_reason: Optional[str]  # Why retry is needed


class PromptQualityGate:
    """
    Multi-criteria quality gate for prompt engineer output.
    
    Evaluates improved prompts on 5 dimensions:
    1. Semantic similarity (preserves original intent)
    2. Information density (more signal per word)
    3. Constraint coverage (includes required constraints)
    4. Specificity (concrete details, not vague)
    5. LLM-as-Judge (overall quality assessment)
    
    Example:
        gate = PromptQualityGate()
        report = gate.evaluate(
            original="write a story",
            improved="You are a sci-fi author. Write a 1000-word story...",
            context={"required_constraints": ["role", "tone"]}
        )
        if report.should_retry:
            # Regenerate with feedback
            pass
    """
    
    def __init__(
        self,
        min_overall_score: float = 3.5,
        min_constraint_coverage: float = 0.5,
        min_specificity: int = 2
    ):
        """
        Initialize quality gate with thresholds.
        
        Args:
            min_overall_score: Minimum acceptable overall score (default: 3.5)
            min_constraint_coverage: Minimum fraction of constraints covered (default: 0.5)
            min_specificity: Minimum specificity score (default: 2)
        """
        self.min_overall_score = min_overall_score
        self.min_constraint_coverage = min_constraint_coverage
        self.min_specificity = min_specificity
        
        # Weights for each metric
        self.weights = {
            'semantic_similarity': 0.20,
            'info_density': 0.20,
            'constraint_coverage': 0.20,
            'specificity': 0.20,
            'llm_judge': 0.20
        }
        
        logger.info(
            f"[quality_gate] initialized with min_overall={min_overall_score}, "
            f"min_constraint={min_constraint_coverage}, min_specificity={min_specificity}"
        )
    
    def _calculate_semantic_similarity(
        self,
        original: str,
        improved: str
    ) -> float:
        """
        Calculate semantic similarity between original and improved prompts.
        
        Uses embedding-based cosine similarity when available.
        Falls back to lexical overlap if embeddings unavailable.
        
        Args:
            original: Original prompt text
            improved: Improved prompt text
        
        Returns:
            Similarity score 0.0-1.0 (higher = more similar)
        """
        try:
            # Try to use embeddings from memory/langmem module
            from memory.langmem import _generate_embedding
            
            orig_emb = _generate_embedding(original)
            imp_emb = _generate_embedding(improved)
            
            if orig_emb and imp_emb:
                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(orig_emb, imp_emb))
                norm_orig = sum(a * a for a in orig_emb) ** 0.5
                norm_imp = sum(b * b for b in imp_emb) ** 0.5
                
                if norm_orig > 0 and norm_imp > 0:
                    similarity = dot_product / (norm_orig * norm_imp)
                    # Normalize from [-1, 1] to [0, 1]
                    normalized = (similarity + 1) / 2
                    return normalized
        except Exception as e:
            logger.debug(f"[quality_gate] embedding similarity failed: {e}")
        
        # Fallback: lexical overlap (Jaccard similarity)
        orig_words = set(original.lower().split())
        imp_words = set(improved.lower().split())
        
        intersection = len(orig_words & imp_words)
        union = len(orig_words | imp_words)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        # Scale to 0-5 range (Jaccard is 0-1)
        return jaccard * 5.0
    
    def _calculate_info_density(self, text: str) -> float:
        """
        Calculate information density of text.
        
        Measures:
        - Named entity count (people, places, organizations)
        - Numbers and quantities
        - Technical terms
        - Action verbs
        - Penalizes: filler words, redundancy
        
        Args:
            text: Text to analyze
        
        Returns:
            Information density score 0.0-5.0
        """
        if not text.strip():
            return 0.0
        
        # Count informative elements
        patterns = {
            'numbers': r'\b\d+(\.\d+)?\b',
            'quoted_text': r'["\'][^"\']+["\']',
            'technical_terms': r'\b[A-Z][a-z]+[A-Z][a-z]+\b',  # CamelCase
            'lists': r'\b(first|second|third|finally|step \d+)\b',
            'action_verbs': r'\b(write|create|build|design|develop|implement|analyze|evaluate)\b',
        }
        
        score = 0.0
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * 0.5
        
        # Penalize filler words
        fillers = [
            'very', 'really', 'quite', 'just', 'actually',
            'basically', 'essentially', 'literally'
        ]
        filler_count = sum(1 for filler in fillers if filler in text.lower())
        score -= filler_count * 0.3
        
        # Normalize to 0-5 range
        normalized = min(5.0, max(0.0, score))
        
        logger.debug(f"[quality_gate] info_density: {normalized:.2f} (fillers={filler_count})")
        return normalized
    
    def _check_constraint_coverage(
        self,
        improved: str,
        required_constraints: List[str]
    ) -> float:
        """
        Check how many required constraints are covered in improved prompt.
        
        Args:
            improved: Improved prompt text
            required_constraints: List of required constraint types
        
        Returns:
            Coverage fraction 0.0-1.0
        """
        if not required_constraints:
            return 1.0  # No constraints to check
        
        constraint_patterns = {
            'role': r'(you are|act as|role|expert|professional|specialist)',
            'audience': r'(audience|reader|viewer|for|target|to)',
            'tone': r'(tone|style|formal|casual|technical|friendly|professional)',
            'format': r'(format|structure|output|return|provide|as a|in a)',
            'length': r'(\b\d+\b words?|paragraphs?|pages?|brief|detailed|concise)',
            'examples': r'(example|such as|like|including|e\.g\.|i\.e\.)',
        }
        
        covered = 0
        for constraint in required_constraints:
            pattern = constraint_patterns.get(constraint.lower(), constraint)
            if re.search(pattern, improved, re.IGNORECASE):
                covered += 1
                logger.debug(f"[quality_gate] constraint '{constraint}' covered")
            else:
                logger.debug(f"[quality_gate] constraint '{constraint}' NOT covered")
        
        coverage = covered / len(required_constraints)
        logger.debug(f"[quality_gate] constraint_coverage: {coverage:.2f} ({covered}/{len(required_constraints)})")
        return coverage
    
    def _calculate_specificity(self, text: str) -> float:
        """
        Calculate specificity score based on concrete details.
        
        Counts:
        - Named entities (people, places, organizations)
        - Numbers and measurements
        - Specific dates/times
        - Technical terminology
        - Concrete examples
        
        Args:
            text: Text to analyze
        
        Returns:
            Specificity score 1.0-5.0
        """
        if not text.strip():
            return 0.0
        
        specificity_indicators = [
            # Numbers with units
            (r'\b\d+\s*(words?|pages?|steps?|examples?|minutes?|hours?)\b', 1.0),
            # Percentages
            (r'\b\d+%', 0.5),
            # Specific dates/times
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b', 0.5),
            # Named styles/formats
            (r'\b(APA|MLA|Chicago|Harvard|JSON|XML|Markdown|HTML|CSS)\b', 0.5),
            # Specific roles
            (r'\b(expert|professional|specialist|senior|lead|chief|principal)\b', 0.5),
            # Concrete examples
            (r'(for example|such as|including|e\.g\.|like|e.g.)', 0.5),
            # Measurements
            (r'\b\d+\s*(cm|kg|lbs|miles|km|MB|GB|TB)\b', 1.0),
        ]
        
        score = 1.0  # Base score
        for pattern, weight in specificity_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * weight
        
        # Cap at 5.0
        normalized = min(5.0, max(1.0, score))
        
        logger.debug(f"[quality_gate] specificity: {normalized:.2f}")
        return normalized
    
    def _llm_judge_evaluation(
        self,
        original: str,
        improved: str,
        context: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Use LLM as judge for overall quality evaluation.
        
        Args:
            original: Original prompt text
            improved: Improved prompt text
            context: Analysis context from upstream agents
        
        Returns:
            Tuple of (score 1-5, feedback string)
        """
        try:
            from config import get_fast_llm
            from langchain_core.messages import SystemMessage, HumanMessage
            
            llm = get_fast_llm()
            
            judge_prompt = f"""You are an expert prompt quality evaluator.

Rate this prompt improvement on 5 dimensions (1-5 scale each):
1. Specificity: Does it add concrete details?
2. Clarity: Is it clearer than the original?
3. Actionability: Can the AI act on this immediately?
4. Completeness: Does it include role, audience, format, constraints?
5. Improvement: Is it genuinely better than the original?

Original prompt:
{original[:500]}

Improved prompt:
{improved[:1000]}

Return ONLY this JSON format:
{{
  "specificity": 1-5,
  "clarity": 1-5,
  "actionability": 1-5,
  "completeness": 1-5,
  "improvement": 1-5,
  "overall": 1-5,
  "feedback": "Brief explanation of scores"
}}"""
            
            response = llm.invoke([
                SystemMessage(content="You are a precise JSON-only evaluator. Output valid JSON only."),
                HumanMessage(content=judge_prompt)
            ])
            
            # Parse response
            from utils import parse_json_response
            result = parse_json_response(response.content, "llm_judge", retries=1)
            
            overall = result.get('overall', 3.0)
            feedback = result.get('feedback', 'No feedback provided')
            
            logger.debug(f"[quality_gate] LLM judge: overall={overall:.1f}, feedback='{feedback[:50]}...'")
            
            return float(overall), feedback
            
        except Exception as e:
            logger.warning(f"[quality_gate] LLM judge failed: {e}")
            # Return neutral score on failure
            return 3.0, "LLM judge unavailable"
    
    def evaluate(
        self,
        original: str,
        improved: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Evaluate improved prompt quality with multi-criteria scoring.
        
        Args:
            original: User's original prompt
            improved: Engineered/improved prompt
            context: Optional context with required_constraints, domain_analysis, etc.
        
        Returns:
            QualityReport with scores and retry recommendation
        
        Example:
            report = gate.evaluate(
                original="write email",
                improved="You are a professional copywriter. Write a 200-word sales email...",
                context={"required_constraints": ["role", "length", "tone"]}
            )
            if report.should_retry:
                print(f"Retry needed: {report.retry_reason}")
        """
        context = context or {}
        required_constraints = context.get('required_constraints', [])
        
        feedback = []
        scores = {}
        
        # 1. Semantic similarity
        scores['semantic_similarity'] = self._calculate_semantic_similarity(original, improved)
        if scores['semantic_similarity'] < 2.0:
            feedback.append("⚠️ Improved prompt diverges too much from original intent")
        
        # 2. Information density
        scores['info_density'] = self._calculate_info_density(improved)
        if scores['info_density'] < 2.5:
            feedback.append("⚠️ Low information density - add more concrete details")
        
        # 3. Constraint coverage
        scores['constraint_coverage'] = self._check_constraint_coverage(improved, required_constraints)
        if scores['constraint_coverage'] < self.min_constraint_coverage:
            feedback.append(f"⚠️ Missing required constraints (covered {scores['constraint_coverage']:.0%})")
        
        # 4. Specificity
        scores['specificity'] = self._calculate_specificity(improved)
        if scores['specificity'] < self.min_specificity:
            feedback.append("⚠️ Too vague - add numbers, examples, or specific details")
        
        # 5. LLM-as-Judge
        llm_score, llm_feedback = self._llm_judge_evaluation(original, improved, context)
        scores['llm_judge'] = llm_score
        if llm_score < 3.0:
            feedback.append(f"⚠️ LLM judge: {llm_feedback}")
        
        # Calculate weighted overall score
        overall = sum(
            scores[metric] * weight
            for metric, weight in self.weights.items()
        )
        
        # Determine if retry is needed
        should_retry = (
            overall < self.min_overall_score or
            scores['constraint_coverage'] < self.min_constraint_coverage or
            scores['specificity'] < self.min_specificity
        )
        
        retry_reason = None
        if should_retry:
            reasons = []
            if overall < self.min_overall_score:
                reasons.append(f"overall score {overall:.1f} < {self.min_overall_score}")
            if scores['constraint_coverage'] < self.min_constraint_coverage:
                reasons.append(f"constraint coverage {scores['constraint_coverage']:.0%} < {self.min_constraint_coverage:.0%}")
            if scores['specificity'] < self.min_specificity:
                reasons.append(f"specificity {scores['specificity']:.1f} < {self.min_specificity}")
            retry_reason = "; ".join(reasons)
        
        logger.info(
            f"[quality_gate] evaluation: overall={overall:.2f}, "
            f"retry={should_retry}, reasons={retry_reason or 'none'}"
        )
        
        return QualityReport(
            overall=overall,
            scores=scores,
            feedback=feedback,
            should_retry=should_retry,
            retry_reason=retry_reason
        )


# Global instance for reuse
quality_gate = PromptQualityGate()


def evaluate_prompt_quality(
    original: str,
    improved: str,
    context: Optional[Dict[str, Any]] = None
) -> QualityReport:
    """
    Convenience function for prompt quality evaluation.
    
    Args:
        original: Original prompt
        improved: Improved prompt
        context: Optional context with constraints
    
    Returns:
        QualityReport with scores and feedback
    """
    return quality_gate.evaluate(original, improved, context)


__all__ = [
    "PromptQualityGate",
    "quality_gate",
    "evaluate_prompt_quality",
    "QualityReport",
]
