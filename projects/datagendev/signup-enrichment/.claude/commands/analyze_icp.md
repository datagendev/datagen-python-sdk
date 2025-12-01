# Analyze ICP Batch

You are analyzing a batch of LinkedIn profiles to update the ICP (Ideal Customer Profile) analysis.

## Your Task

1. **Read the latest batch**: Read `linkedin_profiles_latest_batch.json`
2. **Analyze patterns**: Extract insights following the guidelines below
3. **Update ICP file**: Append analysis to `icp_profile.md` using the REQUIRED PATTERN

## Required Analysis Sections

### 📊 Quantitative Analysis
- Count founders vs employees
- Technical vs non-technical roles
- Education levels (especially advanced degrees)
- Geographic distribution
- Company sizes and industries
- Skills frequency

### 💡 Qualitative Insights
- Career trajectory patterns
- Industry trends
- Use case signals (what problems they might be solving)
- Buying behavior indicators

## REQUIRED PATTERN - Follow Exactly

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

## Data Extraction Guide

From each profile in the JSON, extract:
- `firstName`, `lastName`
- `headline`
- `location`
- `positions.positionHistory[0]` (current role)
- `schools.educationHistory[]`
- `skills[]`
- `followerCount`

## Analysis Best Practices

1. **Compare to Previous Batches**: Reference trends from earlier updates in `icp_profile.md`
2. **Highlight Changes**: Note if this batch differs from typical patterns
3. **Be Specific**: Use concrete numbers and percentages
4. **Add Context**: Explain why patterns matter for DataGen's GTM strategy
5. **Link Profiles**: Always include clickable LinkedIn URLs
6. **Flag Outliers**: Mention unusual or unexpected profiles

## Example Good Insights

✅ "This batch shows 75% technical roles vs 50% historical average - strong signal for developer-focused messaging"

✅ "First batch with 2+ Clay users - indicates our integration messaging is working"

✅ "Geographic shift: 60% international vs 30% historical - consider timezone coverage for support"

❌ "Some people are technical" (too vague)

❌ "Users are from various companies" (not insightful)

## Important Notes

- **APPEND, don't overwrite**: Add new analysis to the end of `icp_profile.md`
- **Use exact timestamp**: Get current date/time for the update header
- **Follow the pattern exactly**: Don't skip sections
- **Include all profiles**: Every profile should appear in the "New Profiles List"
- **Make it actionable**: Insights should inform DataGen's GTM strategy

Now proceed to analyze the batch!
