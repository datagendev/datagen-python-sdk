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

print("Testing email send to yusheng.kuo@datagen.dev")
print("-" * 50)

try:
    result = client.execute_tool(
        "mcp_Gmail_gmail_send_email",
        {
            "to": "yusheng.kuo@datagen.dev",
            "subject": "Test Email - Gmail Tool Fix",
            "body": "This is a test email to verify the Gmail send tool is working correctly after fixing the parameter validation issue.\n\nThe 'to' field is now correctly passed as a string instead of a list."
        }
    )

    print("Success!")
    print(json.dumps(result, indent=2))

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
