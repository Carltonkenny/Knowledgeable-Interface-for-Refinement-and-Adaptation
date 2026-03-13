# PromptForge v2.0 — Refactoring Contract Phase 3

**Version:** 1.0  
**Date:** 2026-03-13  
**Phase:** Profile Tab — "Living Digital Twin"  
**Compliance:** RULES.md v1.0  
**Prerequisites:** Phase 1 & 2 Complete

---

## PHASE 3 OVERVIEW

### Objective

Transform basic profile display into **living digital twin** with:
- Editable username + identity
- Domain niches visualization (LangMem-powered)
- Quality trend sparkline (interactive)
- LangMem memory preview
- Usage statistics dashboard

### Duration

**5-7 days**

### Priority

**MEDIUM** (Personalization + LangMem showcase)

---

## 3.1 BACKEND CONTRACT (Phase 3)

### File: `api.py`

**ADD These Endpoints:**

```python
# ═══ NEW: Profile Enhancement ══════════════════════

@app.patch("/user/username")
async def update_username(
    username: str,
    user: User = Depends(get_current_user)
):
    """
    Update user's username (editable identity).
    
    RULES.md Compliance:
    - JWT required (Security Rule #1)
    - Input validation (Security Rule #9)
    - LangMem embedding for identity changes
    
    Body:
        {"username": "new_username_abc"}
    
    Validation:
        - 3-20 characters
        - Alphanumeric + underscores only
        - Unique per user
    
    Returns:
        {"username": "new_username_abc", "status": "ok"}
    """
    try:
        import re
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            raise HTTPException(
                status_code=400,
                detail="Username must be 3-20 characters, alphanumeric and underscores only"
            )
        
        db = get_client()
        
        # Update profile
        db.table("user_profiles")\
            .update({"username": username})\
            .eq("user_id", user.user_id)\
            .execute()
        
        # LangMem: Embed username change
        from memory.langmem import write_to_langmem
        write_to_langmem(user.user_id, {
            "type": "identity_update",
            "content": f"User changed username to: {username}"
        })
        
        logger.info(f"[api] updated username for user {user.user_id[:8]}...")
        return {"username": username, "status": "ok"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[api] update_username failed")
        raise HTTPException(status_code=500, detail="Failed to update username")


@app.get("/user/domains")
async def get_user_domains(
    user: User = Depends(get_current_user)
):
    """
    Get user's domain niches from LangMem.
    
    RULES.md Compliance:
    - LangMem for web app only (Memory System Rule)
    - RLS via user_id (Security Rule #3)
    
    Returns:
        {
            "domains": [
                {
                    "name": "python",
                    "confidence": 0.8,
                    "prompt_count": 25,
                    "avg_quality": 4.2
                }
            ]
        }
    """
    try:
        db = get_client()
        
        # Query LangMem for domain statistics
        result = db.table("langmem_memories")\
            .select("domain, quality_score")\
            .eq("user_id", user.user_id)\
            .execute()
        
        # Aggregate by domain
        domain_stats = {}
        for row in result.data:
            domain = row.get("domain", "general")
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "count": 0,
                    "quality_scores": []
                }
            
            domain_stats[domain]["count"] += 1
            if row.get("quality_score"):
                quality = row["quality_score"].get("overall", 0)
                domain_stats[domain]["quality_scores"].append(quality)
        
        # Format response
        domains = []
        for name, stats in domain_stats.items():
            avg_quality = (
                sum(stats["quality_scores"]) / len(stats["quality_scores"])
                if stats["quality_scores"] else 0
            )
            
            # Confidence based on prompt count (10 prompts = 100% confidence)
            confidence = min(1.0, stats["count"] / 10)
            
            domains.append({
                "name": name,
                "confidence": round(confidence, 2),
                "prompt_count": stats["count"],
                "avg_quality": round(avg_quality, 2)
            })
        
        # Sort by confidence (highest first)
        domains.sort(key=lambda d: d["confidence"], reverse=True)
        
        return {"domains": domains}
        
    except Exception as e:
        logger.exception("[api] get_user_domains failed")
        raise HTTPException(status_code=500, detail="Failed to load domains")


@app.get("/user/memories")
async def get_user_memories(
    user: User = Depends(get_current_user),
    limit: int = Query(default=5, ge=1, le=20)
):
    """
    Get user's top memories from LangMem (preview).
    
    RULES.md Compliance:
    - LangMem for web app only (Memory System Rule)
    - RLS via user_id (Security Rule #3)
    
    Returns:
        {
            "memories": [
                {
                    "id": "uuid",
                    "content": "User prefers concise prompts",
                    "domain": "general",
                    "quality_score": {...},
                    "created_at": "timestamp",
                    "similarity_score": 0.92
                }
            ]
        }
    """
    try:
        from memory.langmem import query_langmem
        
        # Query LangMem for profile-related memories
        memories = query_langmem(
            user_id=user.user_id,
            query="user preferences profile identity",
            top_k=limit,
            surface="web_app"
        )
        
        return {"memories": memories}
        
    except Exception as e:
        logger.exception("[api] get_user_memories failed")
        raise HTTPException(status_code=500, detail="Failed to load memories")


@app.get("/user/quality-trend")
async def get_quality_trend(
    user: User = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=90)
):
    """
    Get user's quality trend over time (for sparkline chart).
    
    RULES.md Compliance:
    - RLS via user_id (Security Rule #3)
    - Aggregation for performance
    
    Returns:
        {
            "trend": [
                {
                    "date": "2026-03-01",
                    "avg_quality": 4.2,
                    "prompt_count": 5
                }
            ]
        }
    """
    try:
        db = get_client()
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get prompts with quality scores
        result = db.table("requests")\
            .select("quality_score, created_at")\
            .eq("user_id", user.user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()
        
        # Group by date
        daily_quality = {}
        for row in result.data:
            date = row["created_at"][:10]  # YYYY-MM-DD
            if date not in daily_quality:
                daily_quality[date] = []
            
            if row.get("quality_score"):
                quality = row["quality_score"].get("overall", 0)
                daily_quality[date].append(quality)
        
        # Format trend
        trend = [
            {
                "date": date,
                "avg_quality": round(sum(scores) / len(scores), 2) if scores else 0,
                "prompt_count": len(scores)
            }
            for date, scores in sorted(daily_quality.items())
        ]
        
        return {"trend": trend}
        
    except Exception as e:
        logger.exception("[api] get_quality_trend failed")
        raise HTTPException(status_code=500, detail="Failed to load quality trend")


@app.get("/user/stats")
async def get_user_stats(
    user: User = Depends(get_current_user)
):
    """
    Get comprehensive user statistics dashboard.
    
    RULES.md Compliance:
    - RLS via user_id (Security Rule #3)
    - Aggregation for performance
    
    Returns:
        {
            "total_sessions": 15,
            "total_prompts": 150,
            "avg_quality": 4.2,
            "top_domain": "python",
            "top_domain_quality": 4.5,
            "trust_level": 2,
            "hours_saved": 12.5
        }
    """
    try:
        db = get_client()
        
        # Get session count
        sessions_result = db.table("chat_sessions")\
            .select("id", count="exact")\
            .eq("user_id", user.user_id)\
            .execute()
        
        # Get prompt stats
        prompts_result = db.table("requests")\
            .select("quality_score, domain_analysis")\
            .eq("user_id", user.user_id)\
            .execute()
        
        prompts = prompts_result.data
        
        # Calculate stats
        total_prompts = len(prompts)
        quality_scores = [
            p.get("quality_score", {}).get("overall", 0)
            for p in prompts
            if p.get("quality_score")
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Find top domain
        domain_qualities = {}
        for p in prompts:
            domain = p.get("domain_analysis", {}).get("primary_domain", "general")
            quality = p.get("quality_score", {}).get("overall", 0)
            
            if domain not in domain_qualities:
                domain_qualities[domain] = []
            domain_qualities[domain].append(quality)
        
        top_domain = max(
            domain_qualities.keys(),
            key=lambda d: sum(domain_qualities[d]) / len(domain_qualities[d]) if domain_qualities[d] else 0,
            default="general"
        )
        top_domain_quality = round(
            sum(domain_qualities.get(top_domain, [0])) / 
            max(len(domain_qualities.get(top_domain, [1])), 1),
            2
        )
        
        # Trust level (0-2 based on session count)
        session_count = sessions_result.count
        trust_level = 2 if session_count >= 30 else 1 if session_count >= 10 else 0
        
        # Time saved
        hours_saved = round((total_prompts * 5) / 60, 1)
        
        return {
            "total_sessions": session_count,
            "total_prompts": total_prompts,
            "avg_quality": round(avg_quality, 2),
            "top_domain": top_domain,
            "top_domain_quality": top_domain_quality,
            "trust_level": trust_level,
            "hours_saved": hours_saved
        }
        
    except Exception as e:
        logger.exception("[api] get_user_stats failed")
        raise HTTPException(status_code=500, detail="Failed to load stats")
```

---

### File: `migrations/017_add_username_to_profiles.sql`

**CREATE This Migration:**

```sql
-- ============================================================
-- PromptForge v2.0 - Add Username to User Profiles
-- ============================================================
-- Purpose: Enable editable user identity
-- Run in Supabase SQL Editor
-- Time: ~5 seconds
-- ============================================================

BEGIN;

-- Add username column
ALTER TABLE user_profiles
ADD COLUMN username TEXT UNIQUE;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_username 
ON user_profiles(username);

-- Comment for documentation
COMMENT ON COLUMN user_profiles.username IS 
  'Editable username (Phase 3: Living Digital Twin)';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
```

---

## 3.2 FRONTEND CONTRACT (Phase 3)

### File: `features/profile/hooks/useProfile.ts`

**MODIFY Existing Hook:**

```typescript
// MODIFY features/profile/hooks/useProfile.ts
// ADD these new return values

export function useProfile(userId: string) {
  // ... existing code ...
  
  // ADD: Username editing state
  const [isEditingUsername, setIsEditingUsername] = useState(false)
  const [editableUsername, setEditableUsername] = useState('')
  
  // ADD: Username update function
  const updateUsername = useCallback(async (newUsername: string) => {
    try {
      const res = await fetch(`${apiUrl}/user/username`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: newUsername }),
      })
      
      if (!res.ok) throw new Error(`Failed: ${res.status}`)
      
      const data = await res.json()
      setProfile(prev => prev ? {...prev, username: data.username} : null)
      setIsEditingUsername(false)
      
      logger.info('[useProfile] username updated', { username: data.username })
    } catch (err) {
      logger.error('[useProfile] updateUsername failed', { err })
      throw err
    }
  }, [token, apiUrl])
  
  // ADD: Load domains
  const [domains, setDomains] = useState([])
  
  useEffect(() => {
    async function loadDomains() {
      try {
        const res = await fetch(`${apiUrl}/user/domains`, {
          headers: { 'Authorization': `Bearer ${token}` },
        })
        const data = await res.json()
        setDomains(data.domains || [])
      } catch (err) {
        logger.error('[useProfile] loadDomains failed', { err })
      }
    }
    
    loadDomains()
  }, [token, apiUrl])
  
  // ADD: Load memories
  const [memories, setMemories] = useState([])
  
  useEffect(() => {
    async function loadMemories() {
      try {
        const res = await fetch(`${apiUrl}/user/memories?limit=5`, {
          headers: { 'Authorization': `Bearer ${token}` },
        })
        const data = await res.json()
        setMemories(data.memories || [])
      } catch (err) {
        logger.error('[useProfile] loadMemories failed', { err })
      }
    }
    
    loadMemories()
  }, [token, apiUrl])
  
  return {
    profile,
    sessionCount,
    trustLevel,
    personaDotColor,
    isLoading,
    // ADD:
    isEditingUsername,
    editableUsername,
    setEditableUsername,
    setIsEditingUsername,
    updateUsername,
    domains,
    memories,
  }
}
```

---

### File: `features/profile/components/UsernameEditor.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/profile/components/UsernameEditor.tsx
// Editable username with validation

'use client'

import { useState } from 'react'
import { useProfile } from '../hooks/useProfile'

interface UsernameEditorProps {
  userId: string
  currentUsername: string
  onUpdate: (username: string) => void
}

export default function UsernameEditor({
  userId,
  currentUsername,
  onUpdate,
}: UsernameEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [localValue, setLocalValue] = useState(currentUsername)
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const validateUsername = (username: string): boolean => {
    if (username.length < 3 || username.length > 20) {
      setError('Username must be 3-20 characters')
      return false
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setError('Only letters, numbers, and underscores allowed')
      return false
    }
    
    return true
  }

  const handleSave = async () => {
    if (!validateUsername(localValue)) return
    
    setIsSaving(true)
    try {
      await onUpdate(localValue)
      setIsEditing(false)
      setError('')
    } catch (err) {
      setError('Failed to update username')
    } finally {
      setIsSaving(false)
    }
  }

  if (!isEditing) {
    return (
      <button
        onClick={() => setIsEditing(true)}
        className="group flex items-center gap-2 hover:text-kira transition-colors"
      >
        <span className="text-xl font-bold text-text-bright">
          {currentUsername}
        </span>
        <EditIcon className="w-4 h-4 text-text-dim opacity-0 group-hover:opacity-100 transition-opacity" />
      </button>
    )
  }

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSave()}
        disabled={isSaving}
        className="w-full px-3 py-2 bg-layer2 border border-border-default
                 rounded-lg text-text-default focus:outline-none focus:border-kira"
        placeholder="Username"
      />
      
      {error && (
        <p className="text-xs text-error">{error}</p>
      )}
      
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={isSaving || !validateUsername(localValue)}
          className="px-3 py-1 bg-kira text-text-inverse rounded-md text-sm
                   hover:bg-kira/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
        <button
          onClick={() => {
            setIsEditing(false)
            setLocalValue(currentUsername)
            setError('')
          }}
          className="px-3 py-1 bg-layer2 text-text-default rounded-md text-sm
                   hover:bg-layer3"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
```

---

### File: `features/profile/components/DomainNiches.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/profile/components/DomainNiches.tsx
// Visual domain niche cloud

'use client'

interface DomainNichesProps {
  domains: Array<{
    name: string
    confidence: number
    prompt_count: number
    avg_quality: number
  }>
}

export default function DomainNiches({ domains }: DomainNichesProps) {
  if (domains.length === 0) {
    return (
      <div className="text-center text-text-dim py-8">
        No domain niches yet. Start prompting to build your expertise!
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
        Your Domain Niches
      </h3>
      
      <div className="flex flex-wrap gap-2">
        {domains.map(domain => (
          <div
            key={domain.name}
            className="px-4 py-2 bg-layer2 border border-border-default
                     rounded-full hover:border-kira transition-colors
                     cursor-default"
            title={`${domain.prompt_count} prompts • Avg quality: ${domain.avg_quality}/5`}
          >
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-bright">{domain.name}</span>
              
              {/* Confidence dots */}
              <div className="flex gap-0.5">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-1.5 h-1.5 rounded-full ${
                      i < Math.round(domain.confidence * 5)
                        ? 'bg-kira'
                        : 'bg-border-subtle'
                    }`}
                  />
                ))}
              </div>
              
              <span className="text-xs text-text-dim">
                {domain.prompt_count}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <p className="text-xs text-text-dim">
        Confidence based on prompt count and quality scores
      </p>
    </div>
  )
}
```

---

### File: `features/profile/components/LangMemPreview.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/profile/components/LangMemPreview.tsx
// What Kira remembers about you

'use client'

interface LangMemPreviewProps {
  memories: Array<{
    content: string
    domain: string
    quality_score: Record<string, number>
    created_at: string
    similarity_score: number
  }>
}

export default function LangMemPreview({ memories }: LangMemPreviewProps) {
  if (memories.length === 0) {
    return (
      <div className="text-center text-text-dim py-8">
        Kira is still learning about you. Keep prompting!
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim">
        What Kira Remembers
      </h3>
      
      <div className="space-y-2">
        {memories.map((memory, index) => (
          <div
            key={memory.id || index}
            className="p-3 bg-layer2 border border-border-default
                     rounded-lg hover:border-kira/50 transition-colors"
          >
            <p className="text-sm text-text-default mb-2">
              {memory.content}
            </p>
            
            <div className="flex items-center justify-between text-xs text-text-dim">
              <span className="px-2 py-0.5 bg-layer3 rounded-full">
                {memory.domain}
              </span>
              <span>
                Quality: {memory.quality_score?.overall || 0}/5
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <button className="text-sm text-kira hover:underline">
        View all memories →
      </button>
    </div>
  )
}
```

---

## PHASE 3 ACCEPTANCE CRITERIA

### Backend (Must Pass All)

- [ ] `/user/username` PATCH endpoint updates username
- [ ] `/user/domains` GET endpoint returns domain niches
- [ ] `/user/memories` GET endpoint returns LangMem memories
- [ ] `/user/quality-trend` GET endpoint returns trend data
- [ ] `/user/stats` GET endpoint returns comprehensive stats
- [ ] Migration `017_add_username_to_profiles.sql` runs successfully
- [ ] Username validation (3-20 chars, alphanumeric + underscore)
- [ ] LangMem integration for identity updates
- [ ] All functions have type hints + docstrings
- [ ] Structured logging in all endpoints

### Frontend (Must Pass All)

- [ ] `UsernameEditor` component with validation
- [ ] `DomainNiches` component with confidence visualization
- [ ] `LangMemPreview` component shows memories
- [ ] Editable username (click to edit, save to update)
- [ ] Domain confidence dots (5-dot visualization)
- [ ] Quality trend sparkline (interactive)
- [ ] Usage statistics dashboard
- [ ] Loading states during async operations
- [ ] Error states with user-friendly messages

---

## CONTRACT COMPLETE

### Summary of All Phases

| Phase | Tab | Status | Duration |
|-------|-----|--------|----------|
| **Phase 1** | Chat (Multi-Chat) | Ready | 5-7 days |
| **Phase 2** | History (Memory Palace) | Ready | 5-7 days |
| **Phase 3** | Profile (Digital Twin) | Ready | 5-7 days |

### Total Implementation Time

**15-21 days** (3 weeks)

### Expected Outcome

After all 3 phases:
- ✅ Multi-chat session management
- ✅ Semantic search with LangMem RAG
- ✅ Intelligent history grouping
- ✅ Editable user identity
- ✅ Domain niche visualization
- ✅ LangMem memory preview
- ✅ Comprehensive analytics dashboard

**Your PromptForge v2.0 will be a 2026 professional-grade AI prompt engineering platform.**

---

**Contract Version:** 1.0  
**Last Updated:** 2026-03-13  
**Ready for Implementation:** YES

*All contracts follow RULES.md v1.0 engineering standards. No AI slop. Senior-level code quality.*
