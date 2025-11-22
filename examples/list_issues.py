from datagen_sdk import DatagenClient

client = DatagenClient(base_url="http://localhost:3001")
issues = client.execute_tool(
    "mcp_Linear_list_issues",
    {
        "limit": 10,
        "order_by": "createdAt",
        "order_direction": "DESC",
    },
)

# The tool returns a list with the first element containing a list of issues
# Adjust if the schema changes.
issue_block = issues[0] if issues else []
print(f"Issues returned: {len(issue_block)}")
for issue in issue_block:
    ident = issue.get("identifier", "?")
    title = issue.get("title", "(no title)")
    status = issue.get("status") if isinstance(issue.get("status"), str) else issue.get("status", {}).get("name")
    created = issue.get("createdAt")
    print(f"- {ident}: {title} [status: {status}] created: {created}")
