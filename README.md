# datagen-python-sdk

Built for AI coding assistants and developers. DataGen's MCP server lets AI agents discover and understand how to use any integrated tool - Gmail, Linear, Neon, Slack - without hardcoded integration knowledge. Agents use `searchTools` and `getToolDetails` to self-guide, writing clean `execute_tool()` code that skips SDK hell, OAuth nightmares, and API integration boilerplate.

For human developers: write `client.execute_tool()` instead of wrestling with service-specific SDKs and authentication flows. For AI agents: discover tools via MCP, learn their schemas automatically, and write simple execution code.

## Key Features

- **MCP Tools as Code**: Turn any MCP tool into executable code - no SDK installation, no API wrappers
- **Skip Integration Hell**: No Gmail SDK, no LinkedIn API wrappers, no OAuth configuration code
- **One Client for Everything**: Access Gmail, Linear, Neon, Slack - same simple pattern
- **MCP Gateway**: Unified authentication for all connected MCP servers. You don't need to handle auth during the code generation process.
- **MCP Middleware**: Built-in retry logic and rate-limit handling across all your API calls 

![DataGen Workflow Diagram](datagen_workflow_flowchart.png)
*DataGen's MCP Gateway architecture - one client handles auth and routing to Gmail, Neon, LinkedIn. Write simple execute_tool() calls, skip all SDK setup*

## AI Agent-First Design

DataGen is built for AI coding assistants (Claude, Cursor, Copilot, etc.) to discover and use tools without hardcoded knowledge.

**Prerequisites**: Connect MCP servers (Gmail, Neon, Linear, etc.) in the [DataGen Dashboard](https://datagen.dev/signalgen/mcp-servers). Once connected, AI agents can discover and use all their tools automatically. Either in code or context

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

### How DataGen Transforms AI-Assisted Development

DataGen's MCP + SDK combo dramatically improves agent-assisted coding by eliminating the gap between "what you want" and "working code."

**🎯 The AI-Assisted Experience:**

Just tell your AI agent: *"Send an email to new signups from the database"*

The agent instantly:
1. **Self-discovers tools** via MCP (`searchTools` finds `mcp_Neon_run_sql`, `mcp_Gmail_gmail_send_email`)
2. **Learns schemas** via MCP (`getToolDetails` gets exact parameters needed)
3. **Writes clean code** using the SDK (`client.execute_tool()` calls)
4. **Executes immediately** - no OAuth, no API key setup, no SDK installation, no API docs hunting

**Traditional AI-Assisted Development Problems:**
- ❌ Agent generates Gmail SDK boilerplate → you fix OAuth errors for 30 minutes
- ❌ Agent hallucinates API parameters → you debug incorrect field names
- ❌ Agent imports wrong packages → you install 5 SDKs and resolve conflicts
- ❌ You iterate 10+ times to get working integration code

**DataGen AI-Assisted Development Reality:**
- ✅ Agent self-discovers real tools and schemas → generates correct code first try
- ✅ Zero OAuth & API key configuration → authentication handled by MCP Gateway
- ✅ One SDK for everything → no package conflicts or version hell
- ✅ You iterate on business logic, not integration plumbing

**The Result:** Go from idea → working integration in one prompt instead of one hour.

## Installation

Install from PyPI:

```bash
pip install datagen-python-sdk
```

## Quick Start

### 1. Add DataGen MCP Server to Your AI Coding Assistant

Connect DataGen as an MCP server to your AI coding assistant to enable tool discovery and execution directly from your editor.

**Prerequisites:** Get your API key [here](https://datagen.dev/account?tab=api)

**Set up your API key in environments**

```bash
export DATAGEN_API_KEY=your_api_key_here
```

**Standard Configuration:**

```json
{
  "mcpServers": {
    "datagen": {
      "url": "https://mcp.datagen.dev/mcp",
      "headers": {
        "x-api-key": "${DATAGEN_API_KEY}"
      }
    }
  }
}
```

**Client-Specific Setup:**

<details>
 <summary>Cursor</summary>

**One-Click Install:**

[Click to add](cursor://anysphere.cursor-deeplink/mcp/install?name=datagen&config=eyJ0eXBlIjoic3NlIiwidXJsIjoiaHR0cHM6Ly9tY3AuZGF0YWdlbi5kZXYvbWNwIiwiYXV0aCI6Im9hdXRoIn0%3D)

Cursor will handle OAuth authentication automatically when you first use DataGen tools.

</details>

<details>
 <summary>Claude Code</summary>

Use the CLI command with HTTP transport:
```bash
claude mcp add --transport http datagen https://mcp.datagen.dev/mcp --header "x-api-key: YOUR_API_KEY"
```

Verify with:
```bash
claude mcp list
```

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

**Verifying the Connection:**

Once configured, try asking your AI assistant:
- "What tools are available through DataGen?"
- "List my Linear projects using DataGen"
- "Send an email via Gmail through DataGen"

Your AI will use `searchTools` and `getToolDetails` MCP tools to discover and execute DataGen tools automatically.

### 2. Connect MCP servers in DataGen

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

### 3. Start Building

**Option A: AI-Assisted Way (Recommended)**

Just ask your AI coding assistant (Claude Code, Cursor, etc.) to build with DataGen:

*"Build a script that sends an email to new signups from the database using DataGen SDK"*

Your AI will:
- Self-discover the right tools (`searchTools` finds `mcp_Neon_run_sql`, `mcp_Gmail_gmail_send_email`)
- Learn the schemas (`getToolDetails` gets parameters)
- Write clean code using `client.execute_tool()`
- Generate working code in one shot

**Option B: Traditional Developer Way**

Write code directly using the DataGen SDK:

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
```

## Examples

### Example 1: Send Welcome Emails to New Signups

Query your database and send emails - no database drivers, no OAuth setup:

```python
from datagen_sdk import DatagenClient

client = DatagenClient()

# Query Neon database for new signups
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

# Send welcome email via Gmail
for user in new_users:
    client.execute_tool(
        "mcp_Gmail_gmail_send_email",
        {
            "to": user["email"],
            "subject": "Welcome!",
            "body": f"Hi {user['name']}, thanks for signing up!"
        }
    )
```

### Example 2: CRM Dashboard with Streamlit

Build a full dashboard in minutes - same client, multiple services:

```python
import streamlit as st
from datagen_sdk import DatagenClient

st.title("CRM Dashboard")
client = DatagenClient()

# Load high-priority contacts from database
if st.button("Load Contacts"):
    contacts = client.execute_tool("mcp_Neon_run_sql", {
        "params": {
            "sql": "SELECT * FROM crm WHERE priority_score > 75",
            "projectId": "your-project-id",
            "databaseName": "your-db"
        }
    })
    st.dataframe(contacts)

# Send follow-up emails
selected_email = st.selectbox("Select contact", ["user@example.com"])
if st.button("Send Follow-up"):
    client.execute_tool("mcp_Gmail_gmail_send_email", {
        "to": selected_email,
        "subject": "Follow-up",
        "body": st.text_area("Message")
    })
    st.success("Sent!")
```

**Key Benefits:** No database connection setup, no Gmail OAuth, no SDK installation. Same `execute_tool()` pattern for all services.


### Requirements

- Python >= 3.10
- requests >= 2.31.0

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- Homepage: https://datagen.dev
- Source Code: https://github.com/datagen/datagen-python-sdk
- Issue Tracker: https://github.com/datagen/datagen-python-sdk/issues

