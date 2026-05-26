class RAGIncidentAnalyst:
    """
    Agente responsable de analizar el incidente usando solo contexto RAG.
    No inventa información que no esté en la descripción o en los documentos.
    """

    def analyze(self, incident: str, context_blocks: list) -> dict:
        if not context_blocks:
            return {
                "incident_type": "No determinado",
                "known_facts": [
                    "No se encontró contexto suficiente en los documentos internos."
                ],
                "missing_information": [
                    "Se requiere más información del incidente.",
                    "Se requiere revisar fuentes SOC adicionales."
                ],
                "evidence": [],
                "sources": []
            }

        known_facts = []
        evidence = []
        sources = []

        for block in context_blocks:
            source = block.get("source", "fuente_desconocida")
            content = block.get("content", "")

            sources.append(source)

            evidence.append({
                "source": source,
                "excerpt": content[:500]
            })

        incident_lower = incident.lower()

        if (
            "phishing" in incident_lower
            or "correo" in incident_lower
            or "enlace" in incident_lower
        ):
            incident_type = "Posible phishing"
            known_facts.append(
                "El incidente reportado involucra correo electrónico, enlace sospechoso o posible phishing."
            )

        elif (
            "ransomware" in incident_lower
            or "cifrado" in incident_lower
        ):
            incident_type = "Posible ransomware"
            known_facts.append(
                "El incidente reportado contiene indicadores compatibles con ransomware o cifrado malicioso."
            )

        else:
            incident_type = "Incidente de seguridad no clasificado"
            known_facts.append(
                "El tipo exacto del incidente no puede determinarse solo con la descripción inicial."
            )

        known_facts.append(
            "El análisis utiliza documentos internos recuperados por RAG."
        )

        missing_information = [
            "Confirmar usuario afectado.",
            "Confirmar activo o endpoint involucrado.",
            "Confirmar indicador: URL, dominio, IP, hash o remitente.",
            "Validar si hubo exposición de credenciales.",
            "Revisar alertas recientes en herramientas SOC."
        ]

        return {
            "incident_type": incident_type,
            "known_facts": known_facts,
            "missing_information": missing_information,
            "evidence": evidence,
            "sources": sorted(list(set(sources)))
        }


class RiskClassifier:
    """
    Clasificador inicial de severidad.

    Evalúa:
    - Tipo de incidente
    - Riesgo del usuario
    - Alertas encontradas
    """

    def classify(
        self,
        incident_type: str,
        user_risk: dict,
        alerts: dict
    ) -> dict:
        score = 0
        reasons = []

        if incident_type:
            if "phishing" in incident_type.lower():
                score += 2
                reasons.append(
                    "Incidente compatible con phishing."
                )

            if "ransomware" in incident_type.lower():
                score += 4
                reasons.append(
                    "Incidente compatible con ransomware."
                )

        if user_risk:
            risk = user_risk.get("risk", "")

            if risk == "alto":
                score += 3
                reasons.append(
                    "Usuario clasificado con riesgo alto."
                )

            elif risk == "medio":
                score += 2
                reasons.append(
                    "Usuario clasificado con riesgo medio."
                )

            elif risk == "bajo":
                score += 1
                reasons.append(
                    "Usuario clasificado con riesgo bajo."
                )

        if alerts:
            alert_count = len(
                alerts.get("alerts", [])
            )

            score += alert_count

            reasons.append(
                f"Se encontraron {alert_count} alertas recientes."
            )

        if score <= 2:
            severity = "Baja"
        elif score <= 4:
            severity = "Media"
        elif score <= 6:
            severity = "Alta"
        else:
            severity = "Crítica"

        return {
            "severity": severity,
            "score": score,
            "reasons": reasons
        }


class ActionPlanner:
    """
    Agente que recomienda acciones SOC.

    Importante:
    - No ejecuta acciones reales.
    - No elimina datos.
    - No desactiva usuarios.
    - Solo recomienda pasos controlados.
    """

    def plan(
        self,
        incident_type: str,
        severity: str,
        user_email: str,
        user_risk: dict,
        alerts: dict,
        ticket: dict
    ) -> dict:
        containment = []
        investigation = []
        eradication = []
        recovery = []
        reporting = []

        if "phishing" in incident_type.lower():
            containment.extend([
                "Bloquear la URL, dominio o IP asociada al correo sospechoso.",
                "Buscar y retirar correos similares en otros buzones.",
                "Monitorear la cuenta del usuario afectado por actividad anómala."
            ])

            investigation.extend([
                "Confirmar si el usuario hizo clic en el enlace.",
                "Confirmar si el usuario ingresó credenciales.",
                "Revisar logs de autenticación posteriores al clic.",
                "Revisar alertas de email security, endpoint e identidad."
            ])

            eradication.extend([
                "Eliminar correos maliciosos remanentes.",
                "Revocar sesiones activas si se sospecha robo de credenciales.",
                "Forzar cambio de contraseña si hubo ingreso de credenciales."
            ])

            recovery.extend([
                "Confirmar que la cuenta no presenta actividad sospechosa.",
                "Validar que no existan reglas de correo maliciosas.",
                "Cerrar el incidente solo después de documentar evidencia y acciones."
            ])

        elif "ransomware" in incident_type.lower():
            containment.extend([
                "Aislar el endpoint o servidor afectado.",
                "Bloquear indicadores relacionados.",
                "Evitar propagación lateral."
            ])

            investigation.extend([
                "Identificar proceso sospechoso.",
                "Revisar alcance del cifrado.",
                "Determinar activos impactados.",
                "Validar respaldos disponibles."
            ])

            eradication.extend([
                "Eliminar artefactos maliciosos identificados.",
                "Corregir vector inicial de entrada.",
                "Aplicar controles compensatorios."
            ])

            recovery.extend([
                "Restaurar desde respaldos verificados.",
                "Monitorear recurrencia.",
                "Validar operación normal del activo."
            ])

        else:
            containment.extend([
                "Preservar evidencia inicial.",
                "Evitar acciones destructivas sin aprobación.",
                "Escalar al analista SOC correspondiente."
            ])

            investigation.extend([
                "Recolectar usuario, activo, indicador y línea de tiempo.",
                "Consultar alertas recientes.",
                "Validar impacto al negocio."
            ])

            eradication.extend([
                "Definir acciones correctivas según causa raíz."
            ])

            recovery.extend([
                "Validar que el riesgo haya sido reducido."
            ])

        if severity in ["Alta", "Crítica"]:
            reporting.append(
                "Escalar el incidente al equipo de respuesta a incidentes."
            )

        if severity == "Crítica":
            reporting.append(
                "Evaluar notificación a áreas legales, cumplimiento o privacidad si hay datos sensibles comprometidos."
            )

        if user_email:
            reporting.append(
                f"Usuario afectado identificado: {user_email}."
            )

        if user_risk:
            reporting.append(
                f"Riesgo del usuario según MCP: {user_risk.get('risk', 'desconocido')}."
            )

        alert_count = 0

        if alerts:
            alert_count = len(
                alerts.get("alerts", [])
            )

        reporting.append(
            f"Alertas recientes correlacionadas: {alert_count}."
        )

        if ticket:
            reporting.append(
                f"Ticket simulado creado: {ticket.get('ticket_id')}."
            )

        return {
            "containment": containment,
            "investigation": investigation,
            "eradication": eradication,
            "recovery": recovery,
            "reporting": reporting,
            "safety_note": (
                "Este plan no ejecuta acciones destructivas. "
                "Las acciones deben ser revisadas y aprobadas por el SOC."
            )
        }