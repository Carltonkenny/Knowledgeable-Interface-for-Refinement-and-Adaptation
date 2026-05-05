import logging
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import User, get_current_user
from database import get_client
from config import get_fast_llm

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Memory"])

class DistillRequest(BaseModel):
    input: str
    user_id: str

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

@router.post("/semantic-distill")
async def semantic_distill(
    req: DistillRequest,
    user: User = Depends(get_current_user)
):
    """
    Distill raw input into atomic knowledge units.
    """
    if req.user_id != user.user_id:
        logger.warning(f"[memory] semantic-distill unauthorized access attempt: {req.user_id} != {user.user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized.")
        
    try:
        llm = get_fast_llm()
        prompt = (
            "Extract key atomic knowledge units (memories) from the following user input.\n"
            "Format the output as a JSON object with a list of 'core_memories'.\n"
            "Each memory should have:\n"
            "- content: a short, factual statement\n"
            "- domain: the technical domain it relates to (e.g., frontend, backend, devops, database)\n"
            "- quality_score: a number from 1-5 indicating importance/certainty\n\n"
            f"Input: {req.input}\n\n"
            "JSON Output:"
        )
        
        response = await llm.ainvoke(prompt)
        
        # Clean response if markdown blocks are present
        raw_text = response.content.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(raw_text)
        
        logger.info(f"[memory] distilled {len(result.get('core_memories', []))} units for user {user.user_id[:8]}...")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"[memory] semantic-distill JSON parse error: {e}\nRaw output: {response.content}")
        return {"core_memories": []}
    except Exception as e:
        logger.error(f"[memory] semantic-distill error: {e}")
        raise HTTPException(status_code=500, detail="Failed to distill input.")
