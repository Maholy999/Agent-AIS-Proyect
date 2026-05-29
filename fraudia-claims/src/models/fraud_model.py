"""
src/models/fraud_model.py
Modelo de detección de anomalías usando Isolation Forest (scikit-learn).
Genera score de riesgo continuo [0-100] y nivel categórico Bajo/Medio/Alto.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Tuple
import joblib
import os
import streamlit as st

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../data/processed/fraud_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "../../data/processed/scaler.pkl")

FEATURES = [
    "monto_reclamado",
    "historial_reclamos",
    "dias_hasta_siniestro",
    "monto_normalizado",
]


def extraer_features(siniestro: Dict[str, Any]) -> np.ndarray:
    """Extrae y construye el vector de características para el modelo."""
    from datetime import datetime

    fecha_poliza = datetime.strptime(siniestro.get("fecha_poliza", "2020-01-01"), "%Y-%m-%d")
    fecha_incidente = datetime.strptime(siniestro.get("fecha_incidente", "2020-01-01"), "%Y-%m-%d")
    dias = max((fecha_incidente - fecha_poliza).days, 0)

    monto = float(siniestro.get("monto_reclamado", 0))
    historial = int(siniestro.get("historial_reclamos", 0))
    monto_norm = np.log1p(monto)

    return np.array([[monto, historial, dias, monto_norm]])


def extraer_features_batch(siniestros: List[Dict[str, Any]]) -> np.ndarray:
    return np.vstack([extraer_features(s) for s in siniestros])


def entrenar_modelo(siniestros: List[Dict[str, Any]]) -> Tuple:
    """Entrena Isolation Forest con los datos disponibles."""
    X = extraer_features_batch(siniestros)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.15,
        random_state=42,
        max_samples="auto",
    )
    model.fit(X_scaled)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    return model, scaler


@st.cache_resource(show_spinner=False)
def cargar_modelo():
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        return joblib.load(MODEL_PATH), joblib.load(SCALER_PATH)
    return None, None


def calcular_score_ml(siniestro: Dict[str, Any], model=None, scaler=None) -> Dict[str, Any]:
    """
    Calcula el score de anomalía usando Isolation Forest.
    Devuelve score [0-100], nivel de riesgo y confianza.
    """
    if model is None or scaler is None:
        # Fallback heurístico si el modelo no está entrenado
        return _score_heuristico(siniestro)

    X = extraer_features(siniestro)
    X_scaled = scaler.transform(X)

    # decision_function: valores más negativos = más anómalos
    raw_score = model.decision_function(X_scaled)[0]
    prediction = model.predict(X_scaled)[0]  # -1 = anomalía, 1 = normal

    # Normalizar a [0, 100]: más negativo → score más alto
    score_normalizado = int(np.clip(((-raw_score + 0.5) / 1.0) * 100, 0, 100))

    nivel = "Alto" if score_normalizado >= 70 else "Medio" if score_normalizado >= 40 else "Bajo"
    es_anomalia = prediction == -1

    return {
        "score_ml": score_normalizado,
        "es_anomalia": es_anomalia,
        "nivel_riesgo_ml": nivel,
        "raw_score": round(float(raw_score), 4),
        "metodo": "isolation_forest",
    }


def _score_heuristico(siniestro: Dict[str, Any]) -> Dict[str, Any]:
    """Score de respaldo basado en heurísticas cuando el modelo no está disponible."""
    from datetime import datetime

    score = 0
    monto = float(siniestro.get("monto_reclamado", 0))
    historial = int(siniestro.get("historial_reclamos", 0))

    try:
        fp = datetime.strptime(siniestro.get("fecha_poliza", "2020-01-01"), "%Y-%m-%d")
        fi = datetime.strptime(siniestro.get("fecha_incidente", "2020-01-01"), "%Y-%m-%d")
        dias = max((fi - fp).days, 0)
    except Exception:
        dias = 365

    if monto > 40000:
        score += 30
    elif monto > 20000:
        score += 15
    else:
        score += max(0, int(monto / 2000))

    score += min(historial * 10, 30)

    if dias < 30:
        score += 30
    elif dias < 90:
        score += 15

    score = min(score, 100)
    nivel = "Alto" if score >= 70 else "Medio" if score >= 40 else "Bajo"

    return {
        "score_ml": score,
        "es_anomalia": score >= 60,
        "nivel_riesgo_ml": nivel,
        "raw_score": 0.0,
        "metodo": "heuristico",
    }
