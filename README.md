# datagen-python-sdk

A minimal Python SDK for interacting with DataGen MCP (Model Context Protocol) APIs. This SDK provides a simple, type-safe interface to execute tools via the Datagen API with built-in authentication, retry logic, and comprehensive error handling.

## Features

- Simple, intuitive API for executing DataGen tools
- Automatic authentication via API key
- Built-in retry logic with exponential backoff
- Comprehensive error handling with specific exception types
- Type hints for better IDE support
- Zero dependencies except `requests`

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

# Execute a tool
result = client.execute_tool(
    "mcp_Linear_list_projects",
    {"limit": 20}
)

print(f"Found {len(result[0]['content'])} projects")
```

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

## Examples

### List Projects

```python
from datagen_sdk import DatagenClient

client = DatagenClient(base_url="http://localhost:3001")
projects = client.execute_tool("mcp_Linear_list_projects", {"limit": 20})

print(f"Projects returned: {len(projects[0]['content']) if projects else 0}")
for proj in projects[0]["content"]:
    print(f"- {proj.get('name')} (id: {proj.get('id')})")
```

### List Issues

```python
from datagen_sdk import DatagenClient

client = DatagenClient(base_url="http://localhost:3001")
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

### Error Handling with Retries

```python
from datagen_sdk import DatagenClient, DatagenHttpError

client = DatagenClient(
    base_url="http://localhost:3001",
    retries=3,
    backoff_seconds=0.5
)

try:
    result = client.execute_tool("my_tool", {"param": "value"})
    print("Success:", result)
except DatagenHttpError as e:
    print(f"Failed after retries: {e}")
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
