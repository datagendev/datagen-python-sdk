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

print("Test 1: All emails to/from nocodecanada@gmail.com")
print("-" * 50)
try:
    results = client.execute_tool(
        "mcp_Gmail_gmail_search_emails",
        {"query": f"to:{email_address} OR from:{email_address}", "max_results": 20}
    )
    print(f"Count: {results[0]['count']}")
    for email in results[0]['emails']:
        print(f"  - {email['date']}: {email['subject']} (From: {email['from']})")
except Exception as e:
    print(f"Error: {e}")

print("\n")
print("Test 2: Sent emails to nocodecanada@gmail.com")
print("-" * 50)
try:
    results = client.execute_tool(
        "mcp_Gmail_gmail_search_emails",
        {"query": f"to:{email_address}", "max_results": 20}
    )
    print(f"Count: {results[0]['count']}")
    for email in results[0]['emails']:
        print(f"  - {email['date']}: {email['subject']} (From: {email['from']})")
except Exception as e:
    print(f"Error: {e}")

print("\n")
print("Test 3: Recent sent emails (in:sent)")
print("-" * 50)
try:
    results = client.execute_tool(
        "mcp_Gmail_gmail_search_emails",
        {"query": f"to:{email_address} in:sent", "max_results": 20}
    )
    print(f"Count: {results[0]['count']}")
    for email in results[0]['emails']:
        print(f"  - {email['date']}: {email['subject']} (From: {email['from']})")
except Exception as e:
    print(f"Error: {e}")
