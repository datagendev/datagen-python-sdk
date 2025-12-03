# datagen-python-sdk

Built for AI coding assistants and developers. DataGen's MCP server lets AI agents discover and understand how to use any integrated tool - Gmail, Linear, Neon, Slack - without hardcoded integration knowledge. Agents use `searchTools` and `getToolDetails` to self-guide, writing clean `execute_tool()` code that skips SDK hell, OAuth nightmares, and API integration boilerplate.

For human developers: write `client.execute_tool()` instead of wrestling with service-specific SDKs and authentication flows. For AI agents: discover tools via MCP, learn their schemas automatically, and write simple execution code.

## Features

- **Skip SDK Hell**: No Gmail SDK, no LinkedIn API wrappers, no OAuth configuration code
- **One Client for Everything**: Access Gmail, Linear, Neon, Slack - same simple pattern
- **MCP Gateway**: Unified authentication for all connected MCP servers
- **Built-in Retry Logic**: Exponential backoff for failed requests
- **Comprehensive Error Handling**: Specific exception types for different error scenarios
- **Type Hints**: Better IDE support and code intelligence
- **Zero Dependencies**: Only requires `requests` library

## AI Agent-First Design

DataGen is built for AI coding assistants (Claude, Cursor, Copilot, etc.) to discover and use tools without hardcoded knowledge. When you ask an AI agent to "send an email via Gmail," here's what happens:

### The Agent Discovery Workflow

**Step 1: Agent discovers available tools**
```
Agent calls searchTools MCP tool:
Input: "send email"
Output: ['mcp_Gmail_gmail_send_email', 'mcp_Resend_send_email', ...]
```

**Step 2: Agent learns tool schema**
```
Agent calls getToolDetails MCP tool:
Input: "mcp_Gmail_gmail_send_email"
Output: {
  "name": "mcp_Gmail_gmail_send_email",
  "inputSchema": {
    "properties": {
      "to": {"type": "string"},
      "subject": {"type": "string"},
      "body": {"type": "string"}
    }
  }
}
```

**Step 3: Agent writes clean code**
```python
client.execute_tool(
    "mcp_Gmail_gmail_send_email",
    {
        "to": user.email,
        "subject": "Welcome!",
        "body": f"Hi {user.name}, thanks for signing up!"
    }
)
```

### Key Benefits for AI-Assisted Development

- **No hardcoded integrations**: Agents discover tools dynamically via MCP
- **Schema-aware code generation**: Agents understand tool parameters automatically
- **Human developers never write discovery code**: Agents handle tool search and learning
- **Clean execution layer**: Your codebase only contains `execute_tool()` calls
- **Swap services easily**: Add new MCP servers → agents discover them automatically

**Traditional approach:** Agent needs hardcoded knowledge of Gmail SDK, OAuth flows, API structure
**DataGen approach:** Agent uses `searchTools` and `getToolDetails` to learn on-demand

## Why DataGen? Built for AI Agents

DataGen is designed for AI-assisted development. AI coding assistants use DataGen's MCP server to discover and understand tools automatically, without hardcoded integration knowledge. This means agents can write correct code for services they've never seen before.

### The Problem: Authentication Hell & SDK Complexity

Building data-rich applications traditionally means:
- **OAuth Nightmares**: Setting up OAuth flows, managing tokens, handling refreshes for every service
- **SDK Sprawl**: Installing and learning different SDKs for Gmail, Linear, Neon, Slack, etc.
- **Integration Boilerplate**: Pages of authentication and configuration code cluttering your codebase

### The Solution: MCP Gateway with Unified Auth

DataGen acts as an MCP Gateway that handles authentication for ALL connected MCP servers. Connect Gmail, Linear, Neon, or any MCP server once through DataGen's UI, and all their tools become available through one authenticated client.

**Traditional Way** (what you avoid):
```python
# Without DataGen - lots of integration code
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import psycopg2

# Gmail setup
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
gmail_service = build('gmail', 'v1', credentials=creds)
message = MIMEText('email body')
# ... 20+ more lines of Gmail API code

# Database setup
conn = psycopg2.connect(
    host="your-host",
    database="your-db",
    user="your-user",
    password="your-password"
)
# ... more connection management code
```

**DataGen Way** (what you write):
```python
# With DataGen - just execution
from datagen_sdk import DatagenClient

client = DatagenClient()

# Send email - that's all the code you need
client.execute_tool("mcp_Gmail_gmail_send_email", {
    "to": "user@example.com",
    "subject": "Welcome!",
    "body": "Thanks for signing up"
})

# Query database - same simple pattern
contacts = client.execute_tool("mcp_Neon_run_sql", {
    "params": {
        "sql": "SELECT * FROM users WHERE active = true",
        "projectId": "your-project-id",
        "databaseName": "your-db"
    }
})
```

**Key Benefits:**
- ✅ No SDK installation per service
- ✅ No OAuth configuration in code
- ✅ Same pattern for any tool
- ✅ Swap services without rewriting integration code

## Installation

Install from PyPI:

```bash
pip install datagen-python-sdk
```

## Quick Start

### 1. Set up your API key

First, get your API key from: https://datagen.dev/account?tab=api

You can authenticate using the CLI, environment variables, or direct passing.

**Option A: CLI Login (Recommended)**
Run the following command in your terminal and follow the prompts:
```bash
datagen login
```
This will securely save your credentials so you don't need to manage environment variables manually.

**Option B: Environment variable**
```bash
export DATAGEN_API_KEY=your_api_key_here
```

**Option C: Pass directly to the client**
```python
from datagen_sdk import DatagenClient

client = DatagenClient(api_key="your_api_key_here")
```

### 2. Create a client and execute tools

```python
from datagen_sdk import DatagenClient

# Initialize the client (uses https://api.datagen.dev by default)
client = DatagenClient()

# Execute tools from any connected MCP server
# Example: List Linear projects
projects = client.execute_tool(
    "mcp_Linear_list_projects",
    {"limit": 20}
)
print(f"Found {len(projects[0]['content'])} projects")

# Example: Send email via Gmail - same client, different service
client.execute_tool(
    "mcp_Gmail_gmail_send_email",
    {
        "to": "team@example.com",
        "subject": "Project Update",
        "body": "We've successfully integrated DataGen!"
    }
)

# Example: Query Neon database - still the same client
users = client.execute_tool(
    "mcp_Neon_run_sql",
    {
        "params": {
            "sql": "SELECT * FROM users WHERE active = true LIMIT 10",
            "projectId": "your-project-id",
            "databaseName": "your-db"
        }
    }
)
```

Notice how all three services (Linear, Gmail, Neon) use the same client with the same pattern - that's the power of DataGen's MCP Gateway.

## Adding DataGen MCP Server

Connect DataGen as an MCP server to your AI coding assistant to enable tool discovery and execution directly from your editor.

### Prerequisites

Get your API key from: https://datagen.dev/account?tab=api

### Standard Configuration

All MCP clients use this base configuration for SSE (Server-Sent Events) transport:

```json
{
  "mcpServers": {
    "datagen": {
      "type": "sse",
      "url": "https://mcp.datagen.dev/mcp",
      "headers": {
        "x-api-key": "${DATAGEN_API_KEY}"
      }
    }
  }
}
```

**Environment Setup:**
```bash
export DATAGEN_API_KEY=your_api_key_here
```

The `${DATAGEN_API_KEY}` syntax allows the client to read from your environment variable securely.

### Client-Specific Setup

<details>
 <summary>Claude Desktop</summary>

**Config File Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the standard configuration above to your config file, then restart Claude Desktop.

</details>

<details>
 <summary>Claude Code</summary>

Use the CLI command with HTTP transport:
```bash
claude mcp add --transport http datagen https://mcp.datagen.dev/mcp --header "x-api-key: YOUR_API_KEY"
```

Or use environment variable:
```bash
export DATAGEN_API_KEY=your_api_key_here
claude mcp add --transport http datagen https://mcp.datagen.dev/mcp --header "x-api-key: ${DATAGEN_API_KEY}"
```

Verify with:
```bash
claude mcp list
```

</details>

<details>
 <summary>Cline (VS Code Extension)</summary>

1. Open VS Code Settings
2. Search for "Cline MCP"
3. Click "Edit in settings.json"
4. Add the standard configuration above
5. Restart VS Code

</details>

<details>
 <summary>Cursor</summary>

**One-Click Install:**

Click this button to install DataGen MCP in Cursor:

```
cursor://anysphere.cursor-deeplink/mcp/install?name=datagen&config=eyJ0eXBlIjoic3NlIiwidXJsIjoiaHR0cHM6Ly9tY3AuZGF0YWdlbi5kZXYvbWNwIiwiYXV0aCI6Im9hdXRoIn0%3D
```

Copy and paste the URL above into your browser's address bar, or click [here](cursor://anysphere.cursor-deeplink/mcp/install?name=datagen&config=eyJ0eXBlIjoic3NlIiwidXJsIjoiaHR0cHM6Ly9tY3AuZGF0YWdlbi5kZXYvbWNwIiwiYXV0aCI6Im9hdXRoIn0%3D) if your browser supports custom protocol handlers.

**Manual Setup:**

1. Open Settings (Cmd/Ctrl + ,)
2. Navigate to **Settings → MCP → New MCP Server**
3. Enter the configuration:
   - **Name**: `datagen`
   - **Type**: `sse`
   - **URL**: `https://mcp.datagen.dev/mcp`
   - **Auth**: `oauth`
4. Save and restart Cursor

Cursor will handle OAuth authentication automatically when you first use DataGen tools.

</details>

<details>
 <summary>VS Code Copilot</summary>

**Config File Location:** `~/.vscode/mcp_config.json` (or workspace `.vscode/mcp_config.json`)

Add the standard configuration, then reload VS Code.

</details>

<details>
 <summary>JetBrains AI Assistant (IntelliJ, PyCharm, etc.)</summary>

1. Open **Settings → Tools → AI Assistant**
2. Navigate to **Model Context Protocol (MCP)**
3. Click **Add**
4. Enter the standard configuration
5. Apply and restart the IDE

</details>

<details>
 <summary>Gemini CLI</summary>

**Config File Location:** `~/.gemini/settings.json`

Add this configuration for HTTP Streaming:

```json
{
  "mcpServers": {
    "datagen": {
      "httpUrl": "https://mcp.datagen.dev/mcp",
      "headers": {
        "x-api-key": "$DATAGEN_API_KEY"
      },
      "timeout": 5000
    }
  }
}
```

Then set your environment variable:
```bash
export DATAGEN_API_KEY=your_api_key_here
```

Note: Gemini CLI uses `$VAR_NAME` syntax for environment variables in headers.

</details>

<details>
 <summary>Codex (OpenAI)</summary>

**Config File Location:** `~/.codex/config.toml`

Add this configuration for Streamable HTTP:

```toml
[mcp_servers.datagen]
url = "https://mcp.datagen.dev/mcp"
env_http_headers = { "x-api-key" = "DATAGEN_API_KEY" }
```

Then set your environment variable:
```bash
export DATAGEN_API_KEY=your_api_key_here
```

Or use static headers directly:
```toml
[mcp_servers.datagen]
url = "https://mcp.datagen.dev/mcp"
http_headers = { "x-api-key" = "your_api_key_here" }
```

</details>

### Verifying the Connection

Once configured, your AI assistant can discover and execute DataGen tools automatically. The AI uses two key MCP tools:

1. **`searchTools`**: Discovers available tools by searching connected MCP servers
2. **`getToolDetails`**: Retrieves tool schemas to understand parameters and usage

Try asking your AI assistant:
- "What tools are available through DataGen?" → AI calls `searchTools` to discover
- "Show me how to send an email via Gmail" → AI calls `getToolDetails` to learn schema
- "List my Linear projects using DataGen" → AI writes `execute_tool()` code
- "Send an email via Gmail through DataGen" → AI executes the discovered tool

**How it works behind the scenes:**
1. Your AI assistant calls DataGen's `searchTools` MCP tool to find relevant tools
2. AI calls `getToolDetails` to understand the tool's input schema
3. AI writes clean Python code using `client.execute_tool()` with correct parameters
4. Your codebase stays clean - no Gmail SDK imports, no OAuth flows, no API wrappers

## API Reference

### DatagenClient

The main client class for interacting with the Datagen API.

#### Constructor

```python
DatagenClient(
    api_key: Optional[str] = None,
    base_url: str = "https://api.datagen.dev",
    timeout: int = 30,
    retries: int = 0,
    backoff_seconds: float = 0.5
)
```

**Parameters:**
- `api_key` (str, optional): Your Datagen API key. If not provided, reads from `DATAGEN_API_KEY` environment variable.
- `base_url` (str, optional): The base URL of your Datagen API instance. Default: `https://api.datagen.dev`
- `timeout` (int, optional): Request timeout in seconds. Default: `30`
- `retries` (int, optional): Number of retry attempts for failed requests. Default: `0`
- `backoff_seconds` (float, optional): Base backoff time for exponential retry. Default: `0.5`

**Raises:**
- `DatagenAuthError`: If API key is not provided and `DATAGEN_API_KEY` is not set

#### Methods

##### execute_tool

Execute a DataGen tool by its alias name.

```python
execute_tool(
    tool_alias_name: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Any
```

**Parameters:**
- `tool_alias_name` (str): The alias name of the tool to execute (e.g., `"mcp_Linear_list_projects"`)
- `parameters` (dict, optional): Parameters to pass to the tool. Default: `{}`

**Returns:**
- The result data from the tool execution

**Raises:**
- `DatagenAuthError`: Authentication failed (401/403)
- `DatagenHttpError`: HTTP-level errors (network issues, 4xx/5xx status codes)
- `DatagenToolError`: Tool executed but reported a failure

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from datagen_sdk import (
    DatagenClient,
    DatagenError,          # Base exception
    DatagenAuthError,      # Authentication errors
    DatagenHttpError,      # HTTP-level errors
    DatagenToolError       # Tool execution errors
)

try:
    client = DatagenClient()
    result = client.execute_tool("my_tool", {"param": "value"})
except DatagenAuthError as e:
    print(f"Authentication failed: {e}")
except DatagenToolError as e:
    print(f"Tool execution failed: {e}")
except DatagenHttpError as e:
    print(f"HTTP error: {e}")
except DatagenError as e:
    print(f"General error: {e}")
```

## Configuration

### Using Environment Variables

```bash
export DATAGEN_API_KEY=your_api_key_here
```

### Client Configuration Examples

**Basic usage:**
```python
client = DatagenClient()
```

**Custom base URL:**
```python
client = DatagenClient(base_url="https://api.datagen.dev")
```

**With retry logic:**
```python
client = DatagenClient(
    retries=3,              # Retry up to 3 times
    backoff_seconds=1.0     # Start with 1 second, doubles each retry
)
```

**Custom timeout:**
```python
client = DatagenClient(timeout=60)  # 60 second timeout
```

## Building with DataGen

Here's a real-world example of a CRM dashboard built with DataGen. Notice how clean the code is - no database connection setup, no OAuth flows, just execution.

### CRM Dashboard with Streamlit

```python
import streamlit as st
from datagen_sdk import DatagenClient

st.title("CRM Dashboard")
client = DatagenClient()

# Get high-priority contacts from your database
if st.button("Load High-Priority Contacts"):
    contacts = client.execute_tool(
        "mcp_Neon_run_sql",
        {
            "params": {
                "sql": "SELECT * FROM crm WHERE priority_score > 75 ORDER BY priority_score DESC",
                "projectId": "your-project-id",
                "databaseName": "your-db"
            }
        }
    )

    # Display contacts in a table
    st.dataframe(contacts)

# Send follow-up emails
st.subheader("Send Follow-up Email")
selected_email = st.selectbox("Select contact", ["user@example.com"])  # Populate from contacts
message = st.text_area("Compose email")

if st.button("Send Email"):
    client.execute_tool(
        "mcp_Gmail_gmail_send_email",
        {
            "to": selected_email,
            "subject": "Follow-up",
            "body": message
        }
    )
    st.success("Email sent!")

# Track project status
if st.button("Check Linear Projects"):
    projects = client.execute_tool(
        "mcp_Linear_list_projects",
        {"limit": 10}
    )

    for proj in projects[0]["content"]:
        st.write(f"📊 {proj.get('name')} - {proj.get('state')}")
```

### Key Benefits of This Approach

- ✅ **No database connection setup needed** - No `psycopg2.connect()` or connection string management
- ✅ **No Gmail OAuth flow required** - No Google API client setup or token handling
- ✅ **No Linear SDK installation** - No API wrapper imports or configuration
- ✅ **Same code pattern for any tool** - `execute_tool()` works for all services
- ✅ **Easy to swap services** - Change Neon → Supabase without rewriting integration code

### How AI Agents Build This

When an AI assistant helps you build this dashboard:
1. You describe the requirement: "Build a CRM dashboard that queries Neon and sends Gmail emails"
2. AI calls `searchTools` MCP tool to find "mcp_Neon_run_sql" and "mcp_Gmail_gmail_send_email"
3. AI calls `getToolDetails` to learn the exact parameter schemas
4. AI writes the clean code above - no Gmail SDK research, no Neon driver docs, no OAuth configuration

**Result:** The AI writes correct integration code without needing to be trained on every API. DataGen's MCP tools let agents discover and learn on-demand.

### Adaptation for Your Use Case

This pattern works for any scenario:
- **E-commerce analytics**: Combine Shopify data with email notifications
- **Customer support dashboards**: Integrate Zendesk with Slack and databases
- **Data pipelines**: Connect multiple data sources with simple execution calls
- **Marketing automation**: Link CRM data with email and social media tools

Just swap in different tools and queries for your specific needs - the pattern stays the same.

## Examples

### List Linear Projects

```python
from datagen_sdk import DatagenClient

# Initialize with production API (default)
client = DatagenClient()

# Fetch projects from Linear via DataGen
projects = client.execute_tool("mcp_Linear_list_projects", {"limit": 20})

print(f"Projects returned: {len(projects[0]['content']) if projects else 0}")
for proj in projects[0]["content"]:
    print(f"- {proj.get('name')} (id: {proj.get('id')})")
```

### List Linear Issues

```python
from datagen_sdk import DatagenClient

client = DatagenClient()

# Fetch recent issues from Linear
issues = client.execute_tool(
    "mcp_Linear_list_issues",
    {
        "limit": 10,
        "order_by": "createdAt",
        "order_direction": "DESC",
    }
)

issue_block = issues[0] if issues else []
print(f"Issues returned: {len(issue_block)}")
for issue in issue_block:
    ident = issue.get("identifier", "?")
    title = issue.get("title", "(no title)")
    print(f"- {ident}: {title}")
```

### Cross-Service Workflow: Database + Email

Combine multiple services in one workflow - query your database and send notification emails:

```python
from datagen_sdk import DatagenClient

client = DatagenClient()

# Step 1: Query Neon database for new signups
new_users = client.execute_tool(
    "mcp_Neon_run_sql",
    {
        "params": {
            "sql": "SELECT email, name FROM users WHERE created_at > NOW() - INTERVAL '1 day'",
            "projectId": "your-project-id",
            "databaseName": "your-db"
        }
    }
)

# Step 2: Send welcome email to each new user via Gmail
for user in new_users:
    client.execute_tool(
        "mcp_Gmail_gmail_send_email",
        {
            "to": user["email"],
            "subject": "Welcome to our platform!",
            "body": f"Hi {user['name']}, thanks for signing up!"
        }
    )
    print(f"✓ Welcome email sent to {user['email']}")

print(f"Processed {len(new_users)} new users")
```

Notice how you're using both Neon and Gmail with the same client - no separate SDKs, no separate auth flows.

### Error Handling with Retries

```python
from datagen_sdk import DatagenClient, DatagenHttpError, DatagenToolError

client = DatagenClient(
    retries=3,
    backoff_seconds=0.5
)

try:
    result = client.execute_tool("mcp_Linear_list_projects", {"limit": 10})
    print("Success:", result)
except DatagenToolError as e:
    print(f"Tool execution failed: {e}")
except DatagenHttpError as e:
    print(f"HTTP error after retries: {e}")
```

## Development

### Running Examples

See the `examples/` directory for complete examples:

```bash
# Set your API key
export DATAGEN_API_KEY=your_api_key_here

# Run examples
python examples/list_projects.py
python examples/list_issues.py
```

### Requirements

- Python >= 3.10
- requests >= 2.31.0

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- Homepage: https://datagen.dev
- Source Code: https://github.com/datagen/datagen-python-sdk
- Issue Tracker: https://github.com/datagen/datagen-python-sdk/issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
