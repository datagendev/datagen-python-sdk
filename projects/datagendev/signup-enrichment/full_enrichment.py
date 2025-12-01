import os
import sys
import json
import re
import time
from datetime import datetime
from collections import Counter
from datagen_sdk import DatagenClient

# Load environment variables
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if (value.startswith("'") and value.endswith("'")) or \
                   (value.startswith("\"") and value.endswith("\"")):
                    value = value[1:-1]
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

if not os.getenv('DATAGEN_API_KEY'):
    print("Error: DATAGEN_API_KEY not set")
    sys.exit(1)

client = DatagenClient()

def infer_name_from_email(email):
    if not email or '@' not in email:
        return None, None
    user_part = email.split('@')[0]
    if '.' in user_part:
        parts = user_part.split('.')
        if len(parts) >= 2:
            return parts[0].capitalize(), parts[1].capitalize()
    if '_' in user_part:
        parts = user_part.split('_')
        if len(parts) >= 2:
            return parts[0].capitalize(), parts[1].capitalize()
    return user_part.capitalize(), None

def run():
    print("Starting Daily Signup Enrichment Workflow...")
    
    # --- Step 1: Identify Target Users ---
    print("\n--- Step 1: Identifying Target Users ---")
    try:
        # Note: 'created_at' column was missing in previous attempts, so we removed the time filter.
        sql_query = "SELECT id, email, first_name, last_name, company FROM crm WHERE linkedin_url IS NULL LIMIT 20;"
        
        result = client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": sql_query,
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )
        
        users = []
        if isinstance(result, list) and len(result) > 0:
            users = result[0]
        elif isinstance(result, dict):
             # Handle if it returns a dict with 'rows'
             users = result.get('rows', [])
             
        if not users:
            print("No users found needing enrichment.")
            return

        print(f"Found {len(users)} users to process.")
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        return

    # Stats for Step 4
    enriched_count = 0
    role_counts = Counter()
    industry_counts = Counter()

    # --- Step 2: Cascading Enrichment ---
    print("\n--- Step 2 & 3: Cascading Enrichment & Update ---")
    
    for user in users:
        user_id = user.get('id')
        email = user.get('email')
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        company = user.get('company')
        
        print(f"\nProcessing User ID: {user_id} ({email})")
        
        # Name inference
        if not first_name or not last_name:
            fn, ln = infer_name_from_email(email)
            first_name = first_name or fn
            last_name = last_name or ln
            print(f"  Inferred name: {first_name} {last_name}")

        linkedin_url = None
        source = None

        # Step 2.1: Datagen Direct Search
        print("  [Step 2.1] Trying Datagen Search...")
        try:
            params = {}
            if email: params['email'] = email
            if first_name: params['firstName'] = first_name
            if last_name: params['lastName'] = last_name
            if company: params['companyName'] = company
            
            dg_result = client.execute_tool("search_linkedin_person", params)
            person = dg_result.get('person')
            if person and person.get('linkedInUrl'):
                linkedin_url = person.get('linkedInUrl')
                source = "Datagen"
                print(f"    Found URL via Datagen: {linkedin_url}")
        except Exception as e:
            print(f"    Datagen search failed: {e}")

        # Step 2.2: Linkup Search (Fallback #1)
        if not linkedin_url:
            print("  [Step 2.2] Trying Linkup Search...")
            try:
                query = f"{first_name} {last_name} {company or ''} site:linkedin.com/in/".strip()
                linkup_result = client.execute_tool(
                    "mcp_Linkup_search",
                    {
                        "query": query,
                        "depth": "standard",
                        "output_type": "searchResults"
                    }
                )
                items = linkup_result if isinstance(linkup_result, list) else linkup_result.get('items', [])
                for item in items:
                    url = item.get('url', '')
                    if url.startswith("https://www.linkedin.com/in/"):
                        linkedin_url = url
                        source = "Linkup"
                        print(f"    Found URL via Linkup: {linkedin_url}")
                        break
            except Exception as e:
                print(f"    Linkup search failed: {e}")

        # Step 2.3: Exa Search (Fallback #2)
        if not linkedin_url:
            print("  [Step 2.3] Trying Exa Search...")
            try:
                exa_query = f"linkedin profile for {first_name} {last_name} at {company or ''}".strip()
                exa_result = client.execute_tool(
                    "mcp_Exa_web_search_exa",
                    {
                        "query": exa_query,
                        "num_results": 1,
                        "use_autoprompt": True
                    }
                )
                
                results = []
                if isinstance(exa_result, list):
                    results = exa_result
                elif isinstance(exa_result, dict):
                    results = exa_result.get('results', [])
                
                for res in results:
                    # Exa sometimes returns strings formatted with content
                    if isinstance(res, str):
                        match = re.search(r"URL: (https?://www\.linkedin\.com/in/[^\s]+)", res)
                        if match:
                            linkedin_url = match.group(1)
                            source = "Exa"
                            print(f"    Found URL via Exa: {linkedin_url}")
                            break
                    elif isinstance(res, dict):
                         url = res.get('url', '')
                         if "linkedin.com/in/" in url:
                             linkedin_url = url
                             source = "Exa"
                             print(f"    Found URL via Exa: {linkedin_url}")
                             break
            except Exception as e:
                print(f"    Exa search failed: {e}")

        if not linkedin_url:
            print("  ❌ Could not find LinkedIn URL.")
            continue

        # --- Step 3: Deep Profile Enrichment & Update ---
        print(f"  [Step 3] Enriching profile from {linkedin_url}...")
        try:
            profile_data = client.execute_tool(
                "get_linkedin_person_data",
                {"linkedin_url": linkedin_url}
            )
            
            # The tool might return the person object directly or wrapped.
            person_details = profile_data.get('person') if 'person' in profile_data else profile_data

            # Extract fields safely
            new_title = person_details.get('headline') or person_details.get('jobTitle')
            new_company = person_details.get('company')
            if isinstance(new_company, dict):
                new_company = new_company.get('name')
            
            new_location = person_details.get('location')
            new_industry = person_details.get('industry')
            
            # Update DB
            updates = [f"linkedin_url = '{linkedin_url}'"]
            
            if new_title:
                updates.append(f"title = '{new_title.replace("'", "''")}'")
                role_counts[new_title] += 1
            if new_company:
                updates.append(f"company = '{new_company.replace("'", "''")}'")
            if new_industry:
                updates.append(f"industry = '{new_industry.replace("'", "''")}'")
                industry_counts[new_industry] += 1
            if new_location:
                updates.append(f"location = '{new_location.replace("'", "''")}'")
            
            sql_update = f"UPDATE crm SET {', '.join(updates)} WHERE id = {user_id};"
            
            client.execute_tool(
                "mcp_Neon_run_sql",
                {
                    "params": {
                        "sql": sql_update,
                        "projectId": "rough-base-02149126",
                        "databaseName": "datagen"
                    }
                }
            )
            print("    ✅ CRM Updated.")
            enriched_count += 1
            
        except Exception as e:
            print(f"    Error during enrichment/update: {e}")

    # --- Step 4: ICP Refinement ---
    print("\n--- Step 4: ICP Refinement ---")
    if enriched_count > 0:
        try:
            icp_file = "icp.md"
            today = datetime.now().strftime("%Y-%m-%d")
            
            top_roles = ", ".join([f"{c} {r}" for r, c in role_counts.most_common(2)])
            top_industries = ", ".join([i for i, c in industry_counts.most_common(1)])
            
            update_entry = f"\n\n## Update: {today}\n"
            update_entry += f"- **New Signups:** {enriched_count} enriched.\n"
            update_entry += f"- **Top Roles:** {top_roles if top_roles else 'N/A'}.\n"
            update_entry += f"- **Top Industries:** {top_industries if top_industries else 'N/A'}.\n"
            update_entry += "- **Observation:** Automated enrichment batch.\n"
            
            if os.path.exists(icp_file):
                with open(icp_file, 'r') as f:
                    content = f.read()
                content += update_entry
            else:
                content = "# Ideal Customer Profile (ICP)" + update_entry
                
            with open(icp_file, 'w') as f:
                f.write(content)
                
            print(f"Updated {icp_file}")
            
        except Exception as e:
            print(f"Error updating ICP: {e}")
    else:
        print("No enrichments performed (or no new data), skipping ICP update.")

if __name__ == "__main__":
    run()