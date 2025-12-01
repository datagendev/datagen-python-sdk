import os
from datagen_sdk import DatagenClient
import json

# Load env
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

client = DatagenClient()

# Test 1: Check SQL result structure
print("Test 1: SQL query result structure")
print("-" * 50)
sql = "SELECT emails_sent_count, emails_received_count, last_email_received_at FROM crm WHERE id = 1"
result = client.execute_tool("mcp_Neon_run_sql", {
    "params": {
        "sql": sql,
        "projectId": "rough-base-02149126",
        "databaseName": "datagen"
    }
})
print(f"Type: {type(result)}")
print(f"Result: {json.dumps(result, indent=2, default=str)}")

if isinstance(result, list) and len(result) > 0:
    print(f"\nFirst element type: {type(result[0])}")
    print(f"First element: {result[0]}")

# Test 2: Check Gmail search result structure
print("\n\nTest 2: Gmail search result structure")
print("-" * 50)
email = "nocodecanada@gmail.com"
search_results = client.execute_tool(
    "mcp_Gmail_gmail_search_emails",
    {"query": f"to:{email} OR from:{email}", "max_results": 10}
)
print(f"Type: {type(search_results)}")
print(f"Result: {json.dumps(search_results, indent=2, default=str)}")
