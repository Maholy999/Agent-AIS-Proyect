"""
src/features/build_features.py + NLP
Módulo de similitud semántica de narrativas usando sentence-transformers.
Detecta narrativas repetitivas o sospechosamente similares.
"""

import numpy as np
import streamlit as st
from typing import List, Dict, Any, Tuple, Optional

@st.cache_resource(show_spinner=False)
def _get_sentence_transformer_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def calcular_similitud_simple(texto1: str, texto2: str) -> float:
    """
    Similitud basada en palabras compartidas (Jaccard).
    Fallback cuando sentence-transformers no está disponible.
    """
    if not texto1 or not texto2:
        return 0.0
    tokens1 = set(texto1.lower().split())
    tokens2 = set(texto2.lower().split())
    interseccion = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(interseccion) / len(union) if union else 0.0


def detectar_narrativas_similares(
    narrativa_nueva: str,
    narrativas_previas: List[str],
    umbral: float = 0.65,
    usar_transformers: bool = False,
) -> Dict[str, Any]:
    """
    Compara una narrativa nueva contra el historial.
    Devuelve similitudes, índices de casos similares y alerta.
    """
    if not narrativas_previas:
        return {
            "max_similitud": 0.0,
            "casos_similares": [],
            "alerta": False,
            "metodo": "ninguno",
        }

    similitudes = []

    if usar_transformers:
        try:
            from sentence_transformers import util
            model = _get_sentence_transformer_model()
            textos = [narrativa_nueva] + narrativas_previas
            embeddings = model.encode(textos, convert_to_tensor=True)
            emb_nueva = embeddings[0]
            emb_previas = embeddings[1:]
            cosine_scores = util.cos_sim(emb_nueva, emb_previas)[0].tolist()
            similitudes = [(float(s), i) for i, s in enumerate(cosine_scores)]
            metodo = "sentence_transformers"
        except ImportError:
            usar_transformers = False

    if not usar_transformers:
        similitudes = [
            (calcular_similitud_simple(narrativa_nueva, n), i)
            for i, n in enumerate(narrativas_previas)
        ]
        metodo = "jaccard"

    similitudes.sort(reverse=True, key=lambda x: x[0])
    max_sim = similitudes[0][0] if similitudes else 0.0
    casos_similares = [
        {"indice": idx, "similitud": round(sim, 3)}
        for sim, idx in similitudes
        if sim >= umbral
    ]

    return {
        "max_similitud": round(max_sim, 3),
        "casos_similares": casos_similares,
        "alerta": max_sim >= umbral,
        "metodo": metodo,
    }


def score_narrativa(resultado_nlp: Dict[str, Any]) -> int:
    """Convierte resultado NLP en puntuación de riesgo [0-30]."""
    sim = resultado_nlp.get("max_similitud", 0.0)
    if sim >= 0.85:
        return 30
    elif sim >= 0.70:
        return 20
    elif sim >= 0.55:
        return 10
    return 0


def construir_features_completas(
    siniestro: Dict[str, Any],
    resultado_reglas: Dict[str, Any],
    resultado_ml: Dict[str, Any],
    resultado_nlp: Dict[str, Any],
) -> Dict[str, Any]:
    """Consolida todos los análisis en un score final ponderado."""
    score_reglas = resultado_reglas.get("score_reglas", 0)
    score_ml = resultado_ml.get("score_ml", 0)
    score_nlp = score_narrativa(resultado_nlp)

    # Ponderación: reglas 40%, ML 45%, NLP 15%
    score_final = int(score_reglas * 0.40 + score_ml * 0.45 + score_nlp * 0.15)
    score_final = min(score_final, 99)

    nivel = "Alto" if score_final >= 70 else "Medio" if score_final >= 40 else "Bajo"

    todas_alertas = resultado_reglas.get("alertas", [])
    if resultado_nlp.get("alerta"):
        todas_alertas.append(
            f"Narrativa con similitud {resultado_nlp['max_similitud']:.0%} a casos previos"
        )

    return {
        "score_final": score_final,
        "nivel_riesgo": nivel,
        "alertas": todas_alertas,
        "desglose": {
            "score_reglas": score_reglas,
            "score_ml": score_ml,
            "score_nlp": score_nlp,
        },
        "nlp": resultado_nlp,
    }
