from datagen_sdk import DatagenClient

client = DatagenClient(base_url="http://localhost:3001")
projects = client.execute_tool("mcp_Linear_list_projects", {"limit": 20})

print(f"Projects returned: {len(projects[0]['content']) if projects else 0}")
for proj in projects[0]["content"]:
    print(f"- {proj.get('name')} (id: {proj.get('id')}) status: {proj.get('status', {}).get('name') if isinstance(proj.get('status'), dict) else proj.get('status')}")
