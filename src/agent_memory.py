from datetime import datetime


class AgentMemory:

    def __init__(self):
        self.events = []

    def record(
        self,
        agent,
        output
    ):

        self.events.append(
            {
                "time": str(
                    datetime.utcnow()
                ),

                "agent": agent,

                "output": output
            }
        )

    def export(self):
        return self.events