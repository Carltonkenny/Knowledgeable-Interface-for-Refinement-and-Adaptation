# memory/__init__.py
# ─────────────────────────────────────────────
# LangMem Memory Module — Pipeline memory for web app
#
# RULES.md Compliance:
# - LangMem NEVER called on MCP requests (surface isolation)
# - Query on every web request (parallel with other context loads)
# - Write as background task (user NEVER waits)
# - User isolation via Supabase RLS (user_id = auth.uid())
#
# Exports:
#   query_langmem()              — Semantic search for relevant memories
#   write_to_langmem()           — Store session facts (background)
#   get_style_reference()        — User's best past prompts for style
#   update_user_profile()        — Background profile updates
#   should_trigger_update()      — Check if profile update needed
#   save_core_memories_if_needed() — Importance-filtered core memory extraction
# ─────────────────────────────────────────────

from memory.langmem import (
    query_langmem,
    write_to_langmem,
    get_style_reference,
)

from memory.profile_updater import (
    update_user_profile,
    should_trigger_update,
)

from memory.memory_extractor import (
    save_core_memories_if_needed,
    score_importance,
    extract_session_summary,
)

__all__ = [
    "query_langmem",
    "write_to_langmem",
    "get_style_reference",
    "update_user_profile",
    "should_trigger_update",
    "save_core_memories_if_needed",
    "score_importance",
    "extract_session_summary",
]
