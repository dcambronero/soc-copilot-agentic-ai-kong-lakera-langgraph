import requests

from src.config import MCP_SERVER_URL


class MCPClient:
    def __init__(self):
        self.base_url = MCP_SERVER_URL

    def get_asset_info(self, asset_name: str) -> dict:
        response = requests.get(
            f"{self.base_url}/asset/{asset_name}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_user_risk(self, user_email: str) -> dict:
        response = requests.get(
            f"{self.base_url}/user-risk/{user_email}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def search_recent_alerts(self, indicator: str) -> dict:
        response = requests.get(
            f"{self.base_url}/alerts",
            params={"indicator": indicator},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def create_incident_ticket(self, summary: str, severity: str) -> dict:
        response = requests.post(
            f"{self.base_url}/tickets",
            json={
                "summary": summary,
                "severity": severity
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()