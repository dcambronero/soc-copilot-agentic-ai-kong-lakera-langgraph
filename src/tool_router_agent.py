import json
import re

from src.kong_client import (
    KongAIClient,
    KongAIBlockedError
)


class ToolRouterAgent:
    """
    Agente LLM que decide qué herramientas MCP usar.

    Si Kong/Lakera bloquea el router, cae a fallback
    determinístico para mantener continuidad del lab.
    """

    def __init__(self):
        self.kong = KongAIClient()

    def decide_tools(
        self,
        incident: str,
        incident_type: str,
        known_facts: list
    ) -> dict:
        try:
            return self._decide_with_llm(
                incident=incident,
                incident_type=incident_type,
                known_facts=known_facts
            )

        except Exception:
            return self._fallback_decision(
                incident=incident
            )

    def _decide_with_llm(
        self,
        incident: str,
        incident_type: str,
        known_facts: list
    ) -> dict:
        safe_payload = {
            "task": "select_mcp_tools",
            "incident": incident[:600],
            "incident_type": incident_type,
            "known_facts": known_facts[:5],
            "available_tools": [
                {
                    "tool_name": "get_user_risk",
                    "required_argument": "user_email"
                },
                {
                    "tool_name": "get_asset_info",
                    "required_argument": "asset_name"
                },
                {
                    "tool_name": "search_recent_alerts",
                    "required_argument": "indicator"
                }
            ],
            "output_schema": {
                "tool_calls": [
                    {
                        "tool_name": "string",
                        "arguments": "object",
                        "reason": "string"
                    }
                ]
            }
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC tool routing service. "
                        "Return compact JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        safe_payload,
                        ensure_ascii=False
                    )
                }
            ]
        }

        data = self.kong._post_to_kong(
            payload
        )

        content = (
            data["choices"][0]
            ["message"]
            ["content"]
        )

        parsed = self._safe_json_loads(
            content
        )

        return {
            "mode": "llm_via_kong",
            "tool_calls": parsed.get(
                "tool_calls",
                []
            )
        }

    def _fallback_decision(
        self,
        incident: str
    ) -> dict:
        tool_calls = []

        email = self._extract_email(
            incident
        )

        asset = self._extract_asset(
            incident
        )

        indicator = self._extract_indicator(
            incident
        )

        if email:
            tool_calls.append({
                "tool_name": "get_user_risk",
                "arguments": {
                    "user_email": email
                },
                "reason": (
                    "Se detectó un correo de usuario en el incidente."
                )
            })

        if asset:
            tool_calls.append({
                "tool_name": "get_asset_info",
                "arguments": {
                    "asset_name": asset
                },
                "reason": (
                    "Se detectó un activo conocido en el incidente."
                )
            })

        if indicator:
            tool_calls.append({
                "tool_name": "search_recent_alerts",
                "arguments": {
                    "indicator": indicator
                },
                "reason": (
                    "Se detectó un indicador o tipo de amenaza."
                )
            })

        if not indicator:
            tool_calls.append({
                "tool_name": "search_recent_alerts",
                "arguments": {
                    "indicator": incident[:120]
                },
                "reason": (
                    "Se usa el texto del incidente como indicador general."
                )
            })

        return {
            "mode": "fallback_rules",
            "tool_calls": tool_calls
        }

    def _safe_json_loads(
        self,
        content: str
    ) -> dict:
        try:
            return json.loads(
                content
            )

        except json.JSONDecodeError:
            cleaned = (
                content
                .strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            return json.loads(
                cleaned
            )

    def _extract_email(
        self,
        text: str
    ):
        match = re.search(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            text
        )

        if match:
            return match.group(
                0
            )

        return None

    def _extract_asset(
        self,
        text: str
    ):
        lowered = text.lower()

        known_assets = [
            "laptop-jperez",
            "srv-finanzas-01"
        ]

        for asset in known_assets:
            if asset in lowered:
                return asset

        return None

    def _extract_indicator(
        self,
        text: str
    ):
        lowered = text.lower()

        if "phishing" in lowered:
            return "phishing"

        if "ransomware" in lowered:
            return "ransomware"

        if "sospechoso" in lowered:
            return "sospechoso"

        if "cifrado" in lowered:
            return "ransomware"

        return None