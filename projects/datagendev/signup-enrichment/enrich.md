# Daily Signup Enrichment Workflow

**Role:** Data Enrichment Specialist
**Objective:** Enrich new user signups from the past week who are missing LinkedIn profiles, populate their data, and refine the Ideal Customer Profile (ICP).

## Prerequisites
- **Database:** Neon Postgres
- **Tools:**
  - `mcp_Neon_run_sql`
  - `search_linkedin_person` (Datagen)
  - `mcp_Linkup_search` (Linkup - *Verify tool alias via `searchTools` if needed*)
  - `mcp_Exa_web_search_exa` (Exa)
  - `get_linkedin_person_data` (Datagen)

## Workflow Steps

### 1. Identify Target Users
First, retrieve users who signed up recently and are missing enrichment data.

**Tool:** `mcp_Neon_run_sql`
**Instruction:** Select users from the past 7 days with no LinkedIn URL.

**Example Input:**
```json
{
  "tool_alias_name": "mcp_Neon_run_sql",
  "parameters": {
    "sql": "SELECT id, email, first_name, last_name, company FROM crm WHERE created_at >= NOW() - INTERVAL '7 days' AND linkedin_url IS NULL LIMIT 20;",
    "projectId": "rough-base-02149126",
    "databaseName": "datagen"
  }
}
```

### 2. Cascading Enrichment (Per User)
For each user row returned, apply the following waterfall logic:

#### Step 2.1: Datagen Direct Search
Attempt to find the person using Datagen's native LinkedIn search.

**Tool:** `search_linkedin_person`
**Condition:** Try this first.

**Example Input:**
```json
{
  "tool_alias_name": "search_linkedin_person",
  "parameters": {
    "email": "john.doe@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "companyName": "Acme Corp" 
  }
}
```
**Success Criteria:** If the response contains a `person` object with a `linkedInUrl`.
**Action:** If found, save URL and skip to **Step 3**. If not, proceed to **Step 2.2**.

#### Step 2.2: Linkup Search (Fallback #1)
If Datagen search fails, search the web using Linkup for a LinkedIn profile.

**Tool:** `mcp_Linkup_search`
**Condition:** Only if Step 2.1 failed.

**Example Input:**
```json
{
  "tool_alias_name": "mcp_Linkup_search",
  "parameters": {
    "query": "John Doe Acme Corp site:linkedin.com/in/",
    "depth": "standard",
    "output_type": "searchResults"
  }
}
```
**Success Criteria:** Look for a result where the URL starts with `https://www.linkedin.com/in/`.
**Action:** If a valid profile URL is found, save it and skip to **Step 3**. If not, proceed to **Step 2.3**.

#### Step 2.3: Exa Search (Fallback #2)
If Linkup fails, use Exa's neural search capabilities.

**Tool:** `mcp_Exa_web_search_exa`
**Condition:** Only if Step 2.2 failed.

**Example Input:**
```json
{
  "tool_alias_name": "mcp_Exa_web_search_exa",
  "parameters": {
    "query": "linkedin profile for John Doe at Acme Corp",
    "num_results": 1,
    "use_autoprompt": true
  }
}
```
**Success Criteria:** Check the `url` field of the first result.
**Action:** If it matches a LinkedIn profile pattern, save it and proceed to **Step 3**. If this also fails, mark the user as "Not Found" and move to the next record.

### 3. Deep Profile Enrichment & Update
Once a valid `linkedin_url` is identified (from any step above), fetch the full profile details to enrich the CRM.

#### 3.1 Fetch Profile Data
**Tool:** `get_linkedin_person_data`

**Example Input:**
```json
{
  "tool_alias_name": "get_linkedin_person_data",
  "parameters": {
    "linkedin_url": "https://www.linkedin.com/in/johndoe123"
  }
}
```

#### 3.2 Update Database
Update the CRM record with the new details.

**Tool:** `mcp_Neon_run_sql`

**Example Input:**
```json
{
  "tool_alias_name": "mcp_Neon_run_sql",
  "parameters": {
    "sql": "UPDATE crm SET linkedin_url = 'https://www.linkedin.com/in/johndoe123', title = 'Senior Engineer', company = 'Acme Corp', industry = 'Software Development', location = 'San Francisco, CA' WHERE id = 123;",
    "projectId": "rough-base-02149126",
    "databaseName": "datagen"
  }
}
```

### 4. ICP Refinement
After the batch is processed, analyze the newly enriched roles and industries.

**Task:** Read `icp.md`, append new insights, and save.

**Tool:** `read_file` (to read `icp.md`)
**Tool:** `write_file` (to overwrite `icp.md` with new content)

**Update Logic:**
1.  **Check Titles:** Did we sign up more "Founders" or "Engineers" today?
2.  **Check Industries:** Are we seeing a trend in "Healthcare" or "Fintech"?
3.  **Append Entry:**

**Example `icp.md` Update:**
```markdown
## Update: 2025-11-28
- **New Signups:** 5 enriched.
- **Top Roles:** 3 CTOs, 2 Product Managers.
- **Top Industries:** B2B SaaS.
- **Observation:** High traction with technical decision-makers in early-stage startups.
```