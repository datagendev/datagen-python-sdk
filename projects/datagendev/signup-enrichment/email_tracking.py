"""
Email Tracking Service for CRM

Syncs email interactions with Gmail API and updates CRM database with:
- Email status (not_contacted, contacted, replied, needs_followup)
- Sent/received counts and timestamps
- Follow-up flags based on 3-day rule
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from datagen_sdk import DatagenClient


class EmailTrackingService:
    """Service for tracking email interactions and updating CRM database"""

    def __init__(self, client: Optional[DatagenClient] = None):
        """
        Initialize email tracking service

        Args:
            client: DatagenClient instance (creates new one if not provided)
        """
        self.client = client or DatagenClient()
        self.project_id = "rough-base-02149126"
        self.database_name = "datagen"

    def sync_contact_emails(self, email: str, contact_id: int) -> Dict:
        """
        Sync email history for a single contact

        Args:
            email: Contact's email address
            contact_id: Contact's database ID

        Returns:
            Dict with sync results and status
        """
        print(f"Syncing emails for {email} (ID: {contact_id})")

        try:
            # Query Gmail API for all emails to/from this contact
            search_results = self.client.execute_tool(
                "mcp_Gmail_gmail_search_emails",
                {
                    "query": f"to:{email} OR from:{email}",
                    "max_results": 50  # Get more history for accurate counts
                }
            )

            # Parse Gmail results
            emails = self._parse_gmail_results(search_results)

            if not emails:
                print(f"  No emails found for {email}")
                # Update as not_contacted
                self._update_database(
                    contact_id=contact_id,
                    email_status='not_contacted',
                    emails_sent_count=0,
                    emails_received_count=0,
                    last_email_sent_at=None,
                    last_email_received_at=None,
                    needs_followup=False
                )
                return {
                    'success': True,
                    'email': email,
                    'status': 'not_contacted',
                    'sent': 0,
                    'received': 0
                }

            # Separate sent vs received and get timestamps
            sent_emails, received_emails = self._classify_emails(emails, email)

            # Calculate status
            status = self._calculate_status(
                len(sent_emails),
                len(received_emails),
                sent_emails[0] if sent_emails else None,
                received_emails[0] if received_emails else None
            )

            # Get latest timestamps
            last_sent = sent_emails[0] if sent_emails else None
            last_received = received_emails[0] if received_emails else None

            # Calculate needs_followup
            needs_followup = self._calculate_needs_followup(last_sent, last_received)

            # Update database
            self._update_database(
                contact_id=contact_id,
                email_status=status,
                emails_sent_count=len(sent_emails),
                emails_received_count=len(received_emails),
                last_email_sent_at=last_sent,
                last_email_received_at=last_received,
                needs_followup=needs_followup
            )

            print(f"  ✓ Synced: {status} | Sent: {len(sent_emails)} | Received: {len(received_emails)} | Follow-up: {needs_followup}")

            return {
                'success': True,
                'email': email,
                'status': status,
                'sent': len(sent_emails),
                'received': len(received_emails),
                'needs_followup': needs_followup
            }

        except Exception as e:
            print(f"  ✗ Error syncing {email}: {e}")
            return {
                'success': False,
                'email': email,
                'error': str(e)
            }

    def update_after_send(self, contact_id: int, email: str) -> Dict:
        """
        Quick update after sending an email (doesn't query Gmail)

        Args:
            contact_id: Contact's database ID
            email: Contact's email address

        Returns:
            Dict with update results
        """
        print(f"Updating tracking after send to {email} (ID: {contact_id})")

        try:
            # Get current counts from database
            current_data = self._get_current_tracking(contact_id)

            # Increment sent count
            new_sent_count = (current_data.get('emails_sent_count') or 0) + 1
            received_count = current_data.get('emails_received_count') or 0

            # Calculate new status
            status = self._calculate_status(
                new_sent_count,
                received_count,
                datetime.now(timezone.utc),  # Just sent now
                current_data.get('last_email_received_at')
            )

            # Update database
            self._update_database(
                contact_id=contact_id,
                email_status=status,
                emails_sent_count=new_sent_count,
                emails_received_count=received_count,
                last_email_sent_at=datetime.now(timezone.utc),
                last_email_received_at=current_data.get('last_email_received_at'),
                needs_followup=False  # Just sent, so no follow-up needed yet
            )

            print(f"  ✓ Updated: {status} | Sent: {new_sent_count}")

            return {
                'success': True,
                'email': email,
                'status': status,
                'sent': new_sent_count
            }

        except Exception as e:
            print(f"  ✗ Error updating after send: {e}")
            return {
                'success': False,
                'email': email,
                'error': str(e)
            }

    def sync_all_contacts(self, limit: int = 50) -> Dict:
        """
        Sync email tracking for multiple contacts

        Args:
            limit: Maximum number of contacts to sync

        Returns:
            Dict with batch sync results
        """
        print(f"Syncing email tracking for top {limit} contacts...")

        try:
            # Get top priority contacts
            contacts = self._get_contacts_to_sync(limit)

            if not contacts:
                print("No contacts found to sync")
                return {'success': True, 'synced': 0, 'failed': 0}

            print(f"Found {len(contacts)} contacts to sync\n")

            results = {
                'synced': 0,
                'failed': 0,
                'errors': []
            }

            for i, contact in enumerate(contacts, 1):
                contact_id = contact.get('id')
                email = contact.get('email')
                name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()

                print(f"[{i}/{len(contacts)}] {name} <{email}>")

                result = self.sync_contact_emails(email, contact_id)

                if result.get('success'):
                    results['synced'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'email': email,
                        'error': result.get('error')
                    })

                print()  # Blank line between contacts

            print(f"\n{'=' * 50}")
            print(f"Sync completed: {results['synced']} successful, {results['failed']} failed")

            return results

        except Exception as e:
            print(f"Batch sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_gmail_results(self, results: List) -> List[Dict]:
        """Parse Gmail API search results into list of email dicts"""
        if not results or not isinstance(results, list):
            return []

        # Extract emails array from response
        if len(results) > 0 and isinstance(results[0], dict):
            if 'emails' in results[0]:
                return results[0]['emails']

        return []

    def _classify_emails(self, emails: List[Dict], contact_email: str) -> Tuple[List, List]:
        """
        Classify emails as sent or received based on 'from' field

        Args:
            emails: List of email dicts from Gmail
            contact_email: Contact's email address

        Returns:
            Tuple of (sent_emails, received_emails) sorted by date DESC
        """
        sent_emails = []
        received_emails = []

        for email in emails:
            from_field = email.get('from', '').lower()
            email_date = self._parse_email_date(email.get('date'))

            email_data = {
                'date': email_date,
                'subject': email.get('subject', ''),
                'from': from_field
            }

            # If from field contains contact's email, they sent it to us (we received it)
            if contact_email.lower() in from_field:
                received_emails.append(email_data)
            else:
                # Otherwise, we sent it to them
                sent_emails.append(email_data)

        # Sort by date DESC (most recent first)
        sent_emails.sort(key=lambda x: x['date'] if x['date'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        received_emails.sort(key=lambda x: x['date'] if x['date'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        return (
            [e['date'] for e in sent_emails if e['date']],
            [e['date'] for e in received_emails if e['date']]
        )

    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse email date string into datetime object

        Handles multiple formats: RFC 2822, ISO 8601, etc.
        """
        if not date_str:
            return None

        try:
            # Try parsing common formats
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            try:
                # Fallback to ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                print(f"  Warning: Could not parse date: {date_str}")
                return None

    def _calculate_status(
        self,
        sent_count: int,
        received_count: int,
        last_sent: Optional[datetime],
        last_received: Optional[datetime]
    ) -> str:
        """
        Calculate email status based on counts and timestamps

        Returns: 'not_contacted', 'contacted', 'replied', or 'needs_followup'
        """
        if sent_count == 0:
            return 'not_contacted'

        if received_count > 0:
            return 'replied'

        # Check if needs follow-up (sent 3+ days ago, no reply)
        if self._calculate_needs_followup(last_sent, last_received):
            return 'needs_followup'

        return 'contacted'

    def _calculate_needs_followup(
        self,
        last_sent: Optional[datetime],
        last_received: Optional[datetime]
    ) -> bool:
        """
        Determine if contact needs follow-up

        Logic: Sent 3+ days ago AND (no reply OR last_received < last_sent)
        """
        if not last_sent:
            return False

        now = datetime.now(timezone.utc)

        # Ensure last_sent has timezone
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=timezone.utc)

        days_since_sent = (now - last_sent).days

        # Need follow-up if sent 3+ days ago
        if days_since_sent >= 3:
            # And either no reply received, or last reply was before our last message
            if not last_received:
                return True

            # Ensure last_received has timezone
            if last_received.tzinfo is None:
                last_received = last_received.replace(tzinfo=timezone.utc)

            if last_received < last_sent:
                return True

        return False

    def _get_current_tracking(self, contact_id: int) -> Dict:
        """Get current email tracking data for a contact"""
        sql = f"""
        SELECT emails_sent_count, emails_received_count, last_email_received_at
        FROM crm
        WHERE id = {contact_id}
        """

        result = self.client.execute_tool("mcp_Neon_run_sql", {
            "params": {
                "sql": sql,
                "projectId": self.project_id,
                "databaseName": self.database_name
            }
        })

        # Result is double-wrapped: [[{...}]]
        if result and isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list) and len(result[0]) > 0:
                return result[0][0]

        return {}

    def _get_contacts_to_sync(self, limit: int) -> List[Dict]:
        """Get top priority contacts to sync"""
        sql = f"""
        SELECT id, email, first_name, last_name
        FROM crm
        WHERE priority_score > 0
          AND email IS NOT NULL
        ORDER BY priority_score DESC
        LIMIT {limit}
        """

        result = self.client.execute_tool("mcp_Neon_run_sql", {
            "params": {
                "sql": sql,
                "projectId": self.project_id,
                "databaseName": self.database_name
            }
        })

        # Result is double-wrapped: [[{...}, {...}]]
        if result and isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                return result[0]

        return []

    def _update_database(
        self,
        contact_id: int,
        email_status: str,
        emails_sent_count: int,
        emails_received_count: int,
        last_email_sent_at: Optional[datetime],
        last_email_received_at: Optional[datetime],
        needs_followup: bool
    ):
        """Update CRM database with email tracking data"""

        # Format timestamps for SQL
        sent_at_sql = f"'{last_email_sent_at.isoformat()}'" if last_email_sent_at else 'NULL'
        received_at_sql = f"'{last_email_received_at.isoformat()}'" if last_email_received_at else 'NULL'

        sql = f"""
        UPDATE crm
        SET
            email_status = '{email_status}',
            emails_sent_count = {emails_sent_count},
            emails_received_count = {emails_received_count},
            last_email_sent_at = {sent_at_sql},
            last_email_received_at = {received_at_sql},
            needs_followup = {str(needs_followup).lower()},
            email_tracking_last_synced_at = NOW()
        WHERE id = {contact_id}
        """

        self.client.execute_tool("mcp_Neon_run_sql", {
            "params": {
                "sql": sql,
                "projectId": self.project_id,
                "databaseName": self.database_name
            }
        })
