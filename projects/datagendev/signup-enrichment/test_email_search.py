import os
import json
from datagen_sdk import DatagenClient

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

email_address = "nocodecanada@gmail.com"

print(f"Searching for emails to/from: {email_address}")
print(f"Query: to:{email_address} OR from:{email_address}")
print("-" * 50)

try:
    search_results = client.execute_tool(
        "mcp_Gmail_gmail_search_emails",
        {"query": f"to:{email_address} OR from:{email_address}", "max_results": 10}
    )

    print(f"Result type: {type(search_results)}")
    print(f"Result: {json.dumps(search_results, indent=2)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
