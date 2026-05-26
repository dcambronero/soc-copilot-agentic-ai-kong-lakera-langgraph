import re
from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import (
    StateGraph,
    END
)

from src.rag_engine import RAGEngine

from src.agents import (
    RAGIncidentAnalyst,
    RiskClassifier
)

from src.mcp_client import MCPClient

from src.kong_client import (
    KongAIClient,
    KongAIBlockedError
)


class SOCState(TypedDict, total=False):
    incident: str
    graph_trace: List[str]

    context_blocks: List[Dict[str, Any]]

    user_email: Optional[str]
    user_risk: Optional[Dict[str, Any]]
    alerts: Dict[str, Any]
    ticket: Dict[str, Any]

    incident_type: str
    known_facts: List[str]
    missing_information: List[str]
    evidence: List[Dict[str, Any]]
    sources: List[str]

    risk: Dict[str, Any]
    severity: str

    critical_escalation: Dict[str, Any]

    action_plan: Dict[str, Any]
    action_planner_mode: str

    final_response: str

    blocked: bool
    gateway_guardrails: Dict[str, Any]


class SOCGraph:
    """
    SOC Copilot V3.

    Cambios V3:
    - Risk Classifier sigue siendo determinístico.
    - Action Planner ahora usa LLM vía Kong AI Gateway.
    - Lakera sigue centralizado en Kong como plugin.
    """

    def __init__(self):
        self.rag = RAGEngine()
        self.rag_analyst = RAGIncidentAnalyst()
        self.risk_classifier = RiskClassifier()
        self.mcp = MCPClient()
        self.kong_ai = KongAIClient()

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(SOCState)

        workflow.add_node(
            "rag",
            self._rag_node
        )

        workflow.add_node(
            "mcp",
            self._mcp_node
        )

        workflow.add_node(
            "risk",
            self._risk_node
        )

        workflow.add_node(
            "critical_escalation",
            self._critical_escalation_node
        )

        workflow.add_node(
            "planner_llm",
            self._planner_llm_node
        )

        workflow.add_node(
            "llm",
            self._llm_node
        )

        workflow.set_entry_point(
            "rag"
        )

        workflow.add_edge(
            "rag",
            "mcp"
        )

        workflow.add_edge(
            "mcp",
            "risk"
        )

        workflow.add_conditional_edges(
            "risk",
            self._route_after_risk,
            {
                "critical": "critical_escalation",
                "standard": "planner_llm"
            }
        )

        workflow.add_edge(
            "critical_escalation",
            "planner_llm"
        )

        workflow.add_edge(
            "planner_llm",
            "llm"
        )

        workflow.add_edge(
            "llm",
            END
        )

        return workflow.compile()

    def run(
        self,
        incident: str
    ) -> SOCState:
        initial_state: SOCState = {
            "incident": incident,
            "blocked": False,
            "critical_escalation": {},
            "graph_trace": []
        }

        return self.graph.invoke(
            initial_state
        )

    def _append_trace(
        self,
        state: SOCState,
        node_name: str
    ) -> List[str]:
        trace = state.get(
            "graph_trace",
            []
        )

        return trace + [
            node_name
        ]

    def _route_after_risk(
        self,
        state: SOCState
    ) -> str:
        severity = state.get(
            "severity",
            ""
        )

        if severity == "Crítica":
            return "critical"

        return "standard"

    def _rag_node(
        self,
        state: SOCState
    ) -> Dict[str, Any]:
        incident = state["incident"]

        results = self.rag.search(
            incident
        )

        context_blocks = []

        for result in results:
            context_blocks.append({
                "source": result.metadata.get(
                    "source",
                    "fuente_desconocida"
                ),
                "content": result.page_content.strip()
            })

        rag_analysis = self.rag_analyst.analyze(
            incident=incident,
            context_blocks=context_blocks
        )

        return {
            "graph_trace": self._append_trace(
                state,
                "rag"
            ),
            "context_blocks": context_blocks,
            "incident_type": rag_analysis["incident_type"],
            "known_facts": rag_analysis["known_facts"],
            "missing_information": rag_analysis["missing_information"],
            "evidence": rag_analysis["evidence"],
            "sources": rag_analysis["sources"]
        }

    def _mcp_node(
        self,
        state: SOCState
    ) -> Dict[str, Any]:
        incident = state["incident"]

        user_email = self._extract_email(
            incident
        )

        user_risk = None

        if user_email:
            user_risk = self.mcp.get_user_risk(
                user_email
            )

        alerts = self.mcp.search_recent_alerts(
            incident
        )

        return {
            "graph_trace": self._append_trace(
                state,
                "mcp"
            ),
            "user_email": user_email,
            "user_risk": user_risk,
            "alerts": alerts
        }

    def _risk_node(
        self,
        state: SOCState
    ) -> Dict[str, Any]:
        risk = self.risk_classifier.classify(
            incident_type=state["incident_type"],
            user_risk=state.get("user_risk"),
            alerts=state.get("alerts")
        )

        return {
            "graph_trace": self._append_trace(
                state,
                "risk"
            ),
            "risk": risk,
            "severity": risk["severity"]
        }

    def _critical_escalation_node(
        self,
        state: SOCState
    ) -> Dict[str, Any]:
        escalation = {
            "required": True,
            "reason": (
                "La severidad fue clasificada como Crítica. "
                "El incidente requiere escalamiento inmediato."
            ),
            "notify": [
                "SOC Lead",
                "Incident Response Manager",
                "CISO o responsable de seguridad",
                "Legal/Compliance si aplica"
            ],
            "sla": "Atención inmediata",
            "executive_note": (
                "Se recomienda preparar comunicación ejecutiva, "
                "consolidar línea de tiempo y preservar evidencia."
            )
        }

        return {
            "graph_trace": self._append_trace(
                state,
                "critical_escalation"
            ),
            "critical_escalation": escalation
        }

    def _planner_llm_node(
        self,
        state: SOCState
    ) -> Dict[str, Any]:
        ticket = self.mcp.create_incident_ticket(
            summary=state["incident"][:120],
            severity=state["severity"]
        )

        try:
            action_plan = self.kong_ai.generate_action_plan(
                incident=state["incident"],
                incident_type=state["incident_type"],
                severity=state["severity"],
                risk=state["risk"],
                user_email=state.get("user_email"),
                user_risk=state.get("user_risk"),
                alerts=state.get("alerts"),
                sources=state.get("sources", []),
                evidence=state.get("evidence", []),
                ticket=ticket
            )

            planner_mode = "llm_via_kong"

        except KongAIBlockedError as exc:
            action_plan = {
                "containment": [
                    "El Action Planner LLM fue bloqueado por Kong/Lakera."
                ],
                "investigation": [
                    "Revisar el contenido del incidente y la política de guardrails."
                ],
                "eradication": [],
                "recovery": [],
                "reporting": [
                    "Registrar bloqueo del Action Planner por runtime guardrail."
                ],
                "safety_note": (
                    "No se generó plan LLM porque Kong/Lakera bloqueó la solicitud."
                ),
                "gateway_error": str(exc)
            }

            planner_mode = "blocked_by_kong_lakera"

        critical_escalation = state.get(
            "critical_escalation",
            {}
        )

        if critical_escalation.get("required"):
            action_plan.setdefault(
                "reporting",
                []
            )

            action_plan["reporting"].insert(
                0,
                "Activar proceso de escalamiento crítico inmediatamente."
            )

            action_plan["reporting"].append(
                critical_escalation["executive_note"]
            )

        return {
            "graph_trace": self._append_trace(
                state,
                "planner_llm"
            ),
            "ticket": ticket,
            "action_plan": action_plan,
            "action_planner_mode": planner_mode
        }

    def _llm_node(
        self,
        state: SOCState
    ) -> Dict[str, Any]:
        blocked = False
        error = None

        try:
            final_response = self.kong_ai.generate_final_response(
                incident=state["incident"],
                incident_type=state["incident_type"],
                severity=state["severity"],
                risk=state["risk"],
                action_plan=state["action_plan"],
                sources=state["sources"]
            )

        except KongAIBlockedError as exc:
            blocked = True
            error = str(exc)
            final_response = (
                "Kong AI Gateway bloqueó la respuesta usando Lakera Guard."
            )

        return {
            "graph_trace": self._append_trace(
                state,
                "llm"
            ),
            "blocked": blocked,
            "final_response": final_response,
            "gateway_guardrails": {
                "provider": "kong",
                "guardrail": "ai-lakera-guard",
                "blocked": blocked,
                "error": error
            }
        }

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