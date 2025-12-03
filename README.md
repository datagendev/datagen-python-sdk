# datagen-python-sdk

A minimal Python SDK for interacting with DataGen MCP (Model Context Protocol) APIs. Skip the SDK hell, OAuth nightmares, and API integration boilerplate - DataGen's MCP Gateway lets you access Gmail, Linear, Neon, and dozens of other services through one simple client with unified authentication.

Write `client.execute_tool()` instead of wrestling with service-specific SDKs, authentication flows, and API documentation. DataGen makes external services feel like native Python functions.

## Features

- **Skip SDK Hell**: No Gmail SDK, no LinkedIn API wrappers, no OAuth configuration code
- **One Client for Everything**: Access Gmail, Linear, Neon, Slack - same simple pattern
- **MCP Gateway**: Unified authentication for all connected MCP servers
- **Built-in Retry Logic**: Exponential backoff for failed requests
- **Comprehensive Error Handling**: Specific exception types for different error scenarios
- **Type Hints**: Better IDE support and code intelligence
- **Zero Dependencies**: Only requires `requests` library

## Why DataGen?

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

#### Claude Desktop

**Config File Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the standard configuration above to your config file, then restart Claude Desktop.

#### Claude Code

Use the CLI command:
```bash
claude mcp add --transport sse datagen https://mcp.datagen.dev/mcp --header "x-api-key: YOUR_API_KEY"
```

Or use environment variable:
```bash
export DATAGEN_API_KEY=your_api_key_here
claude mcp add --transport sse datagen https://mcp.datagen.dev/mcp --header "x-api-key: ${DATAGEN_API_KEY}"
```

Verify with:
```bash
claude mcp list
```

#### Cline (VS Code Extension)

1. Open VS Code Settings
2. Search for "Cline MCP"
3. Click "Edit in settings.json"
4. Add the standard configuration above
5. Restart VS Code

#### Cursor

1. Open Settings (Cmd/Ctrl + ,)
2. Navigate to **Settings → MCP → New MCP Server**
3. Enter the configuration:
   - **Name**: `datagen`
   - **Type**: `sse`
   - **URL**: `https://mcp.datagen.dev/mcp`
   - **Headers**: `{"x-api-key": "your_api_key_here"}`
4. Save and restart Cursor

#### VS Code Copilot

**Config File Location:** `~/.vscode/mcp_config.json` (or workspace `.vscode/mcp_config.json`)

Add the standard configuration, then reload VS Code.

#### JetBrains AI Assistant (IntelliJ, PyCharm, etc.)

1. Open **Settings → Tools → AI Assistant**
2. Navigate to **Model Context Protocol (MCP)**
3. Click **Add**
4. Enter the standard configuration
5. Apply and restart the IDE

#### Gemini CLI

**Project-wide installation:**
```bash
gemini mcp add datagen --type sse --url https://mcp.datagen.dev/mcp --header "x-api-key: ${DATAGEN_API_KEY}"
```

**Global installation:**
```bash
gemini mcp add -s user datagen --type sse --url https://mcp.datagen.dev/mcp --header "x-api-key: ${DATAGEN_API_KEY}"
```

### Verifying the Connection

Once configured, your AI assistant can discover and execute DataGen tools. Try asking:
- "What tools are available through DataGen?"
- "List my Linear projects using DataGen"
- "Send an email via Gmail through DataGen"

The AI will use DataGen's `searchTools` and `getToolDetails` MCP tools to discover available integrations and their schemas, then execute them via the Python SDK.

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
