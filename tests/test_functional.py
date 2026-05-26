from src.rag_engine import RAGEngine
from src.agents import (
    RAGIncidentAnalyst,
    RiskClassifier,
    ActionPlanner
)


def test_rag_returns_relevant_sources():
    engine = RAGEngine()

    results = engine.search(
        "usuario hizo clic en enlace sospechoso recibido por correo"
    )

    assert len(results) > 0

    sources = [
        result.metadata.get("source")
        for result in results
    ]

    assert "playbook_phishing.txt" in sources


def test_rag_incident_analyst_detects_phishing():
    analyst = RAGIncidentAnalyst()

    context_blocks = [
        {
            "source": "playbook_phishing.txt",
            "content": "Responder a incidentes donde un usuario hace clic en un enlace sospechoso."
        }
    ]

    result = analyst.analyze(
        incident="Usuario hizo clic en enlace sospechoso por correo.",
        context_blocks=context_blocks
    )

    assert result["incident_type"] == "Posible phishing"
    assert "playbook_phishing.txt" in result["sources"]


def test_risk_classifier_returns_high_for_phishing_with_alerts():
    classifier = RiskClassifier()

    result = classifier.classify(
        incident_type="Posible phishing",
        user_risk={
            "risk": "medio"
        },
        alerts={
            "alerts": [
                {
                    "alert_id": "ALERT-1001"
                },
                {
                    "alert_id": "ALERT-1002"
                }
            ]
        }
    )

    assert result["severity"] == "Alta"
    assert result["score"] == 6


def test_action_planner_generates_phishing_actions():
    planner = ActionPlanner()

    result = planner.plan(
        incident_type="Posible phishing",
        severity="Alta",
        user_email="jperez@empresa.com",
        user_risk={
            "risk": "medio"
        },
        alerts={
            "alerts": [
                {
                    "alert_id": "ALERT-1001"
                }
            ]
        },
        ticket={
            "ticket_id": "INC-TEST1234"
        }
    )

    assert len(result["containment"]) > 0
    assert len(result["investigation"]) > 0
    assert len(result["reporting"]) > 0
    assert "INC-TEST1234" in " ".join(result["reporting"])