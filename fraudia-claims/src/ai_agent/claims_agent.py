"""
src/ai_agent/claims_agent.py
Agente conversacional especializado en análisis antifraude.
Integra datos del portafolio con respuestas del LLM.
"""

import json
from typing import Dict, List, Any, Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.explainability.explain_score import responder_consulta


def construir_contexto_portafolio(siniestros: List[Dict[str, Any]]) -> str:
    """Serializa el estado del portafolio para el contexto del agente."""
    if not siniestros:
        return "No hay siniestros registrados en el sistema."

    total = len(siniestros)
    altos = sum(1 for s in siniestros if s.get("nivel_riesgo") == "Alto")
    medios = sum(1 for s in siniestros if s.get("nivel_riesgo") == "Medio")
    bajos = sum(1 for s in siniestros if s.get("nivel_riesgo") == "Bajo")
    monto_total = sum(s.get("monto_reclamado", 0) for s in siniestros)
    score_promedio = sum(s.get("score_riesgo", 0) for s in siniestros) / total if total else 0

    # Casos más críticos
    casos_criticos = sorted(
        [s for s in siniestros if s.get("nivel_riesgo") == "Alto"],
        key=lambda x: x.get("score_riesgo", 0),
        reverse=True,
    )[:5]

    # Proveedores con más alertas
    from collections import Counter
    proveedores = Counter(s.get("proveedor", "N/A") for s in siniestros if s.get("nivel_riesgo") == "Alto")
    top_proveedores = proveedores.most_common(3)

    resumen = {
        "total_siniestros": total,
        "distribucion_riesgo": {"Alto": altos, "Medio": medios, "Bajo": bajos},
        "monto_total_reclamado": round(monto_total, 2),
        "score_promedio": round(score_promedio, 1),
        "casos_criticos_top5": [
            {
                "id": s.get("id_siniestro"),
                "cliente": s.get("cliente"),
                "score": s.get("score_riesgo"),
                "alertas": s.get("alertas", []),
                "monto": s.get("monto_reclamado"),
                "tipo": s.get("tipo_siniestro"),
            }
            for s in casos_criticos
        ],
        "proveedores_mas_alertas": [
            {"proveedor": p, "siniestros_alto_riesgo": c} for p, c in top_proveedores
        ],
    }

    return json.dumps(resumen, ensure_ascii=False, indent=2)


def agente_responder(
    pregunta: str,
    historial_mensajes: List[Dict[str, str]],
    siniestros: List[Dict[str, Any]],
    siniestro_activo: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Punto de entrada principal del agente conversacional.
    Enriquece la pregunta con contexto del portafolio y llama al LLM.
    """
    contexto = construir_contexto_portafolio(siniestros)

    if siniestro_activo:
        contexto += f"\n\nSiniestro actualmente en análisis:\n{json.dumps(siniestro_activo, ensure_ascii=False, indent=2)}"

    return responder_consulta(
        pregunta=pregunta,
        historial=historial_mensajes,
        contexto_datos=contexto,
    )


def sugerir_preguntas(nivel_riesgo_dominante: str) -> List[str]:
    """Sugiere preguntas contextuales según el estado del portafolio."""
    base = [
        "¿Qué casos deberían priorizarse para revisión inmediata?",
        "¿Existen narrativas similares entre siniestros recientes?",
        "Resume los patrones sospechosos detectados hoy.",
    ]
    if nivel_riesgo_dominante == "Alto":
        base += [
            "¿Qué proveedor presenta más alertas activas?",
            "¿Hay concentración de siniestros en alguna ciudad?",
        ]
    return base
