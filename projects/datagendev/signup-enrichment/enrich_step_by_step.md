# Step-by-Step Guide: Finding LinkedIn Profiles for Recent Signups

## Overview
This guide documents the process of finding LinkedIn profiles for users who signed up in the last 2 weeks using DataGen tools.

---

## Step 1: Query Recent Signups from Database

**Tool:** `mcp_Neon_run_sql`

**Query:**
```sql
SELECT id, email, created_at, updated_at
FROM fastapi_user
WHERE created_at >= NOW() - INTERVAL '14 days'
ORDER BY created_at DESC
```

**Parameters:**
```json
{
  "params": {
    "sql": "<query>",
    "projectId": "rough-base-02149126",
    "databaseName": "datagen"
  }
}
```

**Expected Output:** List of users with id, email, and signup dates

---

## Step 2: Search LinkedIn Profiles Using Email

**Tool:** `mcp_Datagen__executeTool` with `search_linkedin_person`

**For each user email:**
```json
{
  "tool_alias_name": "search_linkedin_person",
  "parameters": {
    "email": "user@example.com"
  }
}
```

**Success Criteria:**
- Returns `person` object with LinkedIn profile data
- Contains `linkedInUrl` field

**Failure:**
- Returns "Resource not found" error
- Proceed to Step 3

---

## Step 3: Search Using Inferred Names (Fallback)

**If email search fails, extract name from email:**

**Patterns:**
- `firstname.lastname@domain.com` → firstName: "Firstname", lastName: "Lastname"
- `firstnamelastname@domain.com` → Try web search instead

**Tool:** Same `search_linkedin_person` but with name parameters:
```json
{
  "tool_alias_name": "search_linkedin_person",
  "parameters": {
    "firstName": "Mark",
    "lastName": "Grimes"
  }
}
```

---

## Step 4: Web Search Using Linkup (Second Fallback)

**Tool:** `mcp_Datagen__executeTool` with `mcp_Linkup_linkup_search`

**Query pattern:**
```json
{
  "tool_alias_name": "mcp_Linkup_linkup_search",
  "parameters": {
    "query": "email@example.com linkedin"
  }
}
```

**Parse Results:**
- Look for LinkedIn profile URLs in the returned results
- URLs typically follow pattern: `https://www.linkedin.com/in/username/`

---

## Step 5: Try Exa Search (Third Fallback)

**Tool:** `mcp_Datagen__executeTool` with `mcp_Exa_web_search_exa`

**Query:**
```json
{
  "tool_alias_name": "mcp_Exa_web_search_exa",
  "parameters": {
    "query": "email@example.com linkedin"
  }
}
```

**Note:** Exa returns structured results with titles and URLs. Look for LinkedIn profile links.

---

## Step 6: Update CRM Table with Findings

**First, ensure the `enrich_source` column exists:**

```sql
ALTER TABLE crm ADD COLUMN enrich_source VARCHAR(50)
```

**Update records with LinkedIn URLs and enrichment source:**

```sql
-- For direct email search matches (high confidence)
UPDATE crm
SET linkedin_url = 'https://www.linkedin.com/in/username/',
    enrich_source = 'direct_email'
WHERE email = 'user@example.com';

-- For name-based search matches (high confidence)
UPDATE crm
SET linkedin_url = 'https://www.linkedin.com/in/username/',
    enrich_source = 'direct_name'
WHERE email = 'user@example.com';

-- For Linkup web search matches (medium confidence)
UPDATE crm
SET linkedin_url = 'https://www.linkedin.com/in/username/',
    enrich_source = 'linkup_search'
WHERE email = 'user@example.com';

-- For Exa search matches (medium confidence)
UPDATE crm
SET linkedin_url = 'https://www.linkedin.com/in/username/',
    enrich_source = 'exa_search'
WHERE email = 'user@example.com';
```

**Enrich Source Values:**
- `direct_email` - Found via direct email search (highest confidence)
- `direct_name` - Found via name search (high confidence)
- `linkup_search` - Found via Linkup web search (medium confidence)
- `exa_search` - Found via Exa AI search (medium confidence)
- `manual` - Manually verified or added
- `NULL` - Not enriched yet

**Verify updates:**

```sql
SELECT email, linkedin_url, enrich_source
FROM crm
WHERE email IN ('user1@example.com', 'user2@example.com', 'user3@example.com')
```

---

## Step 7: Compile Results

**Create summary table:**

| ID | Email | LinkedIn Found | LinkedIn URL | Enrich Source |
|---|---|---|---|---|
| 115 | user1@example.com | ✅ Yes | https://linkedin.com/in/... | direct_email |
| 114 | user2@example.com | ✅ Yes | https://linkedin.com/in/... | linkup_search |
| 113 | user3@example.com | ❌ No | - | NULL |

---

## Key Learnings

1. **Direct email search has ~25% success rate** - Most people don't have their email publicly visible on LinkedIn

2. **Name-based search requires full names** - Partial names or usernames won't work well

3. **Web search tools find indirect matches** - Linkup and Exa can discover profiles through mentions, posts, or other web presence

4. **Don't over-infer** - If web search returns company pages or unrelated results, mark as "Not found" rather than guessing

5. **Business emails** - Emails like `nocodecanada@gmail.com` are likely organizations, not individuals

---

## Tools Used

- `mcp_Neon_run_sql` - Database queries
- `search_linkedin_person` - Direct LinkedIn profile search
- `mcp_Linkup_linkup_search` - Web search
- `mcp_Exa_web_search_exa` - AI-powered web search

---

## Success Rate

From our test:
- **Total users:** 4
- **Found via direct email search:** 1 (25%)
- **Found via web search:** 1 (25%)
- **Not found:** 2 (50%)
- **Overall success rate:** 50%
