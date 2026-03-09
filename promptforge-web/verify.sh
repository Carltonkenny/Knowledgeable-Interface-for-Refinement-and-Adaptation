#!/bin/bash
# promptforge-web/verify.sh
# Usage: bash verify.sh
# Run from promptforge-web/ directory.
# Exit 0 = all checks passed. Exit 1 = something is wrong.

set -e
cd "$(dirname "$0")"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PromptForge Frontend — Verify"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. TypeScript ──────────────────────────────────────────────────────────
echo "[ 1/5 ] TypeScript..."
npx tsc --noEmit
echo "  ✅ TypeScript clean"
echo ""

# ── 2. Build ───────────────────────────────────────────────────────────────
echo "[ 2/5 ] Build..."
npm run build > /tmp/pf_build.log 2>&1 || {
  echo "  ❌ Build failed. Last 20 lines:"
  tail -20 /tmp/pf_build.log
  exit 1
}
echo "  ✅ Build passes"
echo ""

# ── 3. Security scan — forbidden strings in source ────────────────────────
echo "[ 3/5 ] Security scan..."
FORBIDDEN=("intent agent" "context agent" "domain agent" "prompt_engineer" "GPT-4o" "gpt-4o-mini" "langmem" "LangGraph" "fly.dev" "cckznjkzsfypssgecyya" "openai.com")
FAIL=0
for term in "${FORBIDDEN[@]}"; do
  FOUND=$(grep -r "$term" app/ features/ --include="*.tsx" --include="*.ts" -l 2>/dev/null | grep -v "\.test\." || true)
  if [ -n "$FOUND" ]; then
    echo "  ❌ SECURITY: '$term' found in:"
    echo "$FOUND" | sed 's/^/     /'
    FAIL=1
  fi
done
if [ $FAIL -eq 1 ]; then exit 1; fi
echo "  ✅ Security scan clean"
echo ""

# ── 4. No rogue fetch() outside lib/ ──────────────────────────────────────
echo "[ 4/5 ] Architecture check (no rogue fetch)..."
ROGUE=$(grep -r "fetch(" app/ features/ components/ --include="*.tsx" --include="*.ts" -l 2>/dev/null | grep -v "route\.ts" || true)
if [ -n "$ROGUE" ]; then
  echo "  ❌ fetch() found outside lib/api.ts or lib/stream.ts in:"
  echo "$ROGUE" | sed 's/^/     /'
  exit 1
fi
echo "  ✅ No rogue fetch() calls"
echo ""

# ── 5. No 'use client' in app/(marketing)/ ────────────────────────────────
echo "[ 5/5 ] Server component check..."
if [ -d "app/(marketing)" ]; then
  CLIENT=$(grep -r "'use client'" "app/(marketing)/" --include="*.tsx" --include="*.ts" -l 2>/dev/null || true)
  if [ -n "$CLIENT" ]; then
    echo "  ❌ 'use client' found in app/(marketing)/:"
    echo "$CLIENT" | sed 's/^/     /'
    exit 1
  fi
fi
echo "  ✅ Server components clean"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ALL CHECKS PASSED ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
