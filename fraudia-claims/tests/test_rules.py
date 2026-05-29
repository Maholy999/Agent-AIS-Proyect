"""
tests/test_rules.py
Tests unitarios para el motor de reglas de negocio.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.rules.fraud_rules import (
    regla_monto_elevado,
    regla_poliza_reciente,
    regla_historial_reclamos,
    regla_monto_cero,
    regla_fecha_futura,
    evaluar_todas_las_reglas,
)


# ── regla_monto_elevado ──────────────────────────────────────
def test_monto_elevado_activa():
    activada, desc, peso = regla_monto_elevado(50000)
    assert activada is True
    assert peso > 0

def test_monto_elevado_no_activa():
    activada, _, _ = regla_monto_elevado(10000)
    assert activada is False

def test_monto_en_umbral():
    activada, _, _ = regla_monto_elevado(30000, umbral=30000)
    assert activada is False  # no supera, es igual


# ── regla_poliza_reciente ────────────────────────────────────
def test_poliza_reciente_activa():
    activada, desc, peso = regla_poliza_reciente("2024-01-01", "2024-01-20")
    assert activada is True
    assert "días" in desc

def test_poliza_reciente_no_activa():
    activada, _, _ = regla_poliza_reciente("2023-01-01", "2024-06-01")
    assert activada is False


# ── regla_historial_reclamos ─────────────────────────────────
def test_historial_alto():
    activada, _, _ = regla_historial_reclamos(5)
    assert activada is True

def test_historial_bajo():
    activada, _, _ = regla_historial_reclamos(1)
    assert activada is False


# ── regla_monto_cero ─────────────────────────────────────────
def test_monto_cero():
    activada, _, peso = regla_monto_cero(0)
    assert activada is True
    assert peso >= 30

def test_monto_positivo():
    activada, _, _ = regla_monto_cero(100)
    assert activada is False


# ── regla_fecha_futura ───────────────────────────────────────
def test_fecha_pasada_no_activa():
    activada, _, _ = regla_fecha_futura("2020-01-01")
    assert activada is False

def test_fecha_futura_activa():
    activada, _, _ = regla_fecha_futura("2099-12-31")
    assert activada is True


# ── evaluar_todas_las_reglas ─────────────────────────────────
def test_siniestro_limpio():
    siniestro = {
        "monto_reclamado": 5000,
        "historial_reclamos": 0,
        "fecha_poliza": "2022-01-01",
        "fecha_incidente": "2024-06-01",
        "proveedor": "Taller Normal",
    }
    resultado = evaluar_todas_las_reglas(siniestro)
    assert isinstance(resultado["score_reglas"], int)
    assert resultado["score_reglas"] < 50
    assert isinstance(resultado["alertas"], list)

def test_siniestro_sospechoso():
    siniestro = {
        "monto_reclamado": 80000,
        "historial_reclamos": 5,
        "fecha_poliza": "2024-06-01",
        "fecha_incidente": "2024-06-15",
        "proveedor": "Taller Sospechoso",
    }
    resultado = evaluar_todas_las_reglas(siniestro, contexto={"conteo_proveedor": 8})
    assert resultado["score_reglas"] >= 50
    assert len(resultado["alertas"]) >= 2

def test_estructura_resultado():
    siniestro = {
        "monto_reclamado": 1000,
        "historial_reclamos": 0,
        "fecha_poliza": "2020-01-01",
        "fecha_incidente": "2024-01-01",
        "proveedor": "Taller A",
    }
    resultado = evaluar_todas_las_reglas(siniestro)
    assert "score_reglas" in resultado
    assert "alertas" in resultado
    assert "detalle_reglas" in resultado
    assert "total_alertas" in resultado


if __name__ == "__main__":
    tests = [
        test_monto_elevado_activa, test_monto_elevado_no_activa, test_monto_en_umbral,
        test_poliza_reciente_activa, test_poliza_reciente_no_activa,
        test_historial_alto, test_historial_bajo,
        test_monto_cero, test_monto_positivo,
        test_fecha_pasada_no_activa, test_fecha_futura_activa,
        test_siniestro_limpio, test_siniestro_sospechoso, test_estructura_resultado,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} tests passed")
