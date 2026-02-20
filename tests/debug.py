# debug.py — multi-industry test
from graph.workflow import workflow
from state import AgentState
from langchain_core.messages import HumanMessage

prompts = {
    "healthcare": "Design a clinical decision support system for emergency triage that analyzes patient symptoms, vital signs, and medical history to prioritize care. Include HIPAA compliance, bias mitigation, and a pilot plan for a 500-bed hospital.",
    "finance": "Create a quantitative trading strategy for crypto markets combining sentiment analysis, on-chain metrics, and technical indicators. Include risk management, backtesting framework, and Sharpe ratio metrics.",
    "legal": "Build an AI contract analysis system for M&A due diligence. Extract key terms, flag risky clauses, handle scanned PDFs, and integrate with CLM platforms. Include audit trails for court admissibility.",
    "manufacturing": "Develop an IoT predictive maintenance system for aerospace CNC machines. Predict tool failures 48 hours ahead, include edge computing under 10ms latency, digital twin integration, and ISO 9001 compliance.",
    "education": "Design an adaptive K-12 math learning platform with real-time cognitive load assessment, gamification, multilingual support including sign language, FERPA compliance, and spaced repetition algorithms."
}

for industry, prompt in prompts.items():
    print(f"\n{'='*60}")
    print(f"TESTING: {industry.upper()}")
    print(f"{'='*60}")

    state = AgentState(
        raw_prompt=prompt,
        intent_result={},
        context_result={},
        domain_result={},
        improved_prompt="",
        final_response={},
        conversation_history=[],
        messages=[HumanMessage(content=prompt)]
    )

    try:
        result = workflow.invoke(state)
        print(f"✅ Intent clarity : {result.get('intent_result', {}).get('goal_clarity', 'N/A')}")
        print(f"✅ Skill level    : {result.get('context_result', {}).get('skill_level', 'N/A')}")
        print(f"✅ Domain         : {result.get('domain_result', {}).get('primary_domain', 'N/A')}")
        print(f"✅ Improved prompt: {result.get('improved_prompt', 'EMPTY')}")
    except Exception as e:
        print(f"❌ FAILED: {e}")