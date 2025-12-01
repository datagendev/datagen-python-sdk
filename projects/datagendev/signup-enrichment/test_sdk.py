import os
import sys
from datagen_sdk import DatagenClient, DatagenError

# Simple .env loader
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

api_key = os.getenv('DATAGEN_API_KEY')
if not api_key:
    print("Error: DATAGEN_API_KEY not set in environment or .env file")
    sys.exit(1)

print(f"API Key found: {api_key[:4]}...{api_key[-4:]}")

client = DatagenClient()

try:
    print("\nTesting connection by calling 'mcp_Exa_web_search_exa'...")
    # Using a specific tool found via searchTools
    result = client.execute_tool("mcp_Exa_web_search_exa", {"query": "Datagen SDK test"})
    
    print("✅ Success! SDK is working.")
    print(f"Result: {result}")

except DatagenError as e:
    print(f"❌ SDK Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
