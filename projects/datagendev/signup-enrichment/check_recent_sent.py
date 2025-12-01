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

print("Check recent sent emails (today)")
print("-" * 50)
try:
    results = client.execute_tool(
        "mcp_Gmail_gmail_search_emails",
        {"query": "in:sent newer_than:1d", "max_results": 20}
    )
    print(f"Found {results[0]['count']} emails sent today")
    if results[0]['count'] > 0:
        for email in results[0]['emails']:
            print(f"\n  Subject: {email['subject']}")
            print(f"  To: {email.get('to', 'N/A')}")
            print(f"  Date: {email['date']}")
            print(f"  Snippet: {email['snippet'][:100]}...")
    else:
        print("No emails sent today found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\nCheck recent emails in general")
print("-" * 50)
try:
    results = client.execute_tool(
        "mcp_Gmail_gmail_list_recent_emails",
        {"max_results": 10}
    )
    print(f"Recent emails: {json.dumps(results, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
