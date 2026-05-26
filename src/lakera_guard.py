import requests

from src.config import (
    LAKERA_API_KEY,
    LAKERA_GUARD_URL
)


class LakeraGuard:
    """
    Runtime Guard usando Lakera REAL.

    Flujo:

    App
    ↓
    Lakera
    ↓
    allow / block

    No existe simulación local.

    Si Lakera falla:
    → se bloquea.

    Si falta API key:
    → falla el arranque.
    """

    def __init__(self):

        if not LAKERA_API_KEY:

            raise RuntimeError(
                (
                    "LAKERA_API_KEY no está configurada. "
                    "Este laboratorio requiere Lakera real."
                )
            )

        self.api_key = LAKERA_API_KEY

        self.url = LAKERA_GUARD_URL

    def validate_input(
        self,
        user_input: str
    ):

        return self._check(
            content=user_input,
            direction="input"
        )

    def validate_output(
        self,
        model_output: str
    ):

        return self._check(
            content=model_output,
            direction="output"
        )

    def _check(
        self,
        content: str,
        direction: str
    ):

        headers = {

            "Authorization":
            f"Bearer {self.api_key}",

            "Content-Type":
            "application/json"
        }

        payload = {

            "messages": [

                {

                    "role":
                    "user",

                    "content":
                    content
                }

            ],

            "metadata": {

                "application":
                "soc-copilot-seguro",

                "environment":
                "lab",

                "direction":
                direction,

                "runtime":
                "flask"

            },

            "dev_info": True
        }

        try:

            print("\n====================")
            print("ENVIANDO A LAKERA")
            print("Direction:", direction)
            print("Endpoint:", self.url)
            print("====================\n")

            response = requests.post(

                self.url,

                headers=headers,

                json=payload,

                timeout=20
            )

            print(
                "\nLAKERA HTTP STATUS:",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

            print("\n===== LAKERA RESPONSE =====")

            print(data)

            print("===========================\n")

            flagged = bool(
                data.get(
                    "flagged",
                    False
                )
            )

            return {

                "allowed":
                not flagged,

                "flagged":
                flagged,

                "direction":
                direction,

                "source":
                "lakera_api",

                "raw":
                data
            }

        except Exception as error:

            print(
                "\n===== LAKERA ERROR ====="
            )

            print(
                str(error)
            )

            print(
                "========================\n"
            )

            raise RuntimeError(

                (
                    "Lakera falló: "
                    f"{str(error)}"
                )

            )