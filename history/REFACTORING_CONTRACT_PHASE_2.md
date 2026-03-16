# PromptForge v2.0 — Refactoring Contract Phase 2

**Version:** 1.0  
**Date:** 2026-03-13  
**Phase:** History Tab — "Intelligent Memory Palace"  
**Compliance:** RULES.md v1.0  
**Prerequisites:** Phase 1 Complete

---

## PHASE 2 OVERVIEW

### Objective

Transform flat history list into **intelligent memory palace** with:
- Semantic search (powered by LangMem + Gemini embeddings)
- Session grouping (organized by conversations)
- Domain filtering (visual tags)
- Quality analytics (trends, insights)

### Duration

**5-7 days**

### Priority

**HIGH** (Showcases LangMem intelligence)

---

## 2.1 BACKEND CONTRACT (Phase 2)

### File: `api.py`

**ADD These Endpoints:**

```python
# ═══ NEW: History Search & Analytics ═══════════════

@app.post("/history/search")
async def search_history(
    query: SearchQuery,
    user: User = Depends(get_current_user)
):
    """
    Semantic search across user's prompt history using LangMem RAG.
    
    RULES.md Compliance:
    - JWT required (Security Rule #1)
    - LangMem for web app only (Memory System Rule)
    - Gemini embeddings (3072 dimensions)
    
    Body:
        {
            "text": "fastapi authentication",
            "filters": {
                "domains": ["python"],
                "min_quality": 3,
                "date_from": "2026-02-13"
            },
            "limit": 20
        }
    
    Returns:
        {"results": [...], "total": int}
    """
    try:
        from memory.langmem import query_langmem
        
        # Semantic search via LangMem (RAG)
        memories = query_langmem(
            user_id=user.user_id,
            query=query.text,
            top_k=query.limit,
            surface="web_app"  # RULES.md: LangMem is web-app exclusive
        )
        
        # Apply filters
        filtered = memories
        
        if query.filters:
            if query.filters.domains:
                filtered = [m for m in filtered 
                           if m.get('domain') in query.filters.domains]
            
            if query.filters.min_quality:
                filtered = [m for m in filtered 
                           if m.get('quality_score', {}).get('overall', 0) >= query.filters.min_quality]
        
        logger.info(f"[api] semantic search returned {len(filtered)} results")
        
        return {
            "results": filtered,
            "total": len(filtered)
        }
        
    except Exception as e:
        logger.exception("[api] search_history failed")
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/history/sessions")
async def get_history_sessions(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Get prompt history grouped by chat sessions.
    
    RULES.md Compliance:
    - RLS via user_id (Security Rule #3)
    - Pagination (Performance Target)
    
    Returns:
        {
            "sessions": [
                {
                    "session_id": "uuid",
                    "title": "FastAPI Authentication",
                    "prompt_count": 5,
                    "avg_quality": 4.2,
                    "domain": "python",
                    "prompts": [...]
                }
            ]
        }
    """
    try:
        db = get_client()
        
        # Get sessions
        sessions_result = db.table("chat_sessions")\
            .select("id, title, created_at, last_activity")\
            .eq("user_id", user.user_id)\
            .order("last_activity", desc=True)\
            .limit(limit)\
            .execute()
        
        sessions = []
        for session in sessions_result.data:
            # Get prompts for this session
            prompts_result = db.table("requests")\
                .select("*")\
                .eq("session_id", session["id"])\
                .eq("user_id", user.user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            # Calculate avg quality
            quality_scores = [
                r.get("quality_score", {}).get("overall", 0)
                for r in prompts_result.data
                if r.get("quality_score")
            ]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Get primary domain
            domains = [
                r.get("domain_analysis", {}).get("primary_domain", "general")
                for r in prompts_result.data
            ]
            primary_domain = max(set(domains), key=domains.count) if domains else "general"
            
            sessions.append({
                "session_id": session["id"],
                "title": session["title"],
                "prompt_count": len(prompts_result.data),
                "avg_quality": round(avg_quality, 2),
                "domain": primary_domain,
                "prompts": prompts_result.data,
                "created_at": session["created_at"],
                "last_activity": session["last_activity"]
            })
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.exception("[api] get_history_sessions failed")
        raise HTTPException(status_code=500, detail="Failed to load sessions")


@app.get("/history/analytics")
async def get_history_analytics(
    user: User = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=90)
):
    """
    Get user's prompt analytics and insights.
    
    RULES.md Compliance:
    - RLS via user_id (Security Rule #3)
    - Aggregation for performance
    
    Returns:
        {
            "total_prompts": 150,
            "avg_quality": 4.2,
            "unique_domains": 8,
            "hours_saved": 12.5,
            "quality_trend": [...],
            "domain_distribution": {...}
        }
    """
    try:
        db = get_client()
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get prompts
        prompts_result = db.table("requests")\
            .select("*")\
            .eq("user_id", user.user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()
        
        prompts = prompts_result.data
        
        # Calculate analytics
        total_prompts = len(prompts)
        
        quality_scores = [
            p.get("quality_score", {}).get("overall", 0)
            for p in prompts
            if p.get("quality_score")
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        domains = [
            p.get("domain_analysis", {}).get("primary_domain", "general")
            for p in prompts
        ]
        unique_domains = len(set(domains))
        
        # Estimate time saved (5 min per improved prompt)
        hours_saved = round((total_prompts * 5) / 60, 1)
        
        # Quality trend (daily averages)
        daily_quality = {}
        for p in prompts:
            date = p["created_at"][:10]  # YYYY-MM-DD
            if date not in daily_quality:
                daily_quality[date] = []
            if p.get("quality_score"):
                daily_quality[date].append(p["quality_score"].get("overall", 0))
        
        quality_trend = [
            {
                "date": date,
                "avg_quality": round(sum(scores) / len(scores), 2) if scores else 0,
                "prompt_count": len(scores)
            }
            for date, scores in sorted(daily_quality.items())
        ]
        
        # Domain distribution
        domain_counts = {}
        for d in domains:
            domain_counts[d] = domain_counts.get(d, 0) + 1
        
        return {
            "total_prompts": total_prompts,
            "avg_quality": round(avg_quality, 2),
            "unique_domains": unique_domains,
            "hours_saved": hours_saved,
            "quality_trend": quality_trend,
            "domain_distribution": domain_counts
        }
        
    except Exception as e:
        logger.exception("[api] get_history_analytics failed")
        raise HTTPException(status_code=500, detail="Failed to load analytics")
```

---

### File: `database.py`

**ADD These Functions:**

```python
# ═══ NEW: History Analytics Functions ═══════════════

def get_user_analytics(user_id: str, days: int = 30) -> Optional[dict]:
    """
    Get user's prompt analytics for specified period.
    
    Args:
        user_id: User UUID from JWT
        days: Number of days to analyze (default: 30)
        
    Returns:
        Analytics dict or None if failed
        
    Example:
        analytics = get_user_analytics("user-uuid", days=30)
    """
    try:
        db = get_client()
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = db.table("requests")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("created_at", cutoff.isoformat())\
            .execute()
        
        prompts = result.data
        
        # Calculate metrics
        total = len(prompts)
        avg_quality = sum(
            p.get("quality_score", {}).get("overall", 0)
            for p in prompts
            if p.get("quality_score")
        ) / total if total > 0 else 0
        
        domains = list(set(
            p.get("domain_analysis", {}).get("primary_domain", "general")
            for p in prompts
        ))
        
        return {
            "total_prompts": total,
            "avg_quality": round(avg_quality, 2),
            "unique_domains": len(domains),
            "domains": domains
        }
        
    except Exception as e:
        logger.error(f"[db] get_user_analytics failed: {e}")
        return None
```

---

### File: `migrations/016_add_history_indexes.sql`

**CREATE This Migration:**

```sql
-- ============================================================
-- PromptForge v2.0 - History Performance Indexes
-- ============================================================
-- Purpose: Optimize history search and analytics queries
-- Run in Supabase SQL Editor
-- Time: ~10 seconds
-- ============================================================

BEGIN;

-- Index for quality score queries
CREATE INDEX IF NOT EXISTS idx_requests_quality_score 
ON requests USING GIN (quality_score);

-- Index for domain analysis queries
CREATE INDEX IF NOT EXISTS idx_requests_domain 
ON requests ((domain_analysis->>'primary_domain'));

-- Composite index for user + date queries
CREATE INDEX IF NOT EXISTS idx_requests_user_date 
ON requests(user_id, created_at DESC);

-- Comment for documentation
COMMENT ON INDEX idx_requests_quality_score IS 
  'Phase 2: History analytics optimization';

COMMIT;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
```

---

## 2.2 FRONTEND CONTRACT (Phase 2)

### File: `features/history/hooks/useHistorySearch.ts` (NEW)

**CREATE This Hook:**

```typescript
// features/history/hooks/useHistorySearch.ts
// Semantic search with LangMem RAG
// RULES.md Compliance: Type hints, error handling, structured logging

'use client'

import { useState, useCallback } from 'react'
import { logger } from '@/lib/logger'
import type { HistoryItem } from '@/lib/api'

interface SearchFilters {
  domains?: string[]
  minQuality?: number
  dateFrom?: string
}

interface UseHistorySearchProps {
  token: string
  apiUrl: string
}

interface UseHistorySearchReturn {
  results: HistoryItem[]
  isLoading: boolean
  error: string | null
  search: (query: string, filters?: SearchFilters) => Promise<void>
}

/**
 * Semantic search across history using LangMem RAG
 */
export function useHistorySearch({
  token,
  apiUrl,
}: UseHistorySearchProps): UseHistorySearchReturn {
  const [results, setResults] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (
    query: string,
    filters?: SearchFilters
  ) => {
    try {
      setIsLoading(true)
      setError(null)

      const res = await fetch(`${apiUrl}/history/search`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: query,
          filters: filters || {},
          limit: 20,
        }),
      })

      if (!res.ok) throw new Error(`Search failed: ${res.status}`)

      const data = await res.json()
      setResults(data.results || [])

      logger.info('[useHistorySearch] search completed', {
        query,
        resultCount: data.results?.length || 0,
      })
    } catch (err) {
      logger.error('[useHistorySearch] search failed', { err, query })
      setError('Failed to search history')
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }, [token, apiUrl])

  return {
    results,
    isLoading,
    error,
    search,
  }
}
```

---

### File: `features/history/components/HistorySearchBar.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/history/components/HistorySearchBar.tsx
// Semantic search bar with domain filters

'use client'

import { useState } from 'react'
import { useHistorySearch } from '../hooks/useHistorySearch'

interface HistorySearchBarProps {
  token: string
  apiUrl: string
  onSearchResults: (results: any[]) => void
}

const DOMAIN_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'creative', label: 'Creative' },
  { value: 'business', label: 'Business' },
  { value: 'data', label: 'Data Science' },
]

export default function HistorySearchBar({
  token,
  apiUrl,
  onSearchResults,
}: HistorySearchBarProps) {
  const [query, setQuery] = useState('')
  const [selectedDomains, setSelectedDomains] = useState<string[]>([])
  
  const { search, isLoading } = useHistorySearch({ token, apiUrl })

  const handleSearch = async () => {
    if (!query.trim()) return
    
    await search(query, {
      domains: selectedDomains.length > 0 ? selectedDomains : undefined,
    })
  }

  const toggleDomain = (domain: string) => {
    setSelectedDomains(prev =>
      prev.includes(domain)
        ? prev.filter(d => d !== domain)
        : [...prev, domain]
    )
  }

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search your prompts... (semantic search powered by Gemini)"
          className="w-full px-4 py-3 pl-12 bg-layer2 border border-border-default
                   rounded-lg text-text-default placeholder-text-dim
                   focus:outline-none focus:border-kira transition-colors"
        />
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-dim" />
        <button
          onClick={handleSearch}
          disabled={isLoading || !query.trim()}
          className="absolute right-2 top-1/2 -translate-y-1/2
                   px-4 py-1.5 bg-kira text-text-inverse rounded-md
                   text-sm font-medium hover:bg-kira/90
                   disabled:opacity-50 disabled:cursor-not-allowed
                   transition-colors"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Domain filters */}
      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-text-dim">Filter by domain:</span>
        {DOMAIN_OPTIONS.map(domain => (
          <button
            key={domain.value}
            onClick={() => toggleDomain(domain.value)}
            className={`
              px-3 py-1 rounded-full text-xs font-medium
              transition-colors
              ${selectedDomains.includes(domain.value)
                ? 'bg-kira/20 text-kira border border-kira'
                : 'bg-layer2 text-text-dim border border-border-default
                   hover:border-border-strong'
              }
            `}
          >
            {domain.label}
          </button>
        ))}
      </div>
    </div>
  )
}
```

---

### File: `features/history/components/SessionGroup.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/history/components/SessionGroup.tsx
// Collapsible session group with prompts

'use client'

import { useState } from 'react'
import HistoryCard from './HistoryCard'

interface SessionGroupProps {
  session: {
    session_id: string
    title: string
    prompt_count: number
    avg_quality: number
    domain: string
    prompts: any[]
    created_at: string
  }
  onUseAgain: (prompt: string) => void
}

export default function SessionGroup({
  session,
  onUseAgain,
}: SessionGroupProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <div className="border border-border-default rounded-xl overflow-hidden bg-layer2">
      {/* Session header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between
                 bg-layer3 hover:bg-layer3/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <ChevronIcon
            className={`w-5 h-5 text-text-dim transition-transform
                       ${isExpanded ? 'rotate-90' : ''}`}
          />
          <div className="text-left">
            <h3 className="font-medium text-text-bright">
              {session.title}
            </h3>
            <p className="text-xs text-text-dim">
              {session.prompt_count} prompts • {session.domain} • 
              Avg Quality: {session.avg_quality}/5
            </p>
          </div>
        </div>
      </button>

      {/* Session prompts */}
      {isExpanded && (
        <div className="p-4 space-y-3">
          {session.prompts.map((prompt, index) => (
            <HistoryCard
              key={prompt.id || index}
              item={prompt}
              onUseAgain={onUseAgain}
            />
          ))}
        </div>
      )}
    </div>
  )
}
```

---

### File: `features/history/components/HistoryAnalytics.tsx` (NEW)

**CREATE This Component:**

```typescript
// features/history/components/HistoryAnalytics.tsx
// Analytics dashboard with charts

'use client'

import { useEffect, useState } from 'react'
import { logger } from '@/lib/logger'

interface HistoryAnalyticsProps {
  token: string
  apiUrl: string
  days?: number
}

interface AnalyticsData {
  total_prompts: number
  avg_quality: number
  unique_domains: number
  hours_saved: number
  quality_trend: Array<{
    date: string
    avg_quality: number
    prompt_count: number
  }>
  domain_distribution: Record<string, number>
}

export default function HistoryAnalytics({
  token,
  apiUrl,
  days = 30,
}: HistoryAnalyticsProps) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const res = await fetch(`${apiUrl}/history/analytics?days=${days}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })

        if (!res.ok) throw new Error(`Failed to load analytics: ${res.status}`)

        const data = await res.json()
        setAnalytics(data)

        logger.info('[HistoryAnalytics] loaded analytics', {
          totalPrompts: data.total_prompts,
          avgQuality: data.avg_quality,
        })
      } catch (err) {
        logger.error('[HistoryAnalytics] load failed', { err })
      } finally {
        setIsLoading(false)
      }
    }

    loadAnalytics()
  }, [token, apiUrl, days])

  if (isLoading) {
    return <div className="p-8 text-center text-text-dim">Loading analytics...</div>
  }

  if (!analytics) {
    return <div className="p-8 text-center text-text-dim">No analytics data available</div>
  }

  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Prompts Improved"
          value={analytics.total_prompts.toString()}
          subtext={`Last ${days} days`}
        />
        <StatCard
          label="Avg Quality"
          value={`${analytics.avg_quality}/5`}
          subtext="Across all domains"
        />
        <StatCard
          label="Domains Explored"
          value={analytics.unique_domains.toString()}
          subtext="Unique domains"
        />
        <StatCard
          label="Time Saved"
          value={`${analytics.hours_saved}h`}
          subtext="~5 min per prompt"
        />
      </div>

      {/* Quality trend chart */}
      <div className="p-6 bg-layer2 rounded-xl border border-border-default">
        <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-4">
          Quality Trend ({days} days)
        </h3>
        <div className="h-32 flex items-end gap-1">
          {analytics.quality_trend.map((day, index) => (
            <div
              key={day.date}
              className="flex-1 bg-kira/20 hover:bg-kira/40 transition-colors rounded-t"
              style={{ height: `${(day.avg_quality / 5) * 100}%` }}
              title={`${day.date}: ${day.avg_quality}/5 (${day.prompt_count} prompts)`}
            />
          ))}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-text-dim">
          <span>{analytics.quality_trend[0]?.date}</span>
          <span>{analytics.quality_trend[analytics.quality_trend.length - 1]?.date}</span>
        </div>
      </div>

      {/* Domain distribution */}
      <div className="p-6 bg-layer2 rounded-xl border border-border-default">
        <h3 className="font-mono text-[10px] tracking-wider uppercase text-text-dim mb-4">
          Domain Distribution
        </h3>
        <div className="space-y-2">
          {Object.entries(analytics.domain_distribution)
            .sort((a, b) => b[1] - a[1])
            .map(([domain, count]) => (
              <div key={domain} className="flex items-center justify-between">
                <span className="text-sm text-text-default">{domain}</span>
                <span className="text-sm text-text-dim">{count} prompts</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}

// Simple stat card component
function StatCard({
  label,
  value,
  subtext,
}: {
  label: string
  value: string
  subtext: string
}) {
  return (
    <div className="p-4 bg-layer2 rounded-xl border border-border-default">
      <p className="text-xs text-text-dim mb-1">{label}</p>
      <p className="text-2xl font-bold text-text-bright">{value}</p>
      <p className="text-[10px] text-text-dim mt-1">{subtext}</p>
    </div>
  )
}
```

---

## PHASE 2 ACCEPTANCE CRITERIA

### Backend (Must Pass All)

- [ ] `/history/search` POST endpoint performs semantic search
- [ ] `/history/sessions` GET endpoint returns grouped sessions
- [ ] `/history/analytics` GET endpoint returns analytics data
- [ ] LangMem RAG integration working (Gemini embeddings)
- [ ] Migration `016_add_history_indexes.sql` runs successfully
- [ ] All queries use RLS (user_id filtering)
- [ ] Type hints + docstrings on all functions
- [ ] Structured logging in all endpoints

### Frontend (Must Pass All)

- [ ] `useHistorySearch` hook performs semantic search
- [ ] `HistorySearchBar` component with domain filters
- [ ] `SessionGroup` component collapsible
- [ ] `HistoryAnalytics` dashboard displays stats
- [ ] Quality trend chart renders correctly
- [ ] Domain distribution shows all domains
- [ ] Loading states during async operations
- [ ] Error states with user-friendly messages

---

**Contract continues with Phase 3 (Profile Tab) in separate document...**
