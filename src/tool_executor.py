from src.mcp_client import MCPClient


class ToolExecutor:
    """
    Ejecuta herramientas disponibles en el MCP Server.

    Herramientas soportadas:
    - get_user_risk
    - get_asset_info
    - search_recent_alerts
    """

    def __init__(self):
        self.mcp = MCPClient()

    def execute(
        self,
        tool_calls: list
    ) -> dict:
        results = {
            "user_email": None,
            "asset_name": None,
            "indicator": None,
            "user_risk": None,
            "asset_info": None,
            "alerts": {
                "indicator": None,
                "alerts": []
            },
            "tools_used": [],
            "tool_results": []
        }

        for call in tool_calls:
            tool_name = call.get(
                "tool_name"
            )

            arguments = call.get(
                "arguments",
                {}
            )

            try:
                if tool_name == "get_user_risk":
                    user_email = arguments.get(
                        "user_email"
                    )

                    if not user_email:
                        continue

                    output = self.mcp.get_user_risk(
                        user_email
                    )

                    results["user_email"] = user_email
                    results["user_risk"] = output
                    results["tools_used"].append(
                        tool_name
                    )
                    results["tool_results"].append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "output": output
                    })

                elif tool_name == "get_asset_info":
                    asset_name = arguments.get(
                        "asset_name"
                    )

                    if not asset_name:
                        continue

                    output = self.mcp.get_asset_info(
                        asset_name
                    )

                    results["asset_name"] = asset_name
                    results["asset_info"] = output
                    results["tools_used"].append(
                        tool_name
                    )
                    results["tool_results"].append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "output": output
                    })

                elif tool_name == "search_recent_alerts":
                    indicator = arguments.get(
                        "indicator"
                    )

                    if not indicator:
                        continue

                    output = self.mcp.search_recent_alerts(
                        indicator
                    )

                    results["indicator"] = indicator
                    results["alerts"] = output
                    results["tools_used"].append(
                        tool_name
                    )
                    results["tool_results"].append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "output": output
                    })

            except Exception as error:
                results["tool_results"].append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "error": str(error)
                })

        return results