import os
import re
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

print("Running migration: 001_add_email_tracking.sql")
print("-" * 50)

# Read migration file
with open('migrations/001_add_email_tracking.sql', 'r') as f:
    sql_content = f.read()

# Remove comments and split by semicolon
lines = []
for line in sql_content.split('\n'):
    line = line.strip()
    if line and not line.startswith('--'):
        lines.append(line)

sql_text = ' '.join(lines)

# Split into individual statements
statements = [s.strip() for s in sql_text.split(';') if s.strip() and s.strip().upper() not in ('BEGIN', 'COMMIT')]

print(f"Found {len(statements)} SQL statements to execute\n")

# Execute each statement
success_count = 0
for i, stmt in enumerate(statements, 1):
    if not stmt:
        continue

    print(f"Statement {i}/{len(statements)}:")
    print(f"  {stmt[:80]}...")

    try:
        result = client.execute_tool("mcp_Neon_run_sql", {
            "params": {
                "sql": stmt,
                "projectId": "rough-base-02149126",
                "databaseName": "datagen"
            }
        })
        print(f"  ✓ Success")
        success_count += 1
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print(f"  ⚠ Already exists (skipping)")
            success_count += 1
        else:
            print(f"  ✗ Failed: {e}")

print(f"\n{'-' * 50}")
print(f"Migration completed: {success_count}/{len(statements)} statements successful")

# Verify columns were added
print("\nVerifying new columns...")
verify_sql = """
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'crm'
  AND column_name IN ('email_status', 'last_email_sent_at', 'last_email_received_at',
                      'email_tracking_last_synced_at', 'emails_sent_count',
                      'emails_received_count', 'needs_followup')
ORDER BY column_name
"""

try:
    verify_result = client.execute_tool("mcp_Neon_run_sql", {
        "params": {
            "sql": verify_sql,
            "projectId": "rough-base-02149126",
            "databaseName": "datagen"
        }
    })

    print("\nEmail tracking columns in CRM table:")
    if isinstance(verify_result, list) and len(verify_result) > 0:
        for row in verify_result:
            if isinstance(row, dict):
                print(f"  - {row.get('column_name')}: {row.get('data_type')} (default: {row.get('column_default')})")
    else:
        print(verify_result)

except Exception as e:
    print(f"Verification failed: {e}")
