# Component 3: Tool Implementations (25%)
**Purpose:** Map existing API endpoints to MCP tools with authentication and structured responses.

## Requirements (from RULES.md)
- forge_refine: Maps to POST /refine
- forge_chat: Maps to POST /chat
- Handle authentication via JWT
- Return structured responses
- Error handling with fallbacks

## Implementation Steps
1. Implement tool handlers in MCP server
2. Add JWT authentication for tool calls
3. Map MCP parameters to API request formats
4. Handle API responses and errors
5. Test tool execution in MCP clients

## Tool Specifications

### forge_refine
**Parameters:**
- prompt (str): The prompt to improve
- session_id (str): Unique session identifier

**Returns:**
```json
{
  "improved_prompt": "string",
  "quality_score": {
    "specificity": 1-5,
    "clarity": 1-5,
    "actionability": 1-5
  },
  "breakdown": {
    "intent": {...},
    "context": {...},
    "domain": {...}
  }
}
```

### forge_chat
**Parameters:**
- message (str): User message for improvement
- session_id (str): Unique session identifier

**Returns:**
```json
{
  "type": "prompt_improved",
  "reply": "string",
  "improved_prompt": "string",
  "breakdown": {...}
}
```

## Authentication
- Generate JWT tokens for MCP tool calls
- Use existing Supabase JWT secret
- Include user_id in token payload
- Validate tokens on API calls

## Error Handling
- API timeout errors
- Invalid parameters
- Authentication failures
- Rate limiting
- Fallback responses for failures

## Parameter Mapping
- MCP `prompt` → API `prompt`
- MCP `message` → API `message`
- MCP `session_id` → API `session_id`
- Add `user_id` from JWT to API calls

## Response Formatting
- Convert API responses to MCP format
- Handle streaming responses (if applicable)
- Include error details in responses
- Maintain consistent structure

## Testing
- Tool registration verification
- Parameter validation
- Authentication flow
- Error condition handling
- Response format compliance</content>
<parameter name="filePath">c:\Users\user\OneDrive\Desktop\newnew\DOCS\phase_3\tools.md