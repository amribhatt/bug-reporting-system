import database

db = database.IncidentDatabase()
incidents = db.get_incidents_for_user('user1')

print("Recent incidents:")
for inc in incidents[-10:]:
    level = inc.get('level', 'N/A')
    print(f"ID: {inc['id']}, Level: {level}, Category: {inc['category']}, Description: {inc['description'][:50]}...")

print(f"\nTotal incidents: {len(incidents)}")

# Also check if Guard Agent has the update method
try:
    from guard_agent.agent import GuardAgent
    guard = GuardAgent()
    print("\nGuard Agent tools:")
    for tool in guard.get_tools():
        print(f"- {tool.__name__}")
except Exception as e:
    print(f"\nError checking Guard Agent: {e}") 