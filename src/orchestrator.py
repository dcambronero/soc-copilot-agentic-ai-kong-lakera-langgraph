from src.soc_graph import SOCGraph


class SOCOrchestrator:
    def __init__(self):
        self.graph = SOCGraph()

    def process_incident(
        self,
        incident: str
    ) -> dict:
        state = self.graph.run(
            incident
        )

        return {
            "blocked": state.get(
                "blocked",
                False
            ),

            "summary": (
                "Procesado por SOC Copilot V3.3 usando LangGraph, "
                "RAG Analyst LLM, MCP, Action Planner LLM y Kong AI Gateway."
            ),

            "graph_trace": state.get(
                "graph_trace",
                []
            ),

            "rag_analyst_mode": state.get(
                "rag_analyst_mode"
            ),

            "severity": state.get(
                "severity"
            ),

            "incident_type": state.get(
                "incident_type"
            ),

            "known_facts": state.get(
                "known_facts",
                []
            ),

            "missing_information": state.get(
                "missing_information",
                []
            ),

            "evidence": state.get(
                "evidence",
                []
            ),

            "sources": state.get(
                "sources",
                []
            ),

            "risk": state.get(
                "risk",
                {}
            ),

            "critical_escalation": state.get(
                "critical_escalation",
                {}
            ),

            "action_planner_mode": state.get(
                "action_planner_mode"
            ),

            "action_plan": state.get(
                "action_plan",
                {}
            ),

            "final_response": state.get(
                "final_response"
            ),

            "gateway_guardrails": state.get(
                "gateway_guardrails",
                {}
            ),

            "mcp": {
                "user_email": state.get(
                    "user_email"
                ),

                "user_risk": state.get(
                    "user_risk"
                ),

                "alerts": state.get(
                    "alerts"
                ),

                "ticket": state.get(
                    "ticket"
                )
            }
        }