import os
import sys
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datagen_sdk import DatagenClient

try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm for progress bar...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

# Load environment variables
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

api_key = os.getenv('DATAGEN_API_KEY')
if not api_key:
    print("Error: DATAGEN_API_KEY not set")
    sys.exit(1)

client = DatagenClient()

def fetch_new_profiles_from_db():
    """Fetch LinkedIn URLs from CRM where profile hasn't been fetched yet"""
    print("Fetching new LinkedIn URLs from CRM (not yet processed)...")
    try:
        result = client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": """
                        SELECT id, email, linkedin_url, company, title, location, enrich_source
                        FROM crm
                        WHERE linkedin_url IS NOT NULL
                          AND linkedin_url != ''
                          AND linkedin_profile_fetched_at IS NULL
                        ORDER BY id DESC
                    """,
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )

        if result and result[0]:
            return result[0]
        return []
    except Exception as e:
        print(f"Error fetching from database: {e}")
        return []

def fetch_linkedin_profile(linkedin_url):
    """Fetch detailed LinkedIn profile data"""
    try:
        result = client.execute_tool(
            "get_linkedin_person_data",
            {"linkedin_url": linkedin_url}
        )
        return result
    except Exception as e:
        print(f"  Error fetching profile: {e}")
        return None

def mark_profile_as_fetched(crm_id):
    """Update the linkedin_profile_fetched_at timestamp"""
    try:
        client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": f"UPDATE crm SET linkedin_profile_fetched_at = NOW() WHERE id = {crm_id}",
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )
        return True
    except Exception as e:
        print(f"  Warning: Failed to mark profile as fetched: {e}")
        return False

def process_single_profile(record):
    """Process a single profile fetch (for parallel execution)"""
    linkedin_url = record.get('linkedin_url')
    email = record.get('email')
    crm_id = record.get('id')

    if not linkedin_url or linkedin_url == '':
        return None

    profile_data = fetch_linkedin_profile(linkedin_url)

    if profile_data and profile_data.get('person'):
        # Mark as fetched in database
        mark_profile_as_fetched(crm_id)

        return {
            "crm_id": crm_id,
            "email": email,
            "linkedin_url": linkedin_url,
            "enrich_source": record.get('enrich_source'),
            "crm_company": record.get('company'),
            "crm_title": record.get('title'),
            "crm_location": record.get('location'),
            "profile": profile_data.get('person'),
            "fetched_at": datetime.now().isoformat(),
            "success": True
        }
    else:
        return {
            "crm_id": crm_id,
            "email": email,
            "linkedin_url": linkedin_url,
            "enrich_source": record.get('enrich_source'),
            "crm_company": record.get('company'),
            "crm_title": record.get('title'),
            "crm_location": record.get('location'),
            "profile": None,
            "error": "Failed to fetch profile data",
            "fetched_at": datetime.now().isoformat(),
            "success": False
        }

def run():
    # Fetch CRM records that haven't been processed yet
    crm_records = fetch_new_profiles_from_db()

    if not crm_records:
        print("✅ No new profiles to fetch. All profiles are up to date!")
        return

    print(f"Found {len(crm_records)} NEW profiles to fetch")
    print(f"Fetching profiles in parallel with progress bar...\n")

    all_profiles = []
    success_count = 0
    failed_count = 0

    # Use ThreadPoolExecutor for parallel processing
    max_workers = 5  # Adjust based on API rate limits

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_record = {
            executor.submit(process_single_profile, record): record
            for record in crm_records
        }

        # Process completed tasks with progress bar
        with tqdm(total=len(crm_records), desc="Fetching profiles", unit="profile") as pbar:
            for future in as_completed(future_to_record):
                record = future_to_record[future]
                try:
                    result = future.result()
                    if result:
                        all_profiles.append(result)
                        if result.get('success'):
                            success_count += 1
                            pbar.set_postfix({'✅': success_count, '❌': failed_count})
                        else:
                            failed_count += 1
                            pbar.set_postfix({'✅': success_count, '❌': failed_count})
                except Exception as e:
                    failed_count += 1
                    pbar.set_postfix({'✅': success_count, '❌': failed_count})
                    tqdm.write(f"❌ Exception for {record.get('email')}: {e}")

                pbar.update(1)

    # Sort profiles by crm_id to maintain consistent order
    all_profiles.sort(key=lambda x: x['crm_id'], reverse=True)

    # Remove 'success' flag before saving (internal use only)
    for profile in all_profiles:
        profile.pop('success', None)

    # Save ONLY the latest batch to file (overwrite previous)
    output_file = "linkedin_profiles_latest_batch.json"
    with open(output_file, 'w') as f:
        json.dump({
            "batch_date": datetime.now().isoformat(),
            "total_in_batch": len(crm_records),
            "profiles_fetched": success_count,
            "profiles_failed": failed_count,
            "profiles": all_profiles
        }, f, indent=2)

    print(f"\n✅ Saved {len(all_profiles)} NEW profiles to {output_file}")
    print(f"   Successfully fetched: {success_count}")
    print(f"   Failed to fetch: {failed_count}")
    print(f"\n💡 Next step: Run generate_icp.py to update ICP analysis")

if __name__ == "__main__":
    run()
