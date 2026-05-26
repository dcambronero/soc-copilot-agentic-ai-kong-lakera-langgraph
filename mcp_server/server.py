from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI(
    title="SOC MCP Server Simulado",
    version="1.0.0"
)


class TicketRequest(BaseModel):
    summary: str
    severity: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "soc-mcp-server"
    }


@app.get("/asset/{asset_name}")
def get_asset_info(asset_name: str):
    assets = {
        "laptop-jperez": {
            "asset_name": "laptop-jperez",
            "type": "endpoint",
            "owner": "jperez@empresa.com",
            "criticality": "media",
            "internet_exposed": False,
            "edr_status": "activo"
        },
        "srv-finanzas-01": {
            "asset_name": "srv-finanzas-01",
            "type": "server",
            "owner": "finanzas",
            "criticality": "alta",
            "internet_exposed": False,
            "edr_status": "activo"
        }
    }

    return assets.get(
        asset_name,
        {
            "asset_name": asset_name,
            "status": "no_encontrado"
        }
    )


@app.get("/user-risk/{user_email}")
def get_user_risk(user_email: str):
    users = {
        "jperez@empresa.com": {
            "user_email": "jperez@empresa.com",
            "department": "finanzas",
            "privileged": False,
            "recent_failed_logins": 3,
            "mfa_enabled": True,
            "risk": "medio"
        },
        "admin@empresa.com": {
            "user_email": "admin@empresa.com",
            "department": "it",
            "privileged": True,
            "recent_failed_logins": 8,
            "mfa_enabled": True,
            "risk": "alto"
        }
    }

    return users.get(
        user_email,
        {
            "user_email": user_email,
            "risk": "desconocido"
        }
    )


@app.get("/alerts")
def search_recent_alerts(indicator: str):
    alerts = []

    if "sospechoso" in indicator.lower() or "phishing" in indicator.lower():
        alerts.append({
            "alert_id": "ALERT-1001",
            "type": "email_security",
            "severity": "high",
            "description": "URL marcada como phishing por gateway de correo.",
            "timestamp": "2026-05-25T10:15:00"
        })

    if "jperez" in indicator.lower():
        alerts.append({
            "alert_id": "ALERT-1002",
            "type": "identity",
            "severity": "medium",
            "description": "Intentos fallidos de autenticación posteriores al correo.",
            "timestamp": "2026-05-25T10:25:00"
        })

    return {
        "indicator": indicator,
        "alerts": alerts
    }


@app.post("/tickets")
def create_incident_ticket(request: TicketRequest):
    ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

    return {
        "ticket_id": ticket_id,
        "summary": request.summary,
        "severity": request.severity,
        "status": "created",
        "created_at": datetime.utcnow().isoformat()
    }