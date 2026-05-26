from src.mcp_client import MCPClient

client = MCPClient()

print("\nHEALTH indirecto: usando herramientas MCP\n")

print("User risk:")
print(client.get_user_risk("jperez@empresa.com"))

print("\nAlerts:")
print(client.search_recent_alerts("jperez phishing sospechoso"))

print("\nTicket:")
print(client.create_incident_ticket(
    summary="Usuario hizo clic en enlace sospechoso",
    severity="alta"
))