from src.soc_graph import SOCGraph
from src.agent_memory import AgentMemory


class SOCOrchestrator:
    def __init__(self):
        self.graph = SOCGraph()

    def process_incident(
        self,
        incident: str
    ) -> dict:
        memory = AgentMemory()

        state = self.graph.run(
            incident
        )

        for step in state.get(
            "graph_trace",
            []
        ):
            memory.record(
                step,
                {
                    "intent": state.get(
                        "intent"
                    ),
                    "intent_confidence": state.get(
                        "intent_confidence"
                    ),
                    "incident_type": state.get(
                        "incident_type"
                    ),
                    "severity": state.get(
                        "severity"
                    ),
                    "blocked": state.get(
                        "blocked",
                        False
                    ),
                    "action_planner_mode": state.get(
                        "action_planner_mode"
                    ),
                    "rag_analyst_mode": state.get(
                        "rag_analyst_mode"
                    ),
                    "mcp_router_mode": state.get(
                        "mcp_router_mode"
                    ),
                    "review_mode": (
                        state.get(
                            "review",
                            {}
                        ).get(
                            "mode"
                        )
                    )
                }
            )

        return {
            "blocked": state.get(
                "blocked",
                False
            ),

            "summary": (
                "Procesado por SOC Copilot Agentic AI usando Intent Router, "
                "LangGraph, RAG, agentes LLM, Tool Calling, Reviewer Agent "
                "y Kong AI Gateway."
            ),

            "graph_trace": state.get(
                "graph_trace",
                []
            ),

            "agent_memory": memory.export(),

            "intent": state.get(
                "intent"
            ),

            "intent_confidence": state.get(
                "intent_confidence"
            ),

            "intent_reason": state.get(
                "intent_reason"
            ),

            "rag_analyst_mode": state.get(
                "rag_analyst_mode"
            ),

            "mcp_router_mode": state.get(
                "mcp_router_mode"
            ),

            "review": state.get(
                "review",
                {}
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

                "asset_name": state.get(
                    "asset_name"
                ),

                "indicator": state.get(
                    "indicator"
                ),

                "router_mode": state.get(
                    "mcp_router_mode"
                ),

                "tool_calls": state.get(
                    "mcp_tool_calls",
                    []
                ),

                "tools_used": state.get(
                    "mcp_tools_used",
                    []
                ),

                "tool_results": state.get(
                    "mcp_tool_results",
                    []
                ),

                "user_risk": state.get(
                    "user_risk"
                ),

                "asset_info": state.get(
                    "asset_info"
                ),

                "alerts": state.get(
                    "alerts"
                ),

                "ticket": state.get(
                    "ticket"
                )
            }
        }