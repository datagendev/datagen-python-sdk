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

DataGen is built for AI coding assistants (Claude, Cursor, Copilot, etc.) to discover and use tools without hardcoded knowledge.

**Prerequisites**: First, connect MCP servers (Gmail, Neon, Linear, etc.) in the DataGen UI at https://datagen.dev. Once connected, AI agents can discover and use all their tools automatically.

When you ask an AI agent to "send an email via Gmail," here's what happens:

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

## Why DataGen?

Traditional development means OAuth nightmares, SDK sprawl, and pages of integration boilerplate. DataGen's MCP Gateway handles authentication for ALL connected services - connect once at https://datagen.dev, never touch credentials in code.

**Traditional Way:**
```python
# 20+ lines of OAuth, credentials, API setup per service
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
gmail_service = build('gmail', 'v1', credentials=creds)
# ... more boilerplate ...
```

**DataGen Way:**
```python
client = DatagenClient()
client.execute_tool("mcp_Gmail_gmail_send_email", {...})
client.execute_tool("mcp_Neon_run_sql", {...})
```

**Benefits:**
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

### 1. Connect MCP servers in DataGen UI

Before you can use tools like Gmail or Neon, you need to connect their MCP servers through the DataGen dashboard:

1. Go to https://datagen.dev
2. Navigate to **MCP Servers** section
3. Click **Add MCP Server**
4. Choose from available MCP servers:
   - **Gmail MCP**: Connect your Gmail account via OAuth
   - **Neon MCP**: Connect your Neon PostgreSQL database
   - **Linear MCP**: Connect your Linear workspace
   - **Slack MCP**: Connect your Slack workspace
   - And many more...
5. Complete the authentication flow for each service

**Once connected**, all tools from these MCP servers become available through the DataGen SDK. You never touch credentials in your code - DataGen's MCP Gateway handles all authentication.

### 2. Set up your API key

Get your API key from: https://datagen.dev/account?tab=api

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

### 3. Create a client and execute tools

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

Once configured, try asking your AI assistant:
- "What tools are available through DataGen?"
- "List my Linear projects using DataGen"
- "Send an email via Gmail through DataGen"

Your AI will use `searchTools` and `getToolDetails` MCP tools to discover and execute DataGen tools automatically.

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

# Query database
if st.button("Load Contacts"):
    contacts = client.execute_tool("mcp_Neon_run_sql", {
        "params": {
            "sql": "SELECT * FROM crm WHERE priority_score > 75",
            "projectId": "your-project-id",
            "databaseName": "your-db"
        }
    })
    st.dataframe(contacts)

# Send emails
selected_email = st.selectbox("Select contact", ["user@example.com"])
message = st.text_area("Message")

if st.button("Send"):
    client.execute_tool("mcp_Gmail_gmail_send_email", {
        "to": selected_email,
        "subject": "Follow-up",
        "body": message
    })
    st.success("Sent!")
```

### Key Benefits of This Approach

- ✅ **No database connection setup needed** - No `psycopg2.connect()` or connection string management
- ✅ **No Gmail OAuth flow required** - No Google API client setup or token handling
- ✅ **No Linear SDK installation** - No API wrapper imports or configuration
- ✅ **Same code pattern for any tool** - `execute_tool()` works for all services
- ✅ **Easy to swap services** - Change Neon → Supabase without rewriting integration code

This pattern works for any scenario - e-commerce analytics, customer support dashboards, data pipelines, marketing automation. Just swap in different tools for your needs.

## Examples

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
