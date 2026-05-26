import json

from src.kong_client import (
    KongAIClient,
    KongAIBlockedError
)


class ReviewerAgent:
    """
    Reviewer Agent.

    Revisa el plan generado por el Action Planner antes
    de producir la respuesta final.

    Evalúa:
    - cobertura del plan
    - coherencia con severidad
    - escalamiento
    - evidencia
    - seguridad operativa
    """

    def __init__(self):
        self.kong = KongAIClient()

    def review_plan(
        self,
        incident: str,
        incident_type: str,
        severity: str,
        risk: dict,
        action_plan: dict,
        sources: list,
        critical_escalation: dict
    ) -> dict:
        try:
            return self._review_with_llm(
                incident=incident,
                incident_type=incident_type,
                severity=severity,
                risk=risk,
                action_plan=action_plan,
                sources=sources,
                critical_escalation=critical_escalation
            )

        except Exception as error:
            return self._fallback_review(
                error=str(error),
                severity=severity,
                action_plan=action_plan
            )

    def _review_with_llm(
        self,
        incident: str,
        incident_type: str,
        severity: str,
        risk: dict,
        action_plan: dict,
        sources: list,
        critical_escalation: dict
    ) -> dict:
        safe_payload = {
            "task": "review_soc_action_plan",
            "incident": incident[:600],
            "incident_type": incident_type,
            "severity": severity,
            "risk": {
                "score": risk.get(
                    "score"
                ),
                "reasons": risk.get(
                    "reasons",
                    []
                )
            },
            "action_plan": {
                "containment": action_plan.get(
                    "containment",
                    []
                ),
                "investigation": action_plan.get(
                    "investigation",
                    []
                ),
                "eradication": action_plan.get(
                    "eradication",
                    []
                ),
                "recovery": action_plan.get(
                    "recovery",
                    []
                ),
                "reporting": action_plan.get(
                    "reporting",
                    []
                ),
                "safety_note": action_plan.get(
                    "safety_note",
                    ""
                )
            },
            "sources": sources[:3] if sources else [],
            "critical_escalation": {
                "required": critical_escalation.get(
                    "required",
                    False
                ),
                "sla": critical_escalation.get(
                    "sla"
                )
            },
            "expected_schema": {
                "decision": "approve | revise",
                "review_score": "integer 1-10",
                "findings": "list",
                "recommended_improvements": "list",
                "safety_notes": "list"
            }
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC plan review service. "
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

        decision = parsed.get(
            "decision",
            "approve"
        )

        if decision not in [
            "approve",
            "revise"
        ]:
            decision = "approve"

        return {
            "mode": "llm_via_kong",
            "decision": decision,
            "review_score": parsed.get(
                "review_score",
                7
            ),
            "findings": parsed.get(
                "findings",
                []
            ),
            "recommended_improvements": parsed.get(
                "recommended_improvements",
                []
            ),
            "safety_notes": parsed.get(
                "safety_notes",
                []
            )
        }

    def _fallback_review(
        self,
        error: str,
        severity: str,
        action_plan: dict
    ) -> dict:
        findings = []

        if severity == "Crítica":
            reporting = action_plan.get(
                "reporting",
                []
            )

            has_escalation = any(
                "escal" in item.lower()
                for item in reporting
            )

            if not has_escalation:
                findings.append(
                    "El plan crítico no menciona escalamiento explícito."
                )

        return {
            "mode": "fallback_rules",
            "decision": "approve",
            "review_score": 6,
            "findings": findings,
            "recommended_improvements": [
                "Validar manualmente el plan por bloqueo o error del Reviewer LLM."
            ],
            "safety_notes": [
                "No se realizaron acciones automáticas.",
                f"Fallback activado por: {error[:300]}"
            ]
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