"""
src/explainability/explain_score.py
Explicaciones inteligentes de scores de riesgo usando GPT-4o-mini.
"""

import os
import json
from functools import lru_cache
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    load_dotenv(os.path.join(_ROOT, ".env"))
except ImportError:
    pass

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# Modelo rápido para el chat del agente (gpt-5-nano es lento por tokens de razonamiento)
OPENAI_MODEL_CHAT = os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini")

_VALID_ROLES = frozenset({"system", "user", "assistant"})


def _normalize_model_name(model: str) -> str:
    return (model or "").lower().replace("_", "-").strip()


def _uses_completion_tokens(model: str) -> bool:
    """Modelos recientes (gpt-5, o-series, gpt-4.1+) usan max_completion_tokens y no temperature."""
    m = _normalize_model_name(model)
    if os.getenv("OPENAI_USE_MAX_COMPLETION_TOKENS", "").lower() in ("1", "true", "yes"):
        return True
    if "gpt-5" in m or "gpt5" in m:
        return True
    if m.startswith(("o1", "o3", "o4")) or m.startswith("o-"):
        return True
    if m.startswith(("gpt-4.1", "gpt-4.5")):
        return True
    return False


def _supports_temperature(model: str) -> bool:
    return not _uses_completion_tokens(model)


def _completion_params(
    model: str,
    max_output: int,
    temperature: float = 0.3,
    *,
    mode: str = "chat",
    use_completion_tokens: Optional[bool] = None,
) -> Dict[str, Any]:
    use_new = _uses_completion_tokens(model) if use_completion_tokens is None else use_completion_tokens
    if use_new:
        # Mínimos probados: chat ~1200, explicación larga ~3000 (evitar error HTTP 400)
        floor = 3000 if mode == "explain" else 1200
        return {"max_completion_tokens": max(max_output, floor)}
    params: Dict[str, Any] = {"max_tokens": max_output}
    if _supports_temperature(model):
        params["temperature"] = temperature
    return params


def _alternate_completion_params(
    model: str,
    max_output: int,
    temperature: float,
    *,
    mode: str = "chat",
) -> Dict[str, Any]:
    """Parámetros alternativos si la API rechaza el primer intento (error 400)."""
    return _completion_params(
        model,
        max_output,
        temperature,
        mode=mode,
        use_completion_tokens=not _uses_completion_tokens(model),
    )


def _sanitize_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    clean: List[Dict[str, str]] = []
    for msg in messages:
        role = (msg.get("role") or "").strip().lower()
        if role == "ai":
            role = "assistant"
        if role not in _VALID_ROLES:
            continue
        content = msg.get("content")
        if content is None:
            continue
        text = str(content).strip()
        if not text:
            continue
        clean.append({"role": role, "content": text})
    return clean


def _is_retriable_openai_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "400" in text
        or "invalid_request" in text
        or "unsupported" in text
        or "max_tokens" in text
        or "max_completion_tokens" in text
        or "temperature" in text
    )


def _create_chat_completion(
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    max_output: int,
    temperature: float = 0.3,
    *,
    mode: str = "chat",
) -> Any:
    """Llama a chat.completions con reintento automático ante parámetros incompatibles."""
    safe_messages = _sanitize_messages(messages)
    if not safe_messages:
        raise ValueError("No hay mensajes válidos para enviar a la API")

    param_sets = [
        _completion_params(model, max_output, temperature, mode=mode),
        _alternate_completion_params(model, max_output, temperature, mode=mode),
    ]
    seen = []
    unique_params = []
    for p in param_sets:
        key = tuple(sorted(p.items()))
        if key not in seen:
            seen.append(key)
            unique_params.append(p)

    last_error: Optional[Exception] = None
    for params in unique_params:
        try:
            return client.chat.completions.create(
                model=model,
                messages=safe_messages,
                **params,
            )
        except Exception as exc:
            last_error = exc
            if not _is_retriable_openai_error(exc):
                raise
    if last_error:
        raise last_error
    raise RuntimeError("No se pudo completar la llamada a OpenAI")


@lru_cache(maxsize=1)
def _get_client() -> Optional[Any]:
    if not _OPENAI_AVAILABLE:
        return None
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-..."):
        return None
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = """Eres un analista experto en detección de fraudes en seguros.
Tu rol es ASISTIR al analista humano — jamás acusas de fraude directamente.
Analizas indicadores de riesgo y generas explicaciones claras, profesionales y accionables.
Responde siempre en español. Sé conciso pero completo.
Usa bullet points cuando sea útil. Nunca menciones que eres una IA en tus análisis."""

CHAT_SYSTEM_PROMPT = SYSTEM_PROMPT + """
En el chat responde de forma breve (máximo 120 palabras) salvo que pidan un análisis detallado."""


def explicar_siniestro(
    siniestro: Dict[str, Any],
    features: Dict[str, Any],
) -> str:
    """
    Genera una explicación narrativa del score de riesgo para un siniestro específico.
    """
    client = _get_client()

    contexto = {
        "id_siniestro": siniestro.get("id_siniestro"),
        "cliente": siniestro.get("cliente"),
        "tipo": siniestro.get("tipo_siniestro"),
        "monto": siniestro.get("monto_reclamado"),
        "historial_reclamos": siniestro.get("historial_reclamos"),
        "dias_desde_poliza": _calcular_dias(siniestro),
        "score_final": features.get("score_final"),
        "nivel_riesgo": features.get("nivel_riesgo"),
        "alertas_activadas": features.get("alertas", []),
        "similitud_narrativa": features.get("nlp", {}).get("max_similitud", 0),
        "narrativa": siniestro.get("narrativa", ""),
    }

    if client is None:
        return _explicacion_local(contexto)

    try:
        prompt = f"""Analiza este siniestro y explica los indicadores de riesgo detectados:

{json.dumps(contexto, ensure_ascii=False, indent=2)}

Proporciona:
1. Conclusión General del Siniestro (Resumen ejecutivo y probabilidad de fraude)
2. Impacto Potencial y Exposición Financiera
3. Nivel de Prioridad y Sugerencia de Auditoría
4. Factores clave que sustentan la decisión"""

        response = _create_chat_completion(
            client,
            OPENAI_MODEL,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_output=900,
            temperature=0.3,
            mode="explain",
        )
        content = response.choices[0].message.content
        return content if content else _explicacion_local(contexto)

    except Exception as e:
        return _explicacion_local(contexto) + f"\n\n*(Modo local: {str(e)[:80]})*"


def responder_consulta(
    pregunta: str,
    historial: List[Dict[str, str]],
    contexto_datos: str,
) -> str:
    """Responde preguntas conversacionales del analista sobre el portafolio."""
    client = _get_client()

    if client is None:
        return _respuesta_local(pregunta, contexto_datos)

    model = OPENAI_MODEL_CHAT
    system_content = CHAT_SYSTEM_PROMPT
    if contexto_datos:
        ctx = contexto_datos if len(contexto_datos) <= 6000 else contexto_datos[:6000] + "\n…[contexto recortado]"
        system_content += f"\n\n## Contexto del portafolio (datos actuales)\n{ctx}"

    mensajes: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    for msg in historial[-6:]:
        mensajes.append(msg)
    mensajes.append({"role": "user", "content": pregunta.strip()})

    try:
        response = _create_chat_completion(
            client,
            model,
            mensajes,
            max_output=450,
            temperature=0.4,
            mode="chat",
        )
        content = response.choices[0].message.content
        return content if content else _respuesta_local(pregunta, contexto_datos)
    except Exception as e:
        return _respuesta_local(pregunta, contexto_datos) + f"\n\n*(Error API: {str(e)[:120]})*"


def _calcular_dias(siniestro: Dict) -> int:
    from datetime import datetime
    try:
        fp = datetime.strptime(siniestro.get("fecha_poliza", "2020-01-01"), "%Y-%m-%d")
        fi = datetime.strptime(siniestro.get("fecha_incidente", "2020-01-01"), "%Y-%m-%d")
        return max((fi - fp).days, 0)
    except Exception:
        return 0


def _explicacion_local(ctx: Dict) -> str:
    """Explicación determinista cuando la API no está disponible."""
    nivel = ctx.get("nivel_riesgo", "Bajo")
    score = ctx.get("score_final", 0)
    alertas = ctx.get("alertas_activadas", [])

    lineas = [
        f"**1. Conclusión General del Siniestro:**",
        f"Tras el análisis automatizado, este caso se clasifica con un nivel de riesgo **{nivel}** (Score: {score}/100). "
        f"{'Existe una alta probabilidad de fraude o sobrecostos debido a la severidad y concurrencia de señales atípicas.' if nivel == 'Alto' else 'Se observan algunas anomalías que elevan la probabilidad de irregularidades y requieren verificación manual.' if nivel == 'Medio' else 'El comportamiento reportado es congruente con los patrones históricos y la probabilidad de fraude es mínima.'}",
        "",
        f"**2. Impacto Potencial y Exposición Financiera:**",
        f"El monto reclamado asciende a **${ctx.get('monto', 0):,.0f}**. "
        f"{'Este valor representa una alta exposición financiera para la aseguradora dado el contexto del siniestro.' if (ctx.get('monto', 0) or 0) > 10000 and nivel != 'Bajo' else 'La exposición financiera se encuentra dentro de parámetros controlables.'}",
        "",
        f"**3. Nivel de Prioridad y Sugerencia de Auditoría:**",
        f"• **Prioridad:** {'🚨 URGENTE' if nivel == 'Alto' else '🟡 MODERADA' if nivel == 'Medio' else '✅ NORMAL'}",
        f"• **Recomendación:** {'Se sugiere paralizar el pago y derivar a la unidad de Investigaciones Especiales (SIU) para una auditoría de campo.' if nivel == 'Alto' else 'Solicitar documentos adicionales y validación cruzada antes de emitir cualquier pago.' if nivel == 'Medio' else 'Proceder con el flujo regular de liquidación y pago.'}",
        "",
        "**4. Factores clave que sustentan la decisión:**",
    ]

    if alertas:
        for a in alertas:
            if isinstance(a, dict):
                lineas.append(f"• {a.get('descripcion', '')}")
            else:
                lineas.append(f"• {a}")
    else:
        lineas.append("• No se detectaron señales de fraude adicionales.")

    lineas.append("")
    lineas.append("⚠️ *Este análisis es autogenerado por el modelo de IA. La decisión final corresponde al ajustador humano.*")
    return "\n".join(lineas)


def _respuesta_local(pregunta: str, contexto: str) -> str:
    pregunta_lower = pregunta.lower()
    if "riesgo alto" in pregunta_lower or "prioritar" in pregunta_lower:
        return "Basado en el análisis del portafolio, los casos con mayor prioridad son aquellos con score superior a 70, múltiples alertas activas y siniestros recientes en pólizas nuevas. Revise el panel de 'Riesgo Alto' en el dashboard."
    elif "proveedor" in pregunta_lower:
        return "Los proveedores con más alertas activas son aquellos que aparecen en múltiples siniestros de alto riesgo. Filtre la tabla por proveedor para identificar patrones de concentración."
    elif "narrativa" in pregunta_lower or "similar" in pregunta_lower:
        return "El módulo NLP detecta narrativas con similitud semántica superior al 65%. Los casos marcados con '🔴 Narrativa similar' presentan descripciones que coinciden con patrones previamente documentados."
    else:
        return f"He analizado su consulta: *'{pregunta}'*. Para una respuesta precisa configure la API key de OpenAI en el archivo .env. El sistema opera en modo local con capacidades de análisis reducidas."
