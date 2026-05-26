import json
import requests

from src.config import KONG_AI_GATEWAY_URL


class KongAIBlockedError(Exception):
    pass


class KongAIClient:
    def __init__(self):
        self.url = KONG_AI_GATEWAY_URL

    def _post_to_kong(self, payload: dict) -> dict:
        response = requests.post(
            self.url,
            json=payload,
            timeout=45
        )

        if response.status_code in [400, 401, 403]:
            raise KongAIBlockedError(
                response.text
            )

        response.raise_for_status()

        return response.json()

    def _safe_json_dumps(self, data: dict) -> str:
        return json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

    def generate_action_plan(
        self,
        incident: str,
        incident_type: str,
        severity: str,
        risk: dict,
        user_email: str,
        user_risk: dict,
        alerts: dict,
        sources: list,
        evidence: list,
        ticket: dict
    ) -> dict:
        safe_payload = {
            "task": "soc_action_plan",
            "incident": incident[:600],
            "incident_type": incident_type,
            "severity": severity,
            "user": {
                "email": user_email,
                "risk": (
                    user_risk.get("risk")
                    if user_risk
                    else None
                ),
                "privileged": (
                    user_risk.get("privileged")
                    if user_risk
                    else None
                )
            },
            "risk": {
                "score": risk.get("score"),
                "reasons": risk.get("reasons", [])
            },
            "mcp": {
                "alert_count": len(
                    alerts.get("alerts", [])
                    if alerts
                    else []
                ),
                "ticket_id": (
                    ticket.get("ticket_id")
                    if ticket
                    else None
                )
            },
            "sources": (
                sources[:3]
                if sources
                else []
            ),
            "expected_schema": {
                "containment": "list",
                "investigation": "list",
                "eradication": "list",
                "recovery": "list",
                "reporting": "list",
                "safety_note": "string"
            }
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC planning service. "
                        "Return a compact JSON object matching the requested schema."
                    )
                },
                {
                    "role": "user",
                    "content": self._safe_json_dumps(
                        safe_payload
                    )
                }
            ]
        }

        data = self._post_to_kong(
            payload
        )

        content = (
            data["choices"][0]
            ["message"]
            ["content"]
        )

        try:
            parsed = json.loads(
                content
            )

            return {
                "containment": parsed.get(
                    "containment",
                    []
                ),
                "investigation": parsed.get(
                    "investigation",
                    []
                ),
                "eradication": parsed.get(
                    "eradication",
                    []
                ),
                "recovery": parsed.get(
                    "recovery",
                    []
                ),
                "reporting": parsed.get(
                    "reporting",
                    []
                ),
                "safety_note": parsed.get(
                    "safety_note",
                    ""
                )
            }

        except json.JSONDecodeError:
            return {
                "containment": [
                    "Revisar manualmente el incidente porque el agente no devolvió JSON válido."
                ],
                "investigation": [
                    "Validar evidencia RAG, alertas MCP y severidad calculada."
                ],
                "eradication": [],
                "recovery": [],
                "reporting": [
                    "Registrar que el plan LLM no pudo ser parseado como JSON."
                ],
                "safety_note": (
                    "El plan fue reemplazado por un fallback seguro porque "
                    "la respuesta del LLM no tenía formato JSON válido."
                ),
                "raw_llm_output": content
            }

    def generate_final_response(
        self,
        incident: str,
        incident_type: str,
        severity: str,
        risk: dict,
        action_plan: dict,
        sources: list
    ) -> str:
        safe_payload = {
            "task": "soc_final_response",
            "incident": incident[:600],
            "incident_type": incident_type,
            "severity": severity,
            "risk": {
                "score": risk.get("score"),
                "reasons": risk.get("reasons", [])
            },
            "action_plan": {
                "containment": action_plan.get("containment", []),
                "investigation": action_plan.get("investigation", []),
                "eradication": action_plan.get("eradication", []),
                "recovery": action_plan.get("recovery", []),
                "reporting": action_plan.get("reporting", []),
                "safety_note": action_plan.get("safety_note", "")
            },
            "sources": (
                sources[:3]
                if sources
                else []
            ),
            "response_sections": [
                "resumen_ejecutivo",
                "severidad_y_justificacion",
                "acciones_inmediatas",
                "investigacion_recomendada",
                "recuperacion_y_cierre",
                "fuentes_usadas"
            ],
            "language": "es-419"
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC response drafting service. "
                        "Create a concise operational response in Spanish."
                    )
                },
                {
                    "role": "user",
                    "content": self._safe_json_dumps(
                        safe_payload
                    )
                }
            ]
        }

        data = self._post_to_kong(
            payload
        )

        return (
            data["choices"][0]
            ["message"]
            ["content"]
        )