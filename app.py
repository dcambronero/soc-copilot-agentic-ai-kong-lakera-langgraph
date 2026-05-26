from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from src.orchestrator import (
    SOCOrchestrator
)

app = Flask(__name__)

# Instancia única del orquestador
orchestrator = SOCOrchestrator()


@app.route("/")
def index():
    """
    Renderiza la interfaz principal del chatbot.
    """

    return render_template(
        "index.html"
    )


@app.route(
    "/chat",
    methods=["POST"]
)
def chat():
    """
    Recibe mensajes del frontend
    y ejecuta el flujo SOC.
    """

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error":
                "No se recibió JSON válido."
            }), 400

        message = (
            data.get(
                "message",
                ""
            )
            .strip()
        )

        if not message:

            return jsonify({
                "error":
                "El mensaje no puede estar vacío."
            }), 400

        result = (
            orchestrator.process_incident(
                message
            )
        )

        return jsonify(
            result
        )

    except Exception as error:

        return jsonify({
            "error":
            f"Error procesando incidente: {str(error)}"
        }), 500


@app.route("/health")
def health():
    """
    Endpoint simple para validar que Flask está vivo.
    """

    return jsonify({
        "status":
        "ok"
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )