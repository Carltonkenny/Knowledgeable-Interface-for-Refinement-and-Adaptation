# Component 2: Supermemory Integration (25%)
**Purpose:** Build MCP-exclusive memory system for conversational context, never overlapping with LangMem.

## Requirements (from RULES.md)
- MCP-exclusive, no web app overlap
- Stores conversational facts and project context
- Temporal updates (new info supersedes old)
- Brief session summaries
- Query at conversation start

## Implementation Steps
1. Create `memory/supermemory.py` with storage interface
2. Implement fact extraction from MCP conversations
3. Add temporal update logic (supersede old facts)
4. Integrate with MCP server for context queries
5. Ensure strict separation from LangMem

## Key Classes
```python
class Supermemory:
    def __init__(self)
    async def store_fact(self, user_id: str, fact: str, context: Dict) -> bool
    async def get_context(self, user_id: str, session_id: str, limit: int = 5) -> List[Dict]
    async def _find_conflicting_fact(self, user_id: str, fact: str) -> Optional[Dict]
    async def _insert_fact(self, user_id: str, fact: str, context: Dict)
    async def _update_fact(self, fact_id: str, fact: str, context: Dict)
```

## Data Storage
**Table:** `supermemory_facts`
```
id: uuid (PK)
user_id: uuid (FK)
fact: text
context: jsonb
created_at: timestamptz
updated_at: timestamptz
```

## Temporal Updates
- New facts supersede conflicting old facts
- Similarity checking for conflict detection
- Update timestamps on modifications
- Preserve creation date for original fact

## Context Retrieval
- Query recent facts for user
- Limit to top N most relevant
- Include metadata (timestamps, context)
- Return structured for MCP injection

## Security
- RLS policies on supermemory_facts table
- User isolation (auth.uid() = user_id)
- No cross-user data access

## Testing
- Unit tests for storage/retrieval
- Temporal update verification
- Isolation from LangMem
- Performance under load</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\supermemory.md