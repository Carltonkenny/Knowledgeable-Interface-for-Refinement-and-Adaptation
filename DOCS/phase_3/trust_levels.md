# Component 4: Trust Level Logic (25%)
**Purpose:** Implement progressive personalization scaling from cold (0) to tuned (2) based on session count.

## Requirements (from RULES.md)
- Level 0 (0-10 sessions): Basic functionality
- Level 1 (10-30 sessions): Domain skip + tone adaptation
- Level 2 (30+ sessions): Full profile + history references
- Natural scaling (no hard gates)
- Kira adapts messaging per level

## Implementation Steps
1. Add trust_level calculation to user_profiles
2. Modify Kira orchestrator for level-aware responses
3. Implement level-specific agent skipping
4. Add level indicators in responses
5. Test scaling across session ranges

## Trust Level Definitions

### Level 0: Cold (0-10 sessions)
**Characteristics:**
- MCP works but no personalization
- Kira message: "Use me via the app more — I'll get sharper."
- All agents run (no skipping)
- Generic tone

**Implementation:**
- Default level for new users
- Full swarm execution
- Basic Kira responses
- No profile references

### Level 1: Warm (10-30 sessions)
**Characteristics:**
- Domain skip active (>85% confidence)
- Tone adaptation active
- Targeted clarification questions
- Partial personalization

**Implementation:**
- Check profile confidence for domain skipping
- Adapt Kira's tone based on user preferences
- Include basic profile references
- Reduced agent execution

### Level 2: Tuned (30+ sessions)
**Characteristics:**
- Full profile active
- Pattern references in Kira's messages
- History-aware rewrites
- Feels like a senior collaborator

**Implementation:**
- Full profile utilization
- Contextual Kira responses
- Advanced agent skipping
- Personalized interactions

## Database Changes
**Add to user_profiles table:**
```
mcp_trust_level: int — 0 | 1 | 2 (calculated field)
```

**Calculation Logic:**
```python
def calculate_trust_level(total_sessions: int) -> int:
    if total_sessions >= 30:
        return 2
    elif total_sessions >= 10:
        return 1
    else:
        return 0
```

## Kira Adaptations
**Level-specific messages:**
- Level 0: Generic, encouraging more usage
- Level 1: Reference known domains, adapt tone
- Level 2: Personal references, pattern recognition

**Tone variations:**
- Casual users: "Hey, let's tweak this..."
- Formal users: "I recommend the following improvements..."
- Technical users: "Based on your domain expertise..."

## Agent Skipping Logic
**Level 1+:** Skip context agent if profile has recent history
**Level 2:** Skip domain agent if confidence >85%
**Always run:** Intent and Prompt Engineer

## Response Indicators
**Include in MCP responses:**
```json
{
  "trust_level": 1,
  "personalization_active": true,
  "agents_skipped": ["context"],
  "profile_insights_used": ["domain_expertise"]
}
```

## Testing
- Session count thresholds
- Level transition accuracy
- Agent skipping behavior
- Kira message variations
- Profile utilization</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\trust_levels.md