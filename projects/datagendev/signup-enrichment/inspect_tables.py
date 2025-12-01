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

client = DatagenClient()

def get_columns(table):
    print(f"--- Columns for {table} ---")
    try:
        sql = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}';"
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
        print(result)
    except Exception as e:
        print(f"Error: {e}")

def run():
    get_columns('user_profile')
    get_columns('fastapi_user')

if __name__ == "__main__":
    run()
