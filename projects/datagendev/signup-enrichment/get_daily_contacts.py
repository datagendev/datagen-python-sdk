import os
import sys
from datetime import datetime, timezone
from datagen_sdk import DatagenClient

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

def time_ago(created_at):
    """Convert datetime to human-readable 'time ago' string"""
    if not created_at:
        return "Unknown"

    if isinstance(created_at, str):
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            try:
                created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            except:
                return "Unknown"
    else:
        created_dt = created_at

    if created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - created_dt

    seconds = diff.total_seconds()
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

def get_top_contacts(limit=10, min_score=0):
    """
    Fetch top priority contacts from CRM.

    Args:
        limit: Maximum number of contacts to return (default: 10)
        min_score: Minimum priority score (default: 0)

    Returns:
        list: Top contacts with their details
    """
    try:
        result = client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": f"""
                        SELECT
                            id,
                            email,
                            first_name,
                            last_name,
                            company,
                            title,
                            location,
                            linkedin_url,
                            priority_score,
                            created_at,
                            user_signup_date,
                            priority_calculated_at
                        FROM crm
                        WHERE priority_score >= {min_score}
                        ORDER BY priority_score DESC, user_signup_date DESC
                        LIMIT {limit}
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
        print(f"Error fetching contacts: {e}")
        return []

def format_name(contact):
    """Format contact name from first_name, last_name, or email"""
    first = (contact.get('first_name') or '').strip()
    last = (contact.get('last_name') or '').strip()

    if first and last:
        return f"{first} {last}"
    elif first:
        return first
    elif last:
        return last
    else:
        # Fallback to email
        email = contact.get('email') or ''
        if email and '@' in email:
            return email.split('@')[0].capitalize()
        return "Unknown"

def print_contacts(contacts, show_all=False):
    """Pretty print the contact list"""
    if not contacts:
        print("\nNo contacts found with current criteria.")
        print("Run 'python calculate_priority.py' to calculate scores first.\n")
        return

    today = datetime.now().strftime('%Y-%m-%d')

    print("\n" + "="*70)
    print(f"📋 Top {len(contacts)} Priority Contacts for {today}")
    print("="*70)

    for i, contact in enumerate(contacts, 1):
        name = format_name(contact)
        email = contact.get('email', 'No email')
        score = contact.get('priority_score', 0)
        company = contact.get('company') or 'Unknown Company'
        title = contact.get('title') or 'Unknown Title'
        linkedin = contact.get('linkedin_url', '')
        # Use user_signup_date if available, otherwise fall back to created_at
        signup_date = contact.get('user_signup_date') or contact.get('created_at')
        signed_up = time_ago(signup_date)

        # Color code score
        if score >= 90:
            score_icon = "🔥"
        elif score >= 75:
            score_icon = "⭐"
        elif score >= 50:
            score_icon = "✓"
        else:
            score_icon = "·"

        print(f"\n{i}. {score_icon} [Score: {score}] {name}")
        print(f"   {title} @ {company}")
        print(f"   📧 {email}")

        if linkedin:
            print(f"   🔗 {linkedin}")

        print(f"   📅 Signed up: {signed_up}")

        if show_all:
            location = contact.get('location')
            if location:
                print(f"   📍 {location}")

    print("\n" + "="*70)
    print(f"\n💡 Tip: Run 'python calculate_priority.py' daily to refresh scores")

def export_to_csv(contacts, filename='daily_contacts.csv'):
    """Export contacts to CSV file"""
    import csv

    if not contacts:
        print("No contacts to export")
        return

    with open(filename, 'w', newline='') as f:
        fieldnames = ['rank', 'score', 'name', 'email', 'company', 'title',
                      'linkedin_url', 'signed_up_at']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for i, contact in enumerate(contacts, 1):
            writer.writerow({
                'rank': i,
                'score': contact.get('priority_score', 0),
                'name': format_name(contact),
                'email': contact.get('email', ''),
                'company': contact.get('company', ''),
                'title': contact.get('title', ''),
                'linkedin_url': contact.get('linkedin_url', ''),
                'signed_up_at': contact.get('created_at', '')
            })

    print(f"\n✅ Exported {len(contacts)} contacts to {filename}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Get your daily priority contacts')
    parser.add_argument('--limit', type=int, default=10,
                        help='Number of contacts to show (default: 10)')
    parser.add_argument('--min-score', type=int, default=0,
                        help='Minimum priority score (default: 0)')
    parser.add_argument('--all', action='store_true',
                        help='Show all contact details')
    parser.add_argument('--export', metavar='FILE',
                        help='Export to CSV file')

    args = parser.parse_args()

    contacts = get_top_contacts(limit=args.limit, min_score=args.min_score)

    if args.export:
        export_to_csv(contacts, args.export)
    else:
        print_contacts(contacts, show_all=args.all)
