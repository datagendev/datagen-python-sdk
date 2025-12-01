import streamlit as st
import pandas as pd
import os
import sys
from datagen_sdk import DatagenClient

st.set_page_config(layout="wide", page_title="DataGen CRM & ICP Dashboard", page_icon="📊")

st.title("📊 DataGen CRM & ICP Dashboard")
st.markdown("Track enrichment progress and analyze Ideal Customer Profile insights")

# Simple .env loader
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
    st.warning("Warning: .env file not found")

api_key = os.getenv('DATAGEN_API_KEY')
if not api_key:
    st.error("Error: DATAGEN_API_KEY not set. Please set it in your .env file or environment variables.")
    st.stop()

client = DatagenClient()

def get_crm_data():
    try:
        rows = client.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": "SELECT id, first_name, last_name, email, company, title, location, industry, linkedin_url, enrich_source, linkedin_profile_fetched_at FROM crm ORDER BY id DESC",
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )

        if not rows or not rows[0]:
            return pd.DataFrame()

        records = rows[0]
        df = pd.DataFrame(records)

        # Add enrichment status columns
        df['Enrichment Status'] = df.apply(lambda row: 'Enriched' if pd.notna(row['company']) or pd.notna(row['title']) else 'Not Enriched', axis=1)
        df['LinkedIn Fetched'] = df['linkedin_profile_fetched_at'].notna()

        return df
    except Exception as e:
        st.error(f"Error fetching CRM data: {e}")
        return pd.DataFrame()

def get_top_priority_contacts(limit=10):
    """Fetch top priority contacts from CRM"""
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
                            linkedin_url,
                            priority_score,
                            created_at,
                            user_signup_date
                        FROM crm
                        WHERE priority_score > 0
                        ORDER BY priority_score DESC, user_signup_date DESC
                        LIMIT {limit}
                    """,
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )

        if result and result[0]:
            return pd.DataFrame(result[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching priority contacts: {e}")
        return pd.DataFrame()

def get_icp_summary():
    try:
        with open("icp_profile.md", 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "No ICP summary found. Run `python fetch_linkedin_profiles.py` and ask the agent to analyze the batch."
    except Exception as e:
        return f"Error reading ICP summary: {e}"

def load_email_draft(first_name, last_name, email, contact_id=None, client_instance=None):
    """Load email draft from CRM database, fallback to .md files"""
    # Safely handle None or empty values
    first_name = (first_name or '').strip()
    last_name = (last_name or '').strip()

    # Use global client if not passed
    if client_instance is None:
        client_instance = client

    # Try loading from database first
    if contact_id or email:
        try:
            # Query for draft from database
            if contact_id:
                query = f"SELECT email_draft FROM crm WHERE id = {contact_id}"
            else:
                query = f"SELECT email_draft FROM crm WHERE email = '{email}'"

            result = client_instance.execute_tool(
                "mcp_Neon_run_sql",
                {
                    "params": {
                        "sql": query,
                        "projectId": "rough-base-02149126",
                        "databaseName": "datagen"
                    }
                }
            )

            if result and result[0] and len(result[0]) > 0:
                draft_data = result[0][0].get('email_draft')
                if draft_data and isinstance(draft_data, dict):
                    subject = draft_data.get('subject', '')
                    body = draft_data.get('body', '')
                    if subject or body:
                        return subject, body, True, 'database'
        except Exception as e:
            st.warning(f"Error loading draft from database: {e}")

    # Fallback to .md files
    possible_filenames = []
    if first_name and last_name:
        possible_filenames.extend([
            f"{first_name.lower()}_{last_name.lower()}.md",
            f"{first_name}_{last_name}.md"
        ])
    if email:
        possible_filenames.append(f"{email.split('@')[0]}.md")

    for filename in possible_filenames:
        filepath = os.path.join("outreach_emails", filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    content = f.read()

                # Parse subject and body from the markdown
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
                    # Find the end of the email draft section (next --- or ## section)
                    body_end = content.find("\n---", body_start)
                    if body_end == -1:
                        body_end = content.find("\n##", body_start)
                    if body_end == -1:
                        body_end = len(content)

                    body = content[body_start:body_end].strip()

                return subject, body, True, 'file'
            except Exception as e:
                st.warning(f"Error reading email draft file: {e}")

    return "", "", False, None

def save_email_draft(contact_id, subject, body, client_instance=None):
    """Save email draft to CRM database"""
    import json
    from datetime import datetime

    # Use global client if not passed
    if client_instance is None:
        client_instance = client

    try:
        # Create draft JSON
        draft_data = {
            "subject": subject,
            "body": body,
            "updated_at": datetime.now().isoformat()
        }

        # Escape single quotes for SQL
        json_str = json.dumps(draft_data).replace("'", "''")

        # Update CRM record
        result = client_instance.execute_tool(
            "mcp_Neon_run_sql",
            {
                "params": {
                    "sql": f"""
                        UPDATE crm
                        SET email_draft = '{json_str}'::jsonb
                        WHERE id = {contact_id}
                    """,
                    "projectId": "rough-base-02149126",
                    "databaseName": "datagen"
                }
            }
        )
        return True
    except Exception as e:
        st.error(f"Error saving draft: {e}")
        return False


if st.button("Refresh Data"):
    st.session_state['crm_df'] = get_crm_data()
    st.session_state['priority_df'] = get_top_priority_contacts()

if 'crm_df' not in st.session_state:
    st.session_state['crm_df'] = get_crm_data()
    st.session_state['priority_df'] = get_top_priority_contacts()

# Priority Contacts Section
st.write("---")
st.write("### 🔥 Top Priority Contacts Today")
st.markdown("*Prioritized by recency - run `python calculate_priority.py` daily to update*")

if 'priority_df' in st.session_state and not st.session_state['priority_df'].empty:
    priority_df = st.session_state['priority_df'].copy()

    # Format the display
    priority_df['Name'] = priority_df.apply(
        lambda row: f"{row.get('first_name', '') or ''} {row.get('last_name', '') or ''}".strip() or row.get('email', '').split('@')[0],
        axis=1
    )
    priority_df['Score'] = priority_df['priority_score'].apply(lambda x: f"🔥 {x}" if x >= 90 else f"⭐ {x}" if x >= 75 else f"✓ {x}")

    # Display columns
    display_cols = ['Score', 'Name', 'email', 'company', 'title', 'linkedin_url']
    display_df = priority_df[[col for col in display_cols if col in priority_df.columns]]

    priority_event = st.dataframe(
        display_df,
        column_config={
            "Score": st.column_config.TextColumn("Priority", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "email": st.column_config.TextColumn("Email", width="medium"),
            "company": st.column_config.TextColumn("Company", width="medium"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "linkedin_url": st.column_config.LinkColumn("LinkedIn", width="small")
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Email functionality for selected priority contact
    if len(priority_event.selection.rows) > 0:
        selected_row_index = priority_event.selection.rows[0]
        selected_contact = priority_df.iloc[selected_row_index]

        contact_email = selected_contact.get('email')
        contact_first_name = selected_contact.get('first_name', '') or ''
        contact_last_name = selected_contact.get('last_name', '') or ''
        contact_full_name = f"{contact_first_name} {contact_last_name}".strip() or contact_email.split('@')[0]

        if contact_email and st.button(f"✉️ Email {contact_full_name}"):
            @st.dialog(f"Email Thread: {contact_full_name}")
            def email_dialog(email_address, contact_name, first_name, last_name, contact_id):
                # Load email draft if available
                draft_subject, draft_body, has_draft, source = load_email_draft(first_name, last_name, email_address, contact_id, client)

                if has_draft:
                    if source == 'database':
                        st.success("📝 Email draft loaded from database")
                    else:
                        st.info("📝 Email draft loaded from outreach_emails/ (not yet saved to database)")

                # 1. Fetch History
                st.subheader("Previous Thread")
                with st.spinner("Fetching email history..."):
                    try:
                        # Search for emails to/from this address
                        search_results = client.execute_tool(
                            "mcp_Gmail_gmail_search_emails",
                            {"query": f"to:{email_address} OR from:{email_address}", "max_results": 5}
                        )

                        messages = []
                        if isinstance(search_results, list) and len(search_results) > 0:
                            # Extract emails from response dict
                            if isinstance(search_results[0], dict) and 'emails' in search_results[0]:
                                messages = search_results[0]['emails']
                            elif isinstance(search_results[0], list):
                                # Unwrap nested list if present
                                messages = search_results[0]
                            else:
                                messages = search_results

                        if messages and isinstance(messages, list):
                            for msg in messages:
                                if isinstance(msg, dict):
                                    msg_id = msg.get('id', 'Unknown ID')
                                    subject = msg.get('subject', '(No Subject)')
                                    sender = msg.get('from', 'Unknown Sender')
                                    date = msg.get('date', 'Unknown Date')
                                    snippet = msg.get('snippet', '') # Snippet might be available in some responses

                                    # Determine direction icon
                                    direction_icon = "📥"
                                    if email_address in sender:
                                        direction_icon = "📥" # Received from contact
                                    else:
                                        direction_icon = "📤" # Sent to contact (presumably)

                                    with st.expander(f"{direction_icon} {subject} - {date}"):
                                        st.markdown(f"**From:** {sender}")
                                        st.markdown(f"**Date:** {date}")
                                        if snippet:
                                            st.markdown(f"**Snippet:** {snippet}")
                                        st.caption(f"ID: {msg_id}")
                                else:
                                    st.text(str(msg))
                        elif not messages:
                            st.info("No previous emails found.")
                        else:
                             # Fallback for unexpected format
                             st.json(search_results)

                    except Exception as e:
                        st.warning(f"Could not fetch history: {e}")

                st.divider()

                # 2. Compose New Email
                st.subheader("Compose Email")
                subject = st.text_input("Subject", value=draft_subject, key=f"subject_{contact_id}")
                body = st.text_area("Message", value=draft_body, height=300, key=f"body_{contact_id}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("💾 Save Draft", key=f"save_{contact_id}"):
                        if save_email_draft(contact_id, subject, body, client):
                            st.success("Draft saved to database!")
                        else:
                            st.error("Failed to save draft")

                with col2:
                    if st.button("📤 Send Email", key=f"send_{contact_id}"):
                        if not subject or not body:
                            st.error("Please fill in both subject and message.")
                        else:
                            with st.spinner("Sending..."):
                                try:
                                    result = client.execute_tool(
                                        "mcp_Gmail_gmail_send_email",
                                        {
                                            "to": email_address,
                                            "subject": subject,
                                            "body": body
                                        }
                                    )
                                    st.success("Email sent successfully!")
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Error sending email: {e}")

            contact_id = selected_contact.get('id')
            email_dialog(contact_email, contact_full_name, contact_first_name, contact_last_name, contact_id)

    st.write("")  # Add spacing

    # Stats
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        hot_leads = len(priority_df[priority_df['priority_score'] >= 90])
        st.metric("🔥 Hot Leads (90+)", hot_leads)
    with col_b:
        high_priority = len(priority_df[priority_df['priority_score'] >= 75])
        st.metric("⭐ High Priority (75+)", high_priority)
    with col_c:
        avg_score = int(priority_df['priority_score'].mean())
        st.metric("📊 Avg Score", avg_score)
else:
    st.info("No priority contacts found. Run `python calculate_priority.py` to calculate scores.")

st.write("---")

if not st.session_state['crm_df'].empty:
    st.write("### CRM Records with Enrichment Status:")
    
    event = st.dataframe(
        st.session_state['crm_df'],
        on_select="rerun",
        selection_mode="single-row"
    )

    if len(event.selection.rows) > 0:
        selected_row_index = event.selection.rows[0]
        selected_record = st.session_state['crm_df'].iloc[selected_row_index]
        
        email = selected_record.get('email')
        first_name = selected_record.get('first_name', 'Contact')
        last_name = selected_record.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()

        if email and st.button(f"✉️ Email {full_name}"):
            @st.dialog(f"Email Thread: {full_name}")
            def email_dialog(email_address, contact_name, fname, lname, contact_id):
                # Load email draft if available
                draft_subject, draft_body, has_draft, source = load_email_draft(fname, lname, email_address, contact_id, client)

                if has_draft:
                    if source == 'database':
                        st.success("📝 Email draft loaded from database")
                    else:
                        st.info("📝 Email draft loaded from outreach_emails/ (not yet saved to database)")

                # 1. Fetch History
                st.subheader("Previous Thread")
                with st.spinner("Fetching email history..."):
                    try:
                        # Search for emails to/from this address
                        search_results = client.execute_tool(
                            "mcp_Gmail_gmail_search_emails",
                            {"query": f"to:{email_address} OR from:{email_address}", "max_results": 5}
                        )

                        messages = []
                        if isinstance(search_results, list) and len(search_results) > 0:
                            # Extract emails from response dict
                            if isinstance(search_results[0], dict) and 'emails' in search_results[0]:
                                messages = search_results[0]['emails']
                            elif isinstance(search_results[0], list):
                                # Unwrap nested list if present
                                messages = search_results[0]
                            else:
                                messages = search_results

                        if messages and isinstance(messages, list):
                            for msg in messages:
                                if isinstance(msg, dict):
                                    msg_id = msg.get('id', 'Unknown ID')
                                    subject = msg.get('subject', '(No Subject)')
                                    sender = msg.get('from', 'Unknown Sender')
                                    date = msg.get('date', 'Unknown Date')
                                    snippet = msg.get('snippet', '') # Snippet might be available in some responses

                                    # Determine direction icon
                                    direction_icon = "📥"
                                    if email_address in sender:
                                        direction_icon = "📥" # Received from contact
                                    else:
                                        direction_icon = "📤" # Sent to contact (presumably)

                                    with st.expander(f"{direction_icon} {subject} - {date}"):
                                        st.markdown(f"**From:** {sender}")
                                        st.markdown(f"**Date:** {date}")
                                        if snippet:
                                            st.markdown(f"**Snippet:** {snippet}")
                                        st.caption(f"ID: {msg_id}")
                                else:
                                    st.text(str(msg))
                        elif not messages:
                            st.info("No previous emails found.")
                        else:
                             # Fallback for unexpected format
                             st.json(search_results)

                    except Exception as e:
                        st.warning(f"Could not fetch history: {e}")

                st.divider()

                # 2. Compose New Email
                st.subheader("Compose Email")
                subject = st.text_input("Subject", value=draft_subject, key=f"subject_crm_{contact_id}")
                body = st.text_area("Message", value=draft_body, height=300, key=f"body_crm_{contact_id}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("💾 Save Draft", key=f"save_crm_{contact_id}"):
                        if save_email_draft(contact_id, subject, body, client):
                            st.success("Draft saved to database!")
                        else:
                            st.error("Failed to save draft")

                with col2:
                    if st.button("📤 Send Email", key=f"send_crm_{contact_id}"):
                        if not subject or not body:
                            st.error("Please fill in both subject and message.")
                        else:
                            with st.spinner("Sending..."):
                                try:
                                    result = client.execute_tool(
                                        "mcp_Gmail_gmail_send_email",
                                        {
                                            "to": email_address,
                                            "subject": subject,
                                            "body": body
                                        }
                                    )
                                    st.success("Email sent successfully!")
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Error sending email: {e}")

            record_id = selected_record.get('id')
            email_dialog(email, full_name, first_name, last_name, record_id)

else:
    st.info("No CRM records found or an error occurred.")

st.write("---")
st.write("### Enrichment Metrics:")

col1, col2, col3, col4 = st.columns(4)

total_records = len(st.session_state['crm_df'])
enriched_records = st.session_state['crm_df']['Enrichment Status'].value_counts().get('Enriched', 0)
not_enriched_records = st.session_state['crm_df']['Enrichment Status'].value_counts().get('Not Enriched', 0)
linkedin_fetched = st.session_state['crm_df']['LinkedIn Fetched'].sum() if 'LinkedIn Fetched' in st.session_state['crm_df'].columns else 0

with col1:
    st.metric("Total Records", total_records)
with col2:
    st.metric("Enriched Records", enriched_records)
with col3:
    st.metric("Not Enriched", not_enriched_records)
with col4:
    st.metric("LinkedIn Profiles Fetched", int(linkedin_fetched))

st.write("---")
st.write("### 🎯 Ideal Customer Profile (ICP) Summary:")
st.markdown("*Continuously updated as new LinkedIn profiles are fetched and analyzed*")

icp_content = get_icp_summary()
st.markdown(icp_content)
