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

    def _extract_content(self, data: dict) -> str:
        return (
            data["choices"][0]
            ["message"]
            ["content"]
        )

    def _safe_json_loads(self, content: str) -> dict:
        try:
            return json.loads(content)

        except json.JSONDecodeError:
            cleaned = (
                content
                .strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            return json.loads(cleaned)

    def _contains_guardrail_terms(self, text: str) -> bool:
        lowered = str(text).lower()

        blocked_terms = [
            "lakera",
            "guardrail",
            "guardrails",
            "kong/lakera",
            "kong",
            "bloqueado",
            "bloqueó",
            "blocked",
            "prompt",
            "jailbreak",
            "bypass",
            "política",
            "policy",
            "runtime",
            "solicitud",
            "api"
        ]

        return any(
            term in lowered
            for term in blocked_terms
        )

    def _sanitize_text_for_llm(self, text: str, max_len: int = 500) -> str:
        if not text:
            return ""

        if self._contains_guardrail_terms(text):
            return ""

        return str(text)[:max_len]

    def _sanitize_incident_for_llm(self, text: str) -> str:
        if not text:
            return ""

        sanitized = str(text)

        replacements = [
            ("Lakera", ""),
            ("lakera", ""),
            ("Guardrails", ""),
            ("guardrails", ""),
            ("Guardrail", ""),
            ("guardrail", ""),
            ("runtime guardrail", ""),
            ("política de guardrails", ""),
            ("bloqueado por Kong/Lakera", ""),
            ("bloqueado por Kong", ""),
            ("bloqueado", ""),
            ("bloqueó", ""),
            ("prompt injection", ""),
            ("jailbreak", ""),
            ("bypass", ""),
            ("prompt", "")
        ]

        for old, new in replacements:
            sanitized = sanitized.replace(
                old,
                new
            )

        return sanitized[:500]

    def _sanitize_list_for_llm(self, items: list) -> list:
        clean_items = []

        for item in items or []:
            text = str(item)

            if self._contains_guardrail_terms(text):
                continue

            clean_items.append(
                text[:250]
            )

        return clean_items[:5]

    def _sanitize_action_plan_for_llm(self, action_plan: dict) -> dict:
        fallback_plan = {
            "containment": [
                "Aislar o monitorear el activo afectado según criticidad.",
                "Preservar evidencia relevante para análisis posterior."
            ],
            "investigation": [
                "Validar alcance del incidente.",
                "Revisar eventos recientes asociados al usuario, activo e indicador."
            ],
            "eradication": [
                "Eliminar artefactos maliciosos si se confirman.",
                "Corregir la causa raíz identificada."
            ],
            "recovery": [
                "Restaurar servicios afectados desde fuentes confiables.",
                "Monitorear recurrencia del comportamiento anómalo."
            ],
            "reporting": [
                "Documentar hallazgos, línea de tiempo y acciones ejecutadas.",
                "Escalar al equipo responsable según severidad."
            ],
            "safety_note": (
                "Las acciones deben ser revisadas y aprobadas por un analista SOC."
            )
        }

        if not action_plan:
            return fallback_plan

        safety_note = self._sanitize_text_for_llm(
            action_plan.get(
                "safety_note",
                ""
            ),
            max_len=250
        )

        sanitized = {
            "containment": self._sanitize_list_for_llm(
                action_plan.get(
                    "containment",
                    []
                )
            ),
            "investigation": self._sanitize_list_for_llm(
                action_plan.get(
                    "investigation",
                    []
                )
            ),
            "eradication": self._sanitize_list_for_llm(
                action_plan.get(
                    "eradication",
                    []
                )
            ),
            "recovery": self._sanitize_list_for_llm(
                action_plan.get(
                    "recovery",
                    []
                )
            ),
            "reporting": self._sanitize_list_for_llm(
                action_plan.get(
                    "reporting",
                    []
                )
            ),
            "safety_note": safety_note
        }

        total_items = (
            len(sanitized["containment"])
            + len(sanitized["investigation"])
            + len(sanitized["eradication"])
            + len(sanitized["recovery"])
            + len(sanitized["reporting"])
        )

        if total_items == 0:
            return fallback_plan

        if not sanitized["containment"]:
            sanitized["containment"] = fallback_plan["containment"]

        if not sanitized["investigation"]:
            sanitized["investigation"] = fallback_plan["investigation"]

        if not sanitized["eradication"]:
            sanitized["eradication"] = fallback_plan["eradication"]

        if not sanitized["recovery"]:
            sanitized["recovery"] = fallback_plan["recovery"]

        if not sanitized["reporting"]:
            sanitized["reporting"] = fallback_plan["reporting"]

        if not sanitized["safety_note"]:
            sanitized["safety_note"] = fallback_plan["safety_note"]

        return sanitized

    def classify_intent(self, user_message: str) -> dict:
        safe_payload = {
            "task": "classify_soc_copilot_intent",
            "user_message": user_message[:500],
            "allowed_intents": [
                "knowledge_question",
                "incident_analysis",
                "playbook_request",
                "tool_lookup",
                "general_chat"
            ],
            "expected_schema": {
                "intent": "string",
                "confidence": "number 0-1",
                "reason": "string"
            }
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC copilot intent classification service. "
                        "Return compact JSON only."
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

        data = self._post_to_kong(payload)
        content = self._extract_content(data)
        parsed = self._safe_json_loads(content)

        intent = parsed.get(
            "intent",
            "incident_analysis"
        )

        if intent not in [
            "knowledge_question",
            "incident_analysis",
            "playbook_request",
            "tool_lookup",
            "general_chat"
        ]:
            intent = "incident_analysis"

        return {
            "intent": intent,
            "confidence": parsed.get(
                "confidence",
                0.5
            ),
            "reason": parsed.get(
                "reason",
                ""
            )
        }

    def generate_knowledge_response(
        self,
        user_message: str,
        context_blocks: list
    ) -> str:
        compact_context = []

        for block in context_blocks[:3]:
            compact_context.append({
                "source": block.get(
                    "source",
                    "fuente_desconocida"
                ),
                "content": block.get(
                    "content",
                    ""
                )[:700]
            })

        safe_payload = {
            "task": "answer_soc_knowledge_question",
            "question": user_message[:600],
            "context": compact_context,
            "response_style": {
                "language": "es-419",
                "format": "brief_clear_explanation",
                "avoid_incident_workflow": True
            }
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC knowledge assistant. "
                        "Answer the question directly in Spanish."
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

        data = self._post_to_kong(payload)

        return self._extract_content(data)

    def analyze_rag_context(
        self,
        incident: str,
        context_blocks: list
    ) -> dict:
        compact_context = []

        for block in context_blocks[:3]:
            compact_context.append({
                "source": block.get(
                    "source",
                    "fuente_desconocida"
                ),
                "content": block.get(
                    "content",
                    ""
                )[:700]
            })

        safe_payload = {
            "task": "rag_incident_analysis",
            "incident": self._sanitize_incident_for_llm(
                incident
            ),
            "context": compact_context,
            "expected_schema": {
                "incident_type": "string",
                "known_facts": "list",
                "missing_information": "list",
                "evidence": "list of objects with source and excerpt",
                "sources": "list"
            }
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "SOC RAG analysis service. "
                        "Return only compact JSON."
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

        data = self._post_to_kong(payload)
        content = self._extract_content(data)
        parsed = self._safe_json_loads(content)

        return {
            "incident_type": parsed.get(
                "incident_type",
                "Incidente de seguridad no clasificado"
            ),
            "known_facts": parsed.get(
                "known_facts",
                []
            ),
            "missing_information": parsed.get(
                "missing_information",
                []
            ),
            "evidence": parsed.get(
                "evidence",
                []
            ),
            "sources": parsed.get(
                "sources",
                []
            )
        }

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
            "incident": self._sanitize_incident_for_llm(
                incident
            ),
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
                "reasons": self._sanitize_list_for_llm(
                    risk.get(
                        "reasons",
                        []
                    )
                )
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

        data = self._post_to_kong(payload)
        content = self._extract_content(data)

        try:
            parsed = self._safe_json_loads(content)

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
                    "Aislar o monitorear el activo afectado según criticidad.",
                    "Preservar evidencia relevante para análisis posterior."
                ],
                "investigation": [
                    "Validar alcance del incidente.",
                    "Revisar eventos recientes asociados al usuario, activo e indicador."
                ],
                "eradication": [
                    "Eliminar artefactos maliciosos si se confirman."
                ],
                "recovery": [
                    "Restaurar servicios afectados desde fuentes confiables."
                ],
                "reporting": [
                    "Documentar hallazgos, línea de tiempo y acciones ejecutadas."
                ],
                "safety_note": (
                    "El plan fue reemplazado por un fallback seguro."
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
        sanitized_action_plan = self._sanitize_action_plan_for_llm(
            action_plan
        )

        safe_payload = {
            "task": "soc_final_response",
            "incident": self._sanitize_incident_for_llm(
                incident
            ),
            "incident_type": incident_type,
            "severity": severity,
            "risk": {
                "score": risk.get("score"),
                "reasons": self._sanitize_list_for_llm(
                    risk.get(
                        "reasons",
                        []
                    )
                )
            },
            "action_plan": sanitized_action_plan,
            "sources": (
                sources[:3]
                if sources
                else []
            ),
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

        data = self._post_to_kong(payload)

        return self._extract_content(data)