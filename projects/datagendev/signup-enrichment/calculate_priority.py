import os
import sys
from datetime import datetime, timezone
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

def calculate_recency_score(created_at, decay_factor=5):
    """
    Calculate priority score based on recency.

    Args:
        created_at: datetime or ISO string of when record was created
        decay_factor: Points lost per day (default: 5)

    Returns:
        int: Priority score (0-100)

    Formula:
        score = 100 - (days_since_signup * decay_factor)
        score = max(0, min(100, score))
    """
    if not created_at:
        return 0

    # Parse datetime if it's a string
    if isinstance(created_at, str):
        # Handle various ISO formats
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            try:
                created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            except:
                return 0
    else:
        created_dt = created_at

    # Ensure timezone aware
    if created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)

    # Calculate days since signup
    now = datetime.now(timezone.utc)
    days_old = (now - created_dt).total_seconds() / 86400  # seconds in a day

    # Calculate score
    score = 100 - (days_old * decay_factor)

    # Clamp between 0 and 100
    return max(0, min(100, int(score)))

def update_priority_scores(decay_factor=5, dry_run=False):
    """
    Update priority scores for all CRM contacts.

    Args:
        decay_factor: Points lost per day (default: 5)
        dry_run: If True, don't update database (just show what would happen)

    Returns:
        dict: Statistics about the update
    """
    print(f"{'[DRY RUN] ' if dry_run else ''}Fetching all CRM records...")

    # Fetch all contacts
    try:
        result = client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": "SELECT id, email, created_at, user_signup_date FROM crm ORDER BY id",
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )

        if not result or not result[0]:
            print("No records found in CRM")
            return {"total": 0, "updated": 0, "errors": 0}

        records = result[0]
        print(f"Found {len(records)} records\n")

    except Exception as e:
        print(f"Error fetching records: {e}")
        return {"total": 0, "updated": 0, "errors": 0}

    # Calculate scores
    stats = {
        "total": len(records),
        "updated": 0,
        "errors": 0,
        "score_distribution": {
            "90-100": 0,
            "75-89": 0,
            "50-74": 0,
            "25-49": 0,
            "1-24": 0,
            "0": 0
        }
    }

    print(f"{'[DRY RUN] ' if dry_run else ''}Calculating priority scores...")

    with tqdm(total=len(records), desc="Processing contacts", unit="contact") as pbar:
        for record in records:
            try:
                # Use user_signup_date if available, otherwise fall back to created_at
                signup_date = record.get('user_signup_date') or record.get('created_at')
                score = calculate_recency_score(signup_date, decay_factor)

                # Update score distribution
                if score >= 90:
                    stats["score_distribution"]["90-100"] += 1
                elif score >= 75:
                    stats["score_distribution"]["75-89"] += 1
                elif score >= 50:
                    stats["score_distribution"]["50-74"] += 1
                elif score >= 25:
                    stats["score_distribution"]["25-49"] += 1
                elif score > 0:
                    stats["score_distribution"]["1-24"] += 1
                else:
                    stats["score_distribution"]["0"] += 1

                if not dry_run:
                    # Update database
                    client.execute_tool(
                        "mcp_Neon_run_sql",
                        {
                            "params": {
                                "sql": f"""
                                    UPDATE crm
                                    SET priority_score = {score},
                                        priority_calculated_at = NOW()
                                    WHERE id = {record['id']}
                                """,
                                "projectId": "rough-base-02149126",
                                "databaseName": "datagen"
                            }
                        }
                    )

                stats["updated"] += 1
                pbar.update(1)

            except Exception as e:
                stats["errors"] += 1
                pbar.write(f"Error processing ID {record.get('id')}: {e}")
                pbar.update(1)

    return stats

def print_stats(stats):
    """Print statistics from the update"""
    print("\n" + "="*50)
    print("Priority Score Calculation Results")
    print("="*50)
    print(f"Total Records: {stats['total']}")
    print(f"Successfully Updated: {stats['updated']}")
    print(f"Errors: {stats['errors']}")
    print("\nScore Distribution:")
    print(f"  90-100 (Hot Leads):     {stats['score_distribution']['90-100']:>4} contacts")
    print(f"  75-89  (High Priority): {stats['score_distribution']['75-89']:>4} contacts")
    print(f"  50-74  (Medium):        {stats['score_distribution']['50-74']:>4} contacts")
    print(f"  25-49  (Low):           {stats['score_distribution']['25-49']:>4} contacts")
    print(f"  1-24   (Very Low):      {stats['score_distribution']['1-24']:>4} contacts")
    print(f"  0      (Expired):       {stats['score_distribution']['0']:>4} contacts")
    print("="*50)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Calculate and update CRM priority scores')
    parser.add_argument('--decay-factor', type=int, default=5,
                        help='Points lost per day (default: 5)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without updating database')

    args = parser.parse_args()

    print(f"\nPriority Score Calculator")
    print(f"Decay Factor: {args.decay_factor} points/day")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}\n")

    stats = update_priority_scores(decay_factor=args.decay_factor, dry_run=args.dry_run)
    print_stats(stats)

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made to the database")
        print("Run without --dry-run to apply changes")
