# ICP Tracking Workflow

This document describes the complete workflow for tracking and analyzing Ideal Customer Profile (ICP) from DataGen user signups.

---

## Overview

The workflow uses an **incremental approach** with **agent-based analysis**:

1. **Fetch** only NEW LinkedIn profiles (not yet processed) using script
2. **Save** the latest batch to `linkedin_profiles_latest_batch.json` (overwrites each time)
3. **Agent analyzes** the batch and **appends** insights to `icp_profile.md`
4. **Track** processed profiles in the database using timestamps

**Key Benefits:**
- No duplicate profile fetching
- No growing local files (except cumulative ICP)
- Agent provides contextual analysis and insights
- Database-driven tracking

---

## Database Schema

### CRM Table Tracking Column

```sql
ALTER TABLE crm ADD COLUMN linkedin_profile_fetched_at TIMESTAMP;
```

This column tracks when a LinkedIn profile was fetched:
- `NULL` = Not yet fetched
- `TIMESTAMP` = Date/time when profile was successfully fetched

---

## Workflow Steps

### Step 1: Fetch New LinkedIn Profiles

**Script:** `fetch_linkedin_profiles.py`

**What it does:**
1. Queries CRM for records where `linkedin_profile_fetched_at IS NULL`
2. Fetches detailed LinkedIn profile data for each unfetched URL
3. Saves profiles to `linkedin_profiles_latest_batch.json` (overwrites previous batch)
4. Updates `linkedin_profile_fetched_at` timestamp in CRM for successfully fetched profiles

**Run:**
```bash
source venv/bin/activate
python fetch_linkedin_profiles.py
```

**Output:**
- `linkedin_profiles_latest_batch.json` - Contains ONLY the newly fetched profiles

**Example Output:**
```
Fetching new LinkedIn URLs from CRM (not yet processed)...
Found 3 NEW profiles to fetch

Fetching profile for user1@example.com...
  URL: https://www.linkedin.com/in/user1
  ✅ Profile fetched successfully
  ✅ Marked as fetched in CRM

✅ Saved 3 NEW profiles to linkedin_profiles_latest_batch.json
   Successfully fetched: 3
   Failed to fetch: 0

💡 Next step: Ask agent to analyze the batch and update icp_profile.md
```

**If no new profiles:**
```
✅ No new profiles to fetch. All profiles are up to date!
```

---

### Step 2: Agent Analyzes and Updates ICP

**Agent Task:** Read `linkedin_profiles_latest_batch.json` and update `icp_profile.md`

**User Prompt:**
```
Read the latest batch of LinkedIn profiles and update the ICP analysis
```

**What the agent does:**
1. Reads `linkedin_profiles_latest_batch.json`
2. Analyzes profiles for patterns:
   - Founders vs employees
   - Technical vs non-technical roles
   - Education levels
   - Geographic distribution
   - Skills and expertise
   - Company sizes and industries
3. Identifies insights and trends from the batch
4. **Appends** a timestamped section to `icp_profile.md` with:
   - Batch summary statistics
   - Key insights
   - Notable patterns
   - Profile references with LinkedIn URLs

**Output:**
- `icp_profile.md` updated with new batch analysis (appended, not overwritten)

---

## File Structure

```
signup-enrichment/
├── fetch_linkedin_profiles.py           # Step 1: Fetch new profiles
├── linkedin_profiles_latest_batch.json  # Latest batch (overwritten)
├── icp_profile.md                       # Cumulative ICP analysis (appended)
├── linkedin_profiles_full.json          # Legacy: First full batch
├── enrich_crm.py                        # Legacy: Enrich CRM
├── enrich_step_by_step.md               # Docs: Enrichment workflow
└── get_icp.md                           # This file: ICP workflow docs
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  CRM Database                                               │
│  ┌─────────────────────────────────────────────────┐       │
│  │ id | email | linkedin_url | linkedin_profile_  │       │
│  │    |       |              | fetched_at         │       │
│  ├────┼───────┼──────────────┼────────────────────┤       │
│  │ 1  | a@... | linkedin/... | 2025-11-28 10:00   │ ✅    │
│  │ 2  | b@... | linkedin/... | NULL               │ ⬅ NEW │
│  │ 3  | c@... | linkedin/... | NULL               │ ⬅ NEW │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ fetch_linkedin_profiles.py
                            │ (queries WHERE fetched_at IS NULL)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  linkedin_profiles_latest_batch.json (OVERWRITTEN)         │
│  {                                                          │
│    "batch_date": "2025-11-28T15:30:00",                    │
│    "profiles": [                                            │
│      { "email": "b@...", "profile": {...} },               │
│      { "email": "c@...", "profile": {...} }                │
│    ]                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ After fetch: UPDATE CRM
                            │ SET linkedin_profile_fetched_at = NOW()
                            │
                            │ AGENT: Read JSON, analyze, append
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  icp_profile.md (APPENDED BY AGENT)                        │
│                                                             │
│  # ICP Analysis                                            │
│  [Initial analysis from first batch]                       │
│  ...                                                        │
│  ---                                                        │
│  ## Update: 2025-11-28 15:35                               │
│  **New Profiles Added:** 2                                 │
│  - Founders: 1 (50%)                                       │
│  - Technical roles: 2 (100%)                               │
│  [Agent's contextual insights]                             │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow Example

### Initial Setup (First Time)

```bash
# 1. Fetch initial batch of profiles
source venv/bin/activate
python fetch_linkedin_profiles.py
```

Then tell the agent:
```
Read the latest batch and create the initial ICP analysis in icp_profile.md
```

---

### Weekly/Regular Updates

```bash
# 1. Fetch NEW profiles only
source venv/bin/activate
python fetch_linkedin_profiles.py
```

If new profiles were found, tell the agent:
```
Read the latest batch of LinkedIn profiles and update the ICP analysis
```

---

## Agent Analysis Guidelines

When analyzing batches, the agent should:

### 📊 Quantitative Analysis
- Count founders, technical roles, education levels
- Geographic distribution
- Company sizes and types
- Skills frequency

### 💡 Qualitative Insights
- Career trajectory patterns
- Industry trends
- Use case signals (what problems they might be solving)
- Buying behavior indicators

### 📝 Documentation Format - REQUIRED PATTERN

**IMPORTANT:** Every batch update MUST follow this exact structure to maintain consistency in `icp_profile.md`:

```markdown
---

## Update: YYYY-MM-DD HH:MM

**New Profiles Added:** [Number]
**Batch Date:** [ISO timestamp from JSON]

### Batch Summary

- **Founders/CEOs:** X (XX%)
- **Technical Roles:** X (XX%)
- **Advanced Degrees:** X (XX%)
- **Geographic Breakdown:** [Primary locations]

### Key Insights

[2-4 bullet points with notable patterns, trends, or surprises in this batch]
- Pattern 1: Description
- Pattern 2: Description
- Pattern 3: Description

### Batch Patterns

**Top Locations:**
- Location 1: X profiles
- Location 2: X profiles
- Location 3: X profiles

**Top Skills (appearing in 2+ profiles):**
- Skill 1: X profiles
- Skill 2: X profiles
- Skill 3: X profiles
...

**Top Companies:**
- Company 1: X profiles
- Company 2: X profiles
...

**Common Titles/Roles:**
- Title 1: X profiles
- Title 2: X profiles
...

### Notable Profiles

[Highlight 2-3 particularly interesting profiles from this batch with context]

**[Name]** - [Title] @ [Company]
- LinkedIn: [URL]
- Notable: [What makes this profile interesting - e.g., "Ex-FAANG founder building AI tools", "Leading community of 5k+ members"]
- Skills: [Top relevant skills]

### Use Case Signals

[What problems are these users likely trying to solve? What use cases do their backgrounds suggest?]
- Use case 1: [% or count] profiles
- Use case 2: [% or count] profiles

### New Profiles List

1. **[First Last]** - [Headline]
   - LinkedIn: [URL]
   - Company: [Company]
   - Location: [Location]

2. **[First Last]** - [Headline]
   - LinkedIn: [URL]
   - Company: [Company]
   - Location: [Location]

[Continue for all profiles in batch]
```

### Analysis Tips

1. **Compare to Previous Batches:** Reference trends from earlier updates
2. **Highlight Changes:** Note if this batch differs from typical patterns
3. **Be Specific:** Use concrete numbers and examples
4. **Add Context:** Explain why patterns matter for DataGen's GTM strategy
5. **Link Profiles:** Always include clickable LinkedIn URLs
6. **Flag Outliers:** Mention unusual or unexpected profiles

### Example Good Insights

✅ "This batch shows 75% technical roles vs 50% historical average - strong signal for developer-focused messaging"

✅ "First batch with 2+ Clay users - indicates our integration messaging is working"

✅ "Geographic shift: 60% international vs 30% historical - consider timezone coverage for support"

❌ "Some people are technical" (too vague)

❌ "Users are from various companies" (not insightful)

---

## Key Design Decisions

### ✅ Why Agent-Based Analysis?
- **Contextual understanding:** Agent can spot nuanced patterns
- **Flexible insights:** Not limited to predefined metrics
- **Natural language:** Easy-to-read analysis vs rigid stats
- **Adaptive:** Can adjust analysis based on emerging patterns

### ✅ Why Database Tracking?
- **Single source of truth:** CRM database controls what's been processed
- **No file sync issues:** Deleting JSON files won't cause re-processing
- **Query flexibility:** Easy to see processed vs unprocessed profiles

### ✅ Why Overwrite Batch File?
- **No file growth:** `linkedin_profiles_latest_batch.json` stays small
- **Clear intent:** Always contains the "latest" batch being analyzed
- **Temporary storage:** Acts as intermediate data for agent analysis

### ✅ Why Append to ICP?
- **Historical context:** See how ICP evolves over time
- **Timestamped insights:** Each batch analysis is dated
- **Cumulative learning:** Build understanding incrementally

---

## Troubleshooting

### "No new profiles to fetch"
✅ This is normal! It means all LinkedIn URLs in CRM have been processed.

### Want to re-fetch a profile?
```sql
-- Clear the timestamp to mark as unfetched
UPDATE crm
SET linkedin_profile_fetched_at = NULL
WHERE email = 'user@example.com';
```

### Want to see which profiles have been fetched?
```sql
SELECT email, linkedin_url, linkedin_profile_fetched_at
FROM crm
WHERE linkedin_profile_fetched_at IS NOT NULL
ORDER BY linkedin_profile_fetched_at DESC;
```

### Want to count unfetched profiles?
```sql
SELECT COUNT(*)
FROM crm
WHERE linkedin_url IS NOT NULL
  AND linkedin_url != ''
  AND linkedin_profile_fetched_at IS NULL;
```

---

## Priority Scoring Workflow

### Overview

Automatically calculate and track priority scores for daily contact outreach based on signup recency.

**Key Features:**
- **Recency-based scoring:** 100 points for new signups, decays 5 points/day
- **Daily recalculation:** Scores update automatically to reflect aging
- **Top 10 contacts:** Quick view of highest priority contacts each morning
- **Database-driven:** Scores stored in CRM for fast queries

### Database Schema

The priority scoring system uses two new columns in the CRM table:

```sql
-- Already added to your CRM table
priority_score INTEGER DEFAULT 0           -- Score 0-100 (higher = more priority)
priority_calculated_at TIMESTAMP           -- Last calculation timestamp
```

### Scoring Formula

```
priority_score = 100 - (days_since_signup × 5)
Minimum: 0
Maximum: 100
```

**Examples:**
- Signed up today: 100 points 🔥
- Signed up yesterday: 95 points ⭐
- Signed up 7 days ago: 65 points ✓
- Signed up 20+ days ago: 0 points (expired)

### Daily Workflow

**Morning Routine:**

```bash
# 1. Recalculate all priority scores (run daily)
source venv/bin/activate
python calculate_priority.py

# 2. View your top 10 contacts for today
python get_daily_contacts.py
```

**Example Output:**

```
📋 Top 10 Priority Contacts for 2025-11-29
======================================================================

1. 🔥 [Score: 98] Jacob Dietle
   Context Operating Systems for GTM @ Taste Systems
   📧 jacob@jdietle.me
   🔗 https://www.linkedin.com/in/jacob-dietle
   📅 Signed up: 2 hours ago

2. 🔥 [Score: 96] Miska Kaskinen
   Co-Founder @ SwiftDial.ai | Clay Creator
   📧 miska@swiftdial.ai
   🔗 https://www.linkedin.com/in/miskakaskinen
   📅 Signed up: 16 hours ago
...
```

### Scripts

#### `calculate_priority.py`

Calculate and update priority scores for all CRM contacts.

**Options:**
```bash
# Normal run (updates database)
python calculate_priority.py

# Dry run (preview without updating)
python calculate_priority.py --dry-run

# Custom decay factor (default: 5)
python calculate_priority.py --decay-factor 3
```

**Output:**
- Progress bar showing calculation status
- Score distribution summary
- Total contacts processed

#### `get_daily_contacts.py`

View your top priority contacts.

**Options:**
```bash
# Top 10 (default)
python get_daily_contacts.py

# Top 20
python get_daily_contacts.py --limit 20

# Only high-priority (score > 75)
python get_daily_contacts.py --min-score 75

# Show all details
python get_daily_contacts.py --all

# Export to CSV
python get_daily_contacts.py --export daily_contacts.csv
```

### Direct SQL Queries

**Top 10 contacts:**
```sql
SELECT id, email, company, title, priority_score, created_at
FROM crm
WHERE priority_score > 0
ORDER BY priority_score DESC, created_at DESC
LIMIT 10;
```

**High-priority contacts (score > 75):**
```sql
SELECT id, email, company, title, priority_score
FROM crm
WHERE priority_score > 75
ORDER BY priority_score DESC;
```

**Recent signups (last 24 hours):**
```sql
SELECT id, email, priority_score, created_at
FROM crm
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY priority_score DESC;
```

### Automation (Optional)

Set up a cron job to run calculations daily:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 8 AM daily)
0 8 * * * cd /Users/yu-shengkuo/projects/datagendev/signup-enrichment && source venv/bin/activate && python calculate_priority.py
```

### Adjusting the Decay Factor

The default decay factor is **5 points/day**, keeping contacts relevant for ~20 days.

**To adjust:**
```bash
# Faster decay (10 points/day = 10 day window)
python calculate_priority.py --decay-factor 10

# Slower decay (3 points/day = 33 day window)
python calculate_priority.py --decay-factor 3
```

### Integration with ICP Analysis

Priority scores complement the ICP analysis:

1. **Morning:** Run `calculate_priority.py` → Get top 10 contacts
2. **Research:** Check their ICP profile in `icp_profile.md`
3. **Outreach:** Personalize messaging based on ICP insights
4. **Weekly:** Review `icp_profile.md` for patterns and trends

---

## Summary

**Simple workflow with agent intelligence:**

1. **Script:** `fetch_linkedin_profiles.py` - Fetch NEW profiles, mark as processed
2. **Agent:** Read JSON, analyze patterns, append insights to `icp_profile.md`
3. **Script:** `calculate_priority.py` - Calculate priority scores for daily outreach
4. **Script:** `get_daily_contacts.py` - View top 10 contacts to contact today

**No duplicates. No file bloat. Intelligent, contextual insights with actionable priorities.**

---

## Quick Reference for Agent

### User Prompt to Trigger Analysis:
```
Read the latest batch of LinkedIn profiles and update the ICP analysis
```

### Agent Checklist:
- [ ] Read `linkedin_profiles_latest_batch.json`
- [ ] Extract batch metadata (date, count)
- [ ] Analyze all profiles for patterns
- [ ] Follow the **REQUIRED PATTERN** template exactly
- [ ] Include all sections: Summary, Insights, Patterns, Notable Profiles, Use Cases, Full List
- [ ] Append (not overwrite) to `icp_profile.md`
- [ ] Use specific numbers and percentages
- [ ] Compare to historical trends if multiple batches exist
- [ ] Include clickable LinkedIn URLs for all profiles

### Data to Extract from Each Profile:
```python
profile.get('firstName'), profile.get('lastName')
profile.get('headline')
profile.get('location')
profile.get('positions', {}).get('positionHistory', [])[0]  # Current role
profile.get('schools', {}).get('educationHistory', [])
profile.get('skills', [])
profile.get('followerCount')
```

### Pattern Template Location:
See section: **📝 Documentation Format - REQUIRED PATTERN** above
