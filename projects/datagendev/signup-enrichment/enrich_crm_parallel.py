import os
import sys
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def process_record(record):
    """
    Process a single record: search LinkedIn and update DB.
    """
    record_id = record['id']
    email = record.get('email')
    
    # Random sleep to avoid burstiness and respect rate limits
    time.sleep(random.uniform(0.5, 2.0))
    
    print(f"[Thread-{record_id}] Processing ID {record_id} ({email})...")
    
    params = {}
    if email:
        params['email'] = email
    
    first_name = record.get('first_name')
    last_name = record.get('last_name')
    
    # If names are missing, try to infer
    if not first_name and not last_name and email:
        first_name, last_name = infer_name_from_email(email)
        print(f"[Thread-{record_id}]   Inferring name: {first_name} {last_name}")
    
    if first_name:
        params['firstName'] = first_name
    if last_name:
        params['lastName'] = last_name

    # print(f"[Thread-{record_id}]   Searching LinkedIn with params: {params}")
    try:
        result = client.execute_tool("search_linkedin_person", params)
        
        person = result.get('person')
        if not person:
            print(f"[Thread-{record_id}]   No person found.")
            return
        
        updates = []
        
        # Extract fields
        headline = person.get('headline')
        if headline:
            safe_headline = headline.replace("'", "''")
            updates.append(f"title = '{safe_headline}'")
            # print(f"[Thread-{record_id}]   Found Title: {headline}")
        
        location = person.get('location')
        if location:
            safe_loc = location.replace("'", "''")
            updates.append(f"location = '{safe_loc}'")
            # print(f"[Thread-{record_id}]   Found Location: {location}")

        # Company info
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
            # print(f"[Thread-{record_id}]   Found Company: {company_name}")
        
        if industry:
            safe_industry = industry.replace("'", "''")
            updates.append(f"industry = '{safe_industry}'")
            # print(f"[Thread-{record_id}]   Found Industry: {industry}")

        if updates:
            sql = f"UPDATE crm SET {', '.join(updates)} WHERE id = {record_id}"
            
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
            print(f"[Thread-{record_id}]   ✅ Updated record.")
        else:
            print(f"[Thread-{record_id}]   No relevant updates found.")

    except Exception as e:
        print(f"[Thread-{record_id}]   ❌ Error: {e}")

def run():
    print("Fetching records to enrich...")
    try:
        # Fetch records that need enrichment
        # Increased LIMIT to 20 for parallel processing demo
        rows = client.execute_tool(
            "mcp_Neon_run_sql", 
            {
                "params": {
                    "sql": "SELECT id, first_name, last_name, email, linkedin_url FROM crm WHERE company IS NULL OR title IS NULL LIMIT 20",
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )
        
        if not rows or not rows[0]:
            print("No records found.")
            return

        records = rows[0]
        print(f"Found {len(records)} records. Starting parallel processing...")

        # Parallel execution
        max_workers = 3 # Conservative limit for rate limiting
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_record, record) for record in records]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Task failed: {e}")
                    
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    run()
