import os
import sys
import json
import time
from datagen_sdk import DatagenClient

# Simple .env loader
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'" ) and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

api_key = os.getenv('DATAGEN_API_KEY')
if not api_key:
    print("Error: DATAGEN_API_KEY not set")
    sys.exit(1)

client = DatagenClient()

def infer_name_from_email(email):
    if not email or '@' not in email:
        return None, None
    user_part = email.split('@')[0]
    # Handle "first.last"
    if '.' in user_part:
        parts = user_part.split('.')
        if len(parts) >= 2:
            return parts[0].capitalize(), parts[1].capitalize()
    # Handle "firstlast" (harder, maybe just return user_part as first name)
    # Or "first_last"
    if '_' in user_part:
        parts = user_part.split('_')
        if len(parts) >= 2:
            return parts[0].capitalize(), parts[1].capitalize()
            
    return user_part.capitalize(), None

def run():
    print("Searching for LinkedIn tools...")
    try:
        # Search for tools via MCP directly (SDK doesn't have a direct search method exposed typically, 
        # but the doc says "searchTools" is an MCP server tool call via MCP protocol.
        # However, the SDK `execute_tool` calls the tool.
        # Let's try to call `mcp__Datagen__searchTools` if that's the internal name, or just `searchTools`.
        # The doc says: "MCP server tools (searchTools...): Call directly via MCP protocol, NOT through execute_tool()"
        # This implies I cannot call `searchTools` via `client.execute_tool` easily if the SDK doesn't wrap it?
        # But wait, the `test_sdk.py` earlier had:
        # result = client.execute_tool("web_search", ...)
        # And the doc says: "2. Installed/Deployed Tools... Use execute_tool()"
        
        # If `search_linkedin_person` is installed, I should be able to call it.
        # Maybe I need to find the "mcp_Provider_tool" name for it if it exists.
        
        # Let's try to list tools via `mcp_Neon_run_sql` is working.
        
        # Let's just try to print what happens if I search.
        # The doc says: "MCP server tools... Call directly via MCP protocol... NOT through execute_tool()"
        # This means I can't use `client.execute_tool("searchTools", ...)`?
        # Let's try it anyway.
        
        # search_results = client.execute_tool("searchTools", {"query": "linkedin"})
        # print(f"Search Results: {search_results}")
        
        pass 
    except Exception as e:
        print(f"Error searching tools: {e}")

    print("Fetching records to enrich...")
    try:
        # Fetch records that need enrichment
        rows = client.execute_tool(
            "mcp_Neon_run_sql", 
            {
                "params": {
                    "sql": "SELECT id, first_name, last_name, email, linkedin_url FROM crm WHERE company IS NULL OR title IS NULL LIMIT 5",
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )
        
        if not rows or not rows[0]:
            print("No records found.")
            return

        records = rows[0]
        print(f"Found {len(records)} records.")

        for record in records:
            print(f"\nProcessing ID {record['id']} ({record.get('email')})...")
            
            params = {}
            if record.get('email'):
                params['email'] = record['email']
            
            first_name = record.get('first_name')
            last_name = record.get('last_name')
            
            # If names are missing, try to infer
            if not first_name and not last_name and record.get('email'):
                first_name, last_name = infer_name_from_email(record['email'])
                print(f"  Inferring name: {first_name} {last_name}")
            
            if first_name:
                params['firstName'] = first_name
            if last_name:
                params['lastName'] = last_name

            print(f"  Searching LinkedIn with params: {params}")
            try:
                result = client.execute_tool("search_linkedin_person", params)
                # print(f"  Raw Result: {json.dumps(result, indent=2)}")
                
                person = result.get('person')
                if not person:
                    print("  No person found.")
                    continue
                
                updates = []
                
                # Extract fields
                headline = person.get('headline')
                if headline:
                    # Escape single quotes for SQL
                    safe_headline = headline.replace("'", "''")
                    updates.append(f"title = '{safe_headline}'")
                    print(f"  Found Title: {headline}")
                
                location = person.get('location')
                if location:
                    safe_loc = location.replace("'", "''")
                    updates.append(f"location = '{safe_loc}'")
                    print(f"  Found Location: {location}")

                # Company info is usually in 'company' dict or 'positions'
                company_info = person.get('company')
                company_name = None
                industry = None
                
                if company_info:
                    company_name = company_info.get('name')
                    industry = company_info.get('industry')
                
                # Fallback to current position
                if not company_name and person.get('positions'):
                    positions = person.get('positions', {}).get('positionHistory', [])
                    if positions:
                        # Assuming first is current
                        current = positions[0]
                        company_name = current.get('companyName')
                        if not headline: # Fallback title
                            title_val = current.get('title')
                            if title_val:
                                safe_title = title_val.replace("'", "''")
                                updates.append(f"title = '{safe_title}'")

                if company_name:
                    safe_company = company_name.replace("'", "''")
                    updates.append(f"company = '{safe_company}'")
                    print(f"  Found Company: {company_name}")
                
                if industry:
                    safe_industry = industry.replace("'", "''")
                    updates.append(f"industry = '{safe_industry}'")
                    print(f"  Found Industry: {industry}")

                if updates:
                    sql = f"UPDATE crm SET {', '.join(updates)} WHERE id = {record['id']}"
                    # print(f"  Executing SQL: {sql}")
                    client.execute_tool(
                        "mcp_Neon_run_sql",
                        {
                            "params": {
                                "sql": sql,
                                "projectId": "rough-base-02149126",
                                "databaseName": "datagen"
                            }
                        }
                    )
                    print("  ✅ Updated record.")
                else:
                    print("  No relevant updates found.")

            except Exception as e:
                print(f"  ❌ Error searching/updating: {e}")
                
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    run()
