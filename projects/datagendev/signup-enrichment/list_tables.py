import os
import sys
from datagen_sdk import DatagenClient

# Load environment variables
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

if not os.getenv('DATAGEN_API_KEY'):
    print("Error: DATAGEN_API_KEY not set")
    sys.exit(1)

client = DatagenClient()

def run():
    print("Listing tables in public schema...")
    try:
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        result = client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": sql,
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )
        print("Tables found:", result)
        
    except Exception as e:
        print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    run()
