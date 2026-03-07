# Dependencies & Environment Setup

## Required Dependencies
**No new dependencies required** (native MCP implementation)

## Development Dependencies
**File:** `requirements-dev.txt`
```
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code Quality
black==23.12.0
flake8==6.1.0
mypy==1.7.1
isort==5.13.2

# Development Tools
pre-commit==3.6.0
jupyter==1.0.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.4.8
```

## Environment Variables
**Existing variables sufficient:**
- SUPABASE_URL
- SUPABASE_JWT_SECRET
- SUPABASE_KEY
- LLM API keys (Pollinations/Groq/OpenAI)

## Development Setup
1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Configure MCP client for testing:
   - Install Cursor or Claude Desktop
   - Configure MCP server endpoint

## Database Setup
**New table required:** `supermemory_facts`
```sql
CREATE TABLE supermemory_facts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  fact text NOT NULL,
  context jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- RLS Policy
CREATE POLICY "users own supermemory" ON supermemory_facts
  FOR ALL USING (auth.uid() = user_id);
```

## Testing Environment
- Unit tests: pytest
- Integration tests: MCP client simulation
- Code quality: black, flake8, mypy
- Documentation: mkdocs

## Deployment Considerations
- MCP server runs alongside web API
- Shared environment variables
- Separate logging for MCP operations
- Monitor MCP-specific metrics</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\dependencies.md