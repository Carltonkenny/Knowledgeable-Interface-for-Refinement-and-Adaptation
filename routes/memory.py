# routes/memory.py
# ─────────────────────────────────────────────
# Memory Management Endpoints
#   DELETE /memory/{memory_id} → Remove a core memory
# ─────────────────────────────────────────────

import logging
from fastapi import APIRouter, HTTPException, Depends
from auth import User, get_current_user
from database import get_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Memory"])

@router.delete("/memory/{memory_id}")
async def delete_core_memory(
    memory_id: str,
    user: User = Depends(get_current_user)
):
    """
    Securely delete a core memory.
    Ensures the user_id matches the memory owner.
    """
    try:
        db = get_client()
        
        # Verify ownership and delete in one step using Supabase RLS or filter
        result = db.table("langmem_memories") \
            .delete() \
            .eq("id", memory_id) \
            .eq("user_id", user.user_id) \
            .execute()
        
        # Check if anything was actually deleted
        if not result.data:
            logger.warning(f"[memory] delete failed: memory {memory_id} not found or unauthorized for user {user.user_id}")
            raise HTTPException(status_code=404, detail="Memory not found or unauthorized.")
            
        logger.info(f"[memory] user {user.user_id[:8]}... deleted memory {memory_id}")
        return {"status": "success", "message": "Memory forgotten."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[memory] delete_core_memory error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete memory.")
