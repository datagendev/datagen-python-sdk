# Datagen Python SDK (local tools API)

Minimal client to call the Datagen Wasp tools API (`/api/tools/execute`) from Python.

## Install

```bash
pip install requests
# or install this folder directly:
# pip install .
```

## Usage

Set your API key (same one you use for the Wasp tools API):

```bash
export DATAGEN_API_KEY="<your-key>"
```

Call a tool:

```python
from datagen_sdk import DatagenClient

client = DatagenClient(base_url="http://localhost:3001")
result = client.execute_tool(
    "mcp_Linear_list_projects",
    {"limit": 10}
)
print(result)
```

## Examples

Run the included examples (ensure DATAGEN_API_KEY is set):

```bash
python examples/list_projects.py
python examples/list_issues.py
```

## API

- `DatagenClient(api_key=None, base_url="http://localhost:3001", timeout=30, retries=0, backoff_seconds=0.5)`
- `execute_tool(tool_alias_name: str, parameters: dict = None) -> Any`

Errors raise one of:
- `DatagenAuthError` (401/403)
- `DatagenToolError` (tool returned `success=false`)
- `DatagenHttpError` (other HTTP issues)

## Notes
- Uses header `X-API-Key` (the Wasp tools API now only accepts this header).
- Defaults to local dev port 3001; adjust `base_url` if your gateway differs.
