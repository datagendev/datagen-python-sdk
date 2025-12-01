"""
CLI Tool for syncing email tracking data from Gmail to CRM database

Usage:
    python sync_email_tracking.py --limit 50          # Sync top 50 contacts
    python sync_email_tracking.py --email user@example.com  # Sync specific contact
    python sync_email_tracking.py --dry-run           # Preview without changes
"""

import os
import argparse
from email_tracking import EmailTrackingService

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


def main():
    parser = argparse.ArgumentParser(
        description='Sync email tracking data from Gmail to CRM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --limit 20                    # Sync top 20 priority contacts
  %(prog)s --email user@example.com      # Sync specific email
  %(prog)s --limit 50 --dry-run          # Preview sync for top 50
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Number of contacts to sync (default: 50)'
    )

    parser.add_argument(
        '--email',
        type=str,
        help='Sync specific email address'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview mode - show what would be synced without making changes'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Email Tracking Sync Tool")
    print("=" * 60)

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")

    service = EmailTrackingService()

    if args.email:
        # Sync specific email
        print(f"\nSyncing single contact: {args.email}")
        print("-" * 60)

        if args.dry_run:
            print(f"Would sync: {args.email}")
            print("Run without --dry-run to execute")
        else:
            # Get contact ID from email
            from datagen_sdk import DatagenClient
            client = DatagenClient()

            sql = f"SELECT id FROM crm WHERE email = '{args.email}'"
            result = client.execute_tool("mcp_Neon_run_sql", {
                "params": {
                    "sql": sql,
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            })

            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    contact_id = result[0][0].get('id')
                    sync_result = service.sync_contact_emails(args.email, contact_id)

                    if sync_result.get('success'):
                        print(f"\n✓ Successfully synced {args.email}")
                        print(f"  Status: {sync_result.get('status')}")
                        print(f"  Sent: {sync_result.get('sent')}")
                        print(f"  Received: {sync_result.get('received')}")
                        print(f"  Needs follow-up: {sync_result.get('needs_followup')}")
                    else:
                        print(f"\n✗ Failed to sync {args.email}")
                        print(f"  Error: {sync_result.get('error')}")
            else:
                print(f"\n✗ Contact not found: {args.email}")

    else:
        # Sync multiple contacts
        print(f"\nSyncing top {args.limit} priority contacts")
        print("-" * 60)

        if args.dry_run:
            print(f"Would sync top {args.limit} contacts")
            print("Run without --dry-run to execute")
        else:
            results = service.sync_all_contacts(limit=args.limit)

            print("\n" + "=" * 60)
            print("SYNC SUMMARY")
            print("=" * 60)
            print(f"✓ Successful: {results.get('synced', 0)}")
            print(f"✗ Failed: {results.get('failed', 0)}")

            if results.get('errors'):
                print("\nErrors:")
                for error in results['errors']:
                    print(f"  - {error.get('email')}: {error.get('error')}")

    print("\n" + "=" * 60)
    print("Sync complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
