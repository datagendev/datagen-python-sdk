#!/usr/bin/env python3
"""
Migration script to:
1. Add email_draft JSONB column to CRM table
2. Migrate existing .md email drafts to the database
"""

import os
import json
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

client = DatagenClient()

def add_email_draft_column():
    """Add email_draft JSONB column to CRM table"""
    print("Adding email_draft column to CRM table...")

    result = client.execute_tool(
        "mcp_Neon_run_sql",
        {
            "params": {
                "sql": """
                    ALTER TABLE crm
                    ADD COLUMN IF NOT EXISTS email_draft JSONB;
                """,
                "projectId": "rough-base-02149126",
                "databaseName": "datagen"
            }
        }
    )
    print("✓ Column added successfully")
    return result

def parse_email_draft(filepath):
    """Parse .md file to extract subject and body"""
    with open(filepath, 'r') as f:
        content = f.read()

    subject = ""
    body = ""

    # Extract subject
    if "**Subject:**" in content:
        subject_start = content.find("**Subject:**") + len("**Subject:**")
        subject_end = content.find("\n", subject_start)
        subject = content[subject_start:subject_end].strip()

    # Extract body
    if "**Body:**" in content:
        body_start = content.find("**Body:**") + len("**Body:**")
        # Find the end of the email draft section
        body_end = content.find("\n---", body_start)
        if body_end == -1:
            body_end = content.find("\n##", body_start)
        if body_end == -1:
            body_end = len(content)

        body = content[body_start:body_end].strip()

    return subject, body

def migrate_md_drafts():
    """Migrate existing .md drafts to database"""
    print("\nMigrating .md files to database...")

    drafts_dir = "outreach_emails"
    if not os.path.exists(drafts_dir):
        print(f"No {drafts_dir} directory found, skipping migration")
        return

    # Get all .md files
    md_files = [f for f in os.listdir(drafts_dir) if f.endswith('.md')]

    if not md_files:
        print("No .md files found to migrate")
        return

    print(f"Found {len(md_files)} draft files to migrate")

    # Get all CRM records
    crm_records = client.execute_tool(
        "mcp_Neon_run_sql",
        {
            "params": {
                "sql": "SELECT id, first_name, last_name, email FROM crm",
                "projectId": "rough-base-02149126",
                "databaseName": "datagen"
            }
        }
    )

    if not crm_records or not crm_records[0]:
        print("No CRM records found")
        return

    records = crm_records[0]
    migrated_count = 0

    for md_file in md_files:
        filename = md_file.replace('.md', '')
        filepath = os.path.join(drafts_dir, md_file)

        print(f"\nProcessing: {md_file}")

        # Find matching CRM record
        matching_record = None
        for record in records:
            first_name = (record.get('first_name') or '').strip().lower()
            last_name = (record.get('last_name') or '').strip().lower()
            email = record.get('email', '')
            email_username = email.split('@')[0] if email else ''

            # Try to match by:
            # 1. Full name format (firstname_lastname)
            # 2. Email username
            # 3. Partial match - filename contains part of email username or vice versa
            name_match = (first_name and last_name and filename.lower() == f"{first_name}_{last_name}")
            email_match = (email_username and filename.lower() == email_username.lower())
            # Check if first part of filename matches first part of email
            filename_first = filename.split('_')[0].lower()
            partial_match = (email_username and filename_first in email_username.lower())

            if name_match or email_match or partial_match:
                print(f"  ✓ Matched with: {email} (name_match={name_match}, email_match={email_match}, partial_match={partial_match})")
                matching_record = record
                break

        if matching_record:
            try:
                # Parse the draft
                subject, body = parse_email_draft(filepath)

                if subject or body:
                    # Create draft JSON
                    draft_data = {
                        "subject": subject,
                        "body": body,
                        "source": "migration",
                        "created_at": "2025-11-29T23:31:00Z"
                    }

                    # Escape single quotes in JSON string for SQL
                    json_str = json.dumps(draft_data).replace("'", "''")

                    # Update CRM record
                    result = client.execute_tool(
                        "mcp_Neon_run_sql",
                        {
                            "params": {
                                "sql": f"""
                                    UPDATE crm
                                    SET email_draft = '{json_str}'::jsonb
                                    WHERE id = {matching_record['id']}
                                """,
                                "projectId": "rough-base-02149126",
                                "databaseName": "datagen"
                            }
                        }
                    )

                    print(f"✓ Migrated draft for {matching_record.get('first_name', '')} {matching_record.get('last_name', '')} (ID: {matching_record['id']})")
                    migrated_count += 1

            except Exception as e:
                print(f"✗ Error migrating {md_file}: {e}")
        else:
            print(f"⚠ No matching CRM record found for {md_file}")

    print(f"\n✓ Migration complete: {migrated_count}/{len(md_files)} drafts migrated")

def verify_migration():
    """Verify the migration"""
    print("\nVerifying migration...")

    result = client.execute_tool(
        "mcp_Neon_run_sql",
        {
            "params": {
                "sql": """
                    SELECT
                        id,
                        email,
                        first_name,
                        last_name,
                        email_draft->>'subject' as draft_subject
                    FROM crm
                    WHERE email_draft IS NOT NULL
                """,
                "projectId": "rough-base-02149126",
                "databaseName": "datagen"
            }
        }
    )

    if result and result[0]:
        print(f"\n✓ Found {len(result[0])} records with email drafts:")
        for record in result[0]:
            print(f"  - {record.get('first_name', '')} {record.get('last_name', '')} ({record.get('email', '')})")
            print(f"    Subject: {record.get('draft_subject', 'N/A')}")
    else:
        print("No records with email drafts found")

if __name__ == "__main__":
    print("Starting email draft migration...\n")

    # Step 1: Add column
    add_email_draft_column()

    # Step 2: Migrate drafts
    migrate_md_drafts()

    # Step 3: Verify
    verify_migration()

    print("\n✓ Migration complete!")
