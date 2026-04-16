# MCP Setup Guide — PromptForge v2.0

Connect Cursor, Claude Desktop, Windsurf, Cline, Zed, or Continue.dev to PromptForge's AI prompt engineering engine via the Model Context Protocol (MCP).

---

## What is PromptForge MCP?

PromptForge exposes an MCP server with **2 tools** that let your AI editor improve prompts through a 4-agent swarm analysis:

| Tool | Description |
|------|-------------|
| `forge_refine` | Improve a prompt through 4-agent AI swarm analysis (intent, context, domain, quality gate) |
| `forge_chat` | Conversational prompt improvement with memory — classifies your message and routes to the right handler |

The MCP server runs locally, communicates over stdio, and authenticates with a long-lived JWT token.

---

## Prerequisites

- **Python 3.9+** installed
- **PromptForge running** on `http://localhost:8000` (the API server)
- **One MCP-compatible client**: Cursor, Claude Desktop, Windsurf, Cline, Zed, or Continue.dev

---

## Step 1: Generate an MCP Token

You need a long-lived JWT token to authenticate with the MCP server. Tokens are valid for **365 days**.

```bash
curl -X POST http://localhost:8000/mcp/generate-token \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "mcp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in_days": 365,
  "expires_at": "2027-04-14T00:00:00+00:00",
  "instructions": "Copy to Cursor MCP config. Valid for 365 days."
}
```

Copy the `mcp_token` value — you'll need it in Step 2.

> **Note:** Your Supabase JWT is the token you get when you log in to the PromptForge web app. You can find it in your browser's local storage under `sb-<project-ref>-auth-token`.

---

## Step 2: Configure Your MCP Client

### Cursor

1. Open **Settings** → **Features** → **MCP Servers**
2. Click **Add New MCP Server**
3. Fill in:
   - **Name:** `PromptForge`
   - **Type:** `stdio`
   - **Command:** `python`
   - **Arguments:** `C:\Users\user\OneDrive\Desktop\newnew\mcp\server.py`
   - **Environment Variables:**
     ```
     MCP_JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     SUPABASE_URL=https://your-project.supabase.co
     ```
4. Click **Save**

### Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "promptforge": {
      "command": "python",
      "args": [
        "C:\\Users\\user\\OneDrive\\Desktop\\newnew\\mcp\\server.py"
      ],
      "env": {
        "MCP_JWT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "SUPABASE_URL": "https://your-project.supabase.co"
      }
    }
  }
}
```

Then restart Claude Desktop.

### Windsurf

Same as Cursor:
1. **Settings** → **Features** → **MCP Servers** → **Add**
2. Use the same configuration as Cursor above.

### Cline (VS Code Extension)

1. Open VS Code → **Cline** extension
2. Click **MCP Settings** (gear icon in Cline panel)
3. Add the server configuration:
   ```json
   {
     "mcpServers": {
       "promptforge": {
         "command": "python",
         "args": ["C:\\Users\\user\\OneDrive\\Desktop\\newnew\\mcp\\server.py"],
         "env": {
           "MCP_JWT_TOKEN": "your-token-here",
           "SUPABASE_URL": "https://your-project.supabase.co"
         }
       }
     }
   }
   ```
4. Save and reload VS Code.

### Zed

In Zed settings (`settings.json`):

```json
{
  "context_servers": {
    "promptforge": {
      "command": {
        "path": "python",
        "args": ["C:\\Users\\user\\OneDrive\\Desktop\\newnew\\mcp\\server.py"],
        "env": {
          "MCP_JWT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "SUPABASE_URL": "https://your-project.supabase.co"
        }
      }
    }
  }
}
```

### Continue.dev

Create or edit `.continue/config.yaml` in your project root:

```yaml
models:
  - provider: mcp
    title: PromptForge
    params:
      command: python
      args:
        - C:\Users\user\OneDrive\Desktop\newnew\mcp\server.py
      env:
        MCP_JWT_TOKEN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        SUPABASE_URL: https://your-project.supabase.co
```

---

## Step 3: Test It Works

Once configured, open your MCP client and verify the tools are available:

**Test 1 — Check tools are loaded:**
Ask your MCP client: "What tools do you have?"
Expected: You should see `forge_refine` and `forge_chat` listed.

**Test 2 — Refine a prompt:**
Use the `forge_refine` tool:
```json
{
  "prompt": "write a blog post about AI",
  "session_id": "mcp-test-001"
}
```

Expected output: An improved prompt with added role assignment, target audience, tone guidance, and output format specifications.

**Test 3 — Chat mode:**
Use the `forge_chat` tool:
```json
{
  "message": "Help me write a prompt for generating API documentation",
  "session_id": "mcp-test-002"
}
```

Expected output: A conversational response that either improves your prompt or asks clarifying questions.

---

## Troubleshooting

### "Module not found" or import errors

**Problem:** Python can't find the PromptForge modules.

**Fix:** Ensure you're using the correct Python environment:
```bash
# Activate your virtual environment first
cd C:\Users\user\OneDrive\Desktop\newnew
python mcp\server.py
```

### "Authentication required" error

**Problem:** MCP_JWT_TOKEN is missing or expired.

**Fix:**
1. Regenerate a token via `POST /mcp/generate-token`
2. Update the `MCP_JWT_TOKEN` in your client config
3. Restart the MCP client

### "Connection refused" or server not starting

**Problem:** The MCP server can't start.

**Fix:**
1. Verify Python 3.9+ is installed: `python --version`
2. Verify dependencies: `pip install -r requirements.txt`
3. Verify `.env` file exists in the project root with required keys
4. Check that port 8000 isn't already in use

### Tools not showing up in client

**Problem:** Your MCP client doesn't show `forge_refine` or `forge_chat`.

**Fix:**
1. Verify the MCP server path is correct (use full absolute path)
2. Restart your MCP client after saving config
3. Check the client's MCP logs for errors
4. For Claude Desktop: verify JSON syntax in `claude_desktop_config.json`

### Token expired

**Problem:** Your MCP token has expired (365-day lifetime).

**Fix:** Generate a new token via `POST /mcp/generate-token` and update your client config.

---

## Tools Reference

### `forge_refine`

Improves a prompt through 4-agent swarm analysis.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | The prompt to improve (5-2000 characters) |
| `session_id` | string | Yes | Unique session identifier for tracking |

**Example:**
```json
{
  "prompt": "Create a landing page copy",
  "session_id": "my-session-123"
}
```

**Returns:**
```json
{
  "improved_prompt": "Act as a senior copywriter... [full engineered prompt]",
  "quality_score": { "specificity": 4, "clarity": 5, "actionability": 4 },
  "breakdown": {
    "intent": { "primary_intent": "creative_writing", ... },
    "context": { "skill_level": "intermediate", ... },
    "domain": { "primary_domain": "marketing", ... }
  }
}
```

### `forge_chat`

Conversational prompt improvement with memory and classification.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User message for improvement (1-2000 characters) |
| `session_id` | string | Yes | Unique session identifier for tracking |

**Example:**
```json
{
  "message": "Make it more professional",
  "session_id": "my-session-123"
}
```

**Returns:**
```json
{
  "type": "followup_refined",
  "reply": "Updated! Here's your refined prompt...",
  "improved_prompt": "[refined prompt]",
  "breakdown": null,
  "session_id": "my-session-123"
}
```

---

## Architecture Notes

- **LangMem is NEVER called from MCP** — MCP uses Supermemory exclusively for context
- **Supermemory is NEVER called from the web app** — Surface isolation is enforced
- **Trust levels** progress from 0 (cold) → 1 (warm) → 2 (tuned) based on web app usage
- All MCP communication is over **stdio** (JSON-RPC 2.0 protocol)
- Tokens can be revoked via `POST /mcp/revoke-token/{token_id}` if compromised
