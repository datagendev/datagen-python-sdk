import os
import json
from datagen_sdk import DatagenClient

# Simplified env loading
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

try:
    print("Executing tool...")
    results = client.execute_tool("mcp_Gmail_gmail_search_emails", {"query": "newer_than:1y", "max_results": 2})
    
    print(f"Type: {type(results)}")
    
    if isinstance(results, list):
        print(f"List length: {len(results)}")
        if len(results) > 0:
            print(f"First item type: {type(results[0])}")
            print("First item content:")
            print(results[0])
    else:
        print("Content:")
        print(results)

except Exception as e:
    print(f"Error: {e}")
