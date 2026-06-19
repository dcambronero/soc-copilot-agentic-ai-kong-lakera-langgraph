import re

from src.kong_client import KongAIClient


class IntentRouterAgent:
    """
    Clasifica la intención del usuario.

    Esto evita que preguntas generales como:
    "¿Qué es un SOC?"
    entren al workflow de incidente.
    """

    def __init__(self):
        self.kong = KongAIClient()

    def classify(
        self,
        user_message: str
    ) -> dict:
        try:
            return self.kong.classify_intent(
                user_message
            )

        except Exception:
            return self._fallback_classify(
                user_message
            )

    def _fallback_classify(
        self,
        user_message: str
    ) -> dict:
        text = user_message.lower().strip()

        knowledge_patterns = [
            "que es",
            "qué es",
            "explica",
            "definicion",
            "definición",
            "para que sirve",
            "para qué sirve",
            "diferencia",
            "como funciona",
            "cómo funciona"
        ]

        incident_patterns = [
            "usuario",
            "alerta",
            "incidente",
            "ransomware",
            "phishing",
            "malware",
            "cifrado",
            "credenciales",
            "endpoint",
            "servidor",
            "sospechoso",
            "fallidos",
            "autenticacion",
            "autenticación"
        ]

        for pattern in incident_patterns:
            if pattern in text:
                return {
                    "intent": "incident_analysis",
                    "confidence": 0.8,
                    "reason": (
                        "El mensaje contiene señales típicas de incidente SOC."
                    )
                }

        for pattern in knowledge_patterns:
            if pattern in text:
                return {
                    "intent": "knowledge_question",
                    "confidence": 0.8,
                    "reason": (
                        "El mensaje parece una pregunta conceptual o explicativa."
                    )
                }

        if self._contains_email(
            text
        ):
            return {
                "intent": "incident_analysis",
                "confidence": 0.7,
                "reason": (
                    "El mensaje contiene un correo de usuario."
                )
            }

        return {
            "intent": "knowledge_question",
            "confidence": 0.5,
            "reason": (
                "Fallback por defecto para preguntas generales."
            )
        }

    def _contains_email(
        self,
        text: str
    ) -> bool:
        match = re.search(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            text
        )

        return match is not None