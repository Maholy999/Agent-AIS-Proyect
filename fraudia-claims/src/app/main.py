"""
src/app/main.py
AIS — Análisis Inteligente de Siniestros · Dashboard principal.
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import io
from datetime import datetime, date

# ── path setup ─────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    supabase_url = os.environ.get("SUPABASE_URL", "")
    if "/rest/v1/" in supabase_url:
        supabase_url = supabase_url.replace("/rest/v1/", "").strip("/")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    
    if supabase_url and supabase_key:
        try:
            return create_client(supabase_url, supabase_key)
        except Exception as e:
            st.error(f"Error inicializando Supabase: {e}")
            return None
    return None

supabase = init_supabase()

# ── page config (MUST be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="AIS — Análisis Inteligente de Siniestros",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── demo data loader ───────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def cargar_datos_demo():
    if not supabase:
        path = os.path.join(ROOT, "data/synthetic/siniestros_demo.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        sys.path.insert(0, os.path.join(ROOT, "data/synthetic"))
        from generate_demo import generar_dataset
        return generar_dataset()
    try:
        res = supabase.table("siniestros").select("*").order("fecha_registro", desc=True).execute()
        if res.data:
            for item in res.data:
                if isinstance(item.get("alertas"), str):
                    try:
                        item["alertas"] = json.loads(item["alertas"])
                    except Exception:
                        item["alertas"] = []
            return res.data
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
    return []

# ── imports (soft-fail) ────────────────────────────────────────
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY = True
except ImportError:
    PLOTLY = False

# ═══════════════════════════════════════════════════════════════
# CSS — AIS Enterprise Theme (Indigo / Cyan)
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=Inter:wght@300;400;500;600&display=swap');

/* ── reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #060A12 !important;
    font-family: 'Inter', sans-serif !important;
    color: #CBD5E1 !important;
}

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* ══════════════════════════════════════════
   LAYOUT GLOBAL — márgenes laterales reales
   Esto es lo que controla que NADA quede pegado
   a los bordes de la pantalla.
   ══════════════════════════════════════════ */
.block-container {
    max-width: 1520px !important;
    margin: 0 auto !important;
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 4rem !important;
    padding-right: 4rem !important;
}

/* Streamlit a veces inyecta un contenedor interno extra */
[data-testid="stAppViewBlockContainer"] {
    max-width: 1520px !important;
    margin: 0 auto !important;
    padding-left: 4rem !important;
    padding-right: 4rem !important;
}

section[data-testid="stSidebar"] { display: none; }
div[data-testid="stToolbar"] { display: none; }

/* ── scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0B1120; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.7); }

/* ── topbar ── */
.ais-topbar {
    background: rgba(6,10,18,0.97);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-bottom: 1px solid rgba(99,102,241,0.18);
    padding: 0 48px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    margin-bottom: 32px;
}
.ais-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 22px;
    color: #fff;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.ais-logo-accent { color: #6366F1; }
.ais-logo-sub {
    font-size: 10px;
    color: #475569;
    font-family: 'Space Mono', monospace;
    font-weight: 400;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.2);
    padding: 3px 8px;
    border-radius: 4px;
}
.ais-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    color: #475569;
    font-family: 'Space Mono', monospace;
}
.ais-status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── section headers ── */
.ais-section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #6366F1;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.ais-section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(99,102,241,0.3), transparent);
}

/* ══════════════════════════════════════════
   KPI CARDS — rediseñadas con jerarquía clara
   ══════════════════════════════════════════ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 32px;
}
.kpi-card {
    background: #0B1120;
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 14px;
    padding: 24px 26px;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
    cursor: default;
    min-height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-card:hover {
    border-color: rgba(99,102,241,0.35);
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(99,102,241,0.12);
}
/* top accent line */
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}
.kpi-card.indigo::before { background: linear-gradient(90deg, #6366F1, #818CF8); }
.kpi-card.red::before    { background: linear-gradient(90deg, #F43F5E, #FB7185); }
.kpi-card.amber::before  { background: linear-gradient(90deg, #F59E0B, #FCD34D); }
.kpi-card.cyan::before   { background: linear-gradient(90deg, #22D3EE, #67E8F9); }

/* background glow blob */
.kpi-card::after {
    content: '';
    position: absolute;
    width: 80px; height: 80px;
    border-radius: 50%;
    right: 16px; top: 16px;
    opacity: 0.08;
    filter: blur(20px);
}
.kpi-card.indigo::after { background: #6366F1; }
.kpi-card.red::after    { background: #F43F5E; }
.kpi-card.amber::after  { background: #F59E0B; }
.kpi-card.cyan::after   { background: #22D3EE; }

.kpi-top-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}
.kpi-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: #64748B;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-weight: 500;
    line-height: 1.4;
}
.kpi-icon {
    font-size: 22px;
    opacity: 0.7;
    line-height: 1;
}
.kpi-value {
    font-family: 'DM Sans', sans-serif;
    font-weight: 700;
    font-size: 42px;
    color: #F1F5F9;
    line-height: 1.05;
    letter-spacing: -0.5px;
    margin-top: 10px;
    font-variant-numeric: tabular-nums;
}
.kpi-value.small { font-size: 30px; letter-spacing: 0; }
.kpi-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
}
.kpi-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: #475569;
    font-weight: 400;
}
.kpi-badge {
    font-size: 10px;
    font-family: 'DM Mono', monospace;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
}
.kpi-badge.indigo { background: rgba(99,102,241,0.12); color: #818CF8; }
.kpi-badge.red    { background: rgba(244,63,94,0.12);  color: #FB7185; }
.kpi-badge.amber  { background: rgba(245,158,11,0.12); color: #FCD34D; }
.kpi-badge.cyan   { background: rgba(34,211,238,0.12); color: #67E8F9; }

/* ── risk pills ── */
.risk-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.risk-alto  { background: rgba(244,63,94,0.12);   color: #FB7185; border: 1px solid rgba(244,63,94,0.25); }
.risk-medio { background: rgba(245,158,11,0.12);  color: #FCD34D; border: 1px solid rgba(245,158,11,0.25); }
.risk-bajo  { background: rgba(16,185,129,0.12);  color: #34D399; border: 1px solid rgba(16,185,129,0.25); }
.risk-dot { width: 5px; height: 5px; border-radius: 50%; }
.risk-alto .risk-dot  { background: #F43F5E; box-shadow: 0 0 5px #F43F5E; }
.risk-medio .risk-dot { background: #F59E0B; box-shadow: 0 0 5px #F59E0B; }
.risk-bajo .risk-dot  { background: #10B981; box-shadow: 0 0 5px #10B981; }

/* ── score bar ── */
.score-bar-wrap { min-width: 80px; }
.score-label { font-size: 12px; color: #E2E8F0; font-weight: 600; margin-bottom: 4px; }
.score-bar-track {
    height: 5px;
    background: rgba(30,41,59,0.8);
    border-radius: 3px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s ease;
}

/* ── claims table ── */
.claims-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.claims-table th {
    text-align: left;
    padding: 10px 14px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #475569;
    border-bottom: 1px solid rgba(99,102,241,0.15);
    background: rgba(11,17,32,0.5);
}
.claims-table td {
    padding: 12px 14px;
    border-bottom: 1px solid rgba(30,41,59,0.5);
    color: #94A3B8;
    vertical-align: middle;
}
.claims-table tr:hover td {
    background: rgba(99,102,241,0.05);
    color: #CBD5E1;
}
.claim-id {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #818CF8;
}
.claim-monto { color: #E2E8F0; font-weight: 600; }

/* ── alert items ── */
.alert-item {
    background: rgba(244,63,94,0.05);
    border: 1px solid rgba(244,63,94,0.18);
    border-left: 3px solid #F43F5E;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.alert-item.medium {
    background: rgba(245,158,11,0.05);
    border-color: rgba(245,158,11,0.18);
    border-left-color: #F59E0B;
}
.alert-id {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #94A3B8;
    margin-bottom: 4px;
}
.alert-desc { font-size: 12px; color: #CBD5E1; line-height: 1.5; }
.alert-explain {
    font-size: 11px;
    color: #64748B;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid rgba(30,41,59,0.5);
    line-height: 1.5;
    font-style: italic;
}

/* ── chart card ── */
.chart-card {
    background: #0B1120;
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 20px;
}

/* ── explain card ── */
.explain-card {
    background: #0B1120;
    border: 1px solid rgba(99,102,241,0.2);
    border-left: 3px solid #6366F1;
    border-radius: 10px;
    padding: 16px 18px;
    margin-top: 12px;
}
.explain-card h5 {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    color: #818CF8;
    margin: 0 0 8px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.explain-card p { font-size: 13px; color: #94A3B8; line-height: 1.7; margin: 0; }

/* ── info card (nlp, ahorro) ── */
.info-card {
    background: #0B1120;
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.info-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 12px;
    color: #818CF8;
    font-weight: 700;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── savings card ── */
.savings-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(34,211,238,0.08));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 20px;
    text-align: center;
}
.savings-amount {
    font-family: 'Syne', sans-serif;
    font-size: 40px;
    font-weight: 800;
    color: #22D3EE;
    letter-spacing: -1px;
    line-height: 1;
    margin: 8px 0 4px;
}
.savings-label {
    font-size: 11px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── ranking bar ── */
.rank-bar-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.rank-label { font-size: 12px; color: #CBD5E1; width: 160px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-bar-track { flex: 1; height: 8px; background: rgba(30,41,59,0.8); border-radius: 4px; overflow: hidden; }
.rank-bar-fill { height: 100%; border-radius: 4px; }
.rank-count { font-size: 11px; color: #64748B; font-family: 'Space Mono', monospace; min-width: 28px; text-align: right; }

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(99,102,241,0.2) !important;
    gap: 0 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #475569 !important;
    border: none !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #818CF8 !important;
    border-bottom: 2px solid #6366F1 !important;
}

/* ── streamlit form inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
    background: rgba(11,17,32,0.9) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    color: #CBD5E1 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(99,102,241,0.55) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}
label[data-baseweb="label"], .stTextInput label,
.stSelectbox label, .stNumberInput label,
.stTextArea label, .stDateInput label {
    color: #64748B !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
.stButton > button {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    font-size: 13px !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6366F1, #818CF8) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(99,102,241,0.45) !important;
}

/* ── chat ── */
.chat-bubble {
    padding: 11px 15px;
    border-radius: 10px;
    font-size: 12px;
    line-height: 1.6;
    max-width: 92%;
    margin-bottom: 2px;
}
.chat-bubble.user {
    background: rgba(99,102,241,0.18);
    border: 1px solid rgba(99,102,241,0.3);
    color: #C7D2FE;
    align-self: flex-end;
    border-bottom-right-radius: 3px;
}
.chat-bubble.ai {
    background: rgba(11,17,32,0.9);
    border: 1px solid rgba(99,102,241,0.15);
    color: #CBD5E1;
    align-self: flex-start;
    border-bottom-left-radius: 3px;
}
.chat-label {
    font-size: 9px;
    color: #334155;
    font-family: 'Space Mono', monospace;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── login ── */
.login-wrap {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #060A12;
    background-image:
        radial-gradient(ellipse at 15% 50%, rgba(99,102,241,0.18) 0%, transparent 60%),
        radial-gradient(ellipse at 85% 20%, rgba(34,211,238,0.1) 0%, transparent 50%);
}

/* ── network graph legend ── */
.net-legend {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 11px;
    color: #64748B;
    margin-top: 8px;
}
.net-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 4px;
    vertical-align: middle;
}

/* ── separator ── */
.ais-separator {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.2), transparent);
    margin: 24px 0;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "show_form": False,
        "siniestros": [],
        "chat_history": [],
        "selected_id": None,
        "filter_risk": "Todos",
        "search_query": "",
        "ahorro_tasa": 30,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def risk_pill_html(nivel: str) -> str:
    cls = {"Alto": "risk-alto", "Medio": "risk-medio", "Bajo": "risk-bajo"}.get(nivel, "risk-bajo")
    return f'<span class="risk-pill {cls}"><span class="risk-dot"></span>{nivel}</span>'

def score_bar_html(score: int) -> str:
    color = "#F43F5E" if score >= 70 else "#F59E0B" if score >= 40 else "#10B981"
    return f"""
    <div class="score-bar-wrap">
      <div class="score-label">{score}</div>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
      </div>
    </div>"""

def generar_explicacion_alerta(s: dict) -> str:
    """Genera automáticamente una explicación textual de la alerta del siniestro."""
    alertas = s.get("alertas", [])
    if isinstance(alertas, str):
        try:
            import json
            alertas = json.loads(alertas)
        except Exception:
            alertas = []
            
    nivel = s.get("nivel_riesgo", "Bajo")
    score = s.get("score_riesgo", 0)
    monto = s.get("monto_reclamado", 0)
    historial = s.get("historial_reclamos", s.get("historial_siniestros_asegurado", 0))
    dias_entre = s.get("dias_entre_ocurrencia_reporte", 0)
    ramo = s.get("ramo", s.get("tipo_siniestro", "desconocido"))

    partes = []

    if nivel == "Alto":
        partes.append(f"**Score {score}/100:** El análisis detecta una acumulación inusual de anomalías que superan significativamente los parámetros estándar del ramo {ramo}. Se identifican inconsistencias que sugieren la necesidad de una verificación de campo.")
    elif nivel == "Medio":
        partes.append(f"**Score {score}/100:** El análisis detecta factores atípicos que se desvían de los patrones comunes. Se sugiere una validación documental detallada antes de continuar con la liquidación.")
    else:
        partes.append(f"**Score {score}/100:** Los indicadores analizados y el comportamiento del asegurado se mantienen dentro de los parámetros esperados para el ramo {ramo}. No se identifican anomalías críticas.")

    desc_alertas = " ".join([str(a.get("descripcion", a)) if isinstance(a, dict) else str(a) for a in alertas]).lower()
    
    # Análisis contextual
    if "reporte" in desc_alertas and ("días" in desc_alertas or "demorado" in desc_alertas or "extemporáneo" in desc_alertas):
        if nivel == "Bajo":
            partes.append(f"• **Demora en Notificación:** Aunque el reclamo se reportó con {dias_entre} días de demora, este lapso no representa un riesgo severo en el contexto actual y se considera explicable.")
        else:
            partes.append(f"• **Demora en Notificación:** El reclamo fue reportado {dias_entre} días después del evento. Esta demora limita la capacidad técnica de la aseguradora para inspeccionar el lugar de los hechos de manera oportuna.")
        
    if "falta" in desc_alertas and "documentación" in desc_alertas:
        partes.append("• **Documentación Pendiente:** El expediente carece de documentos obligatorios. Su ausencia impide completar la validación pericial de las circunstancias declaradas.")

    if monto > 15000:
        if nivel == "Bajo":
            partes.append(f"• **Monto:** El reclamo asciende a ${monto:,.0f}. Aunque es un monto considerable, guarda proporción con el tipo de evento y la suma asegurada.")
        else:
            partes.append(f"• **Exposición Financiera:** El monto reclamado (${monto:,.0f}) excede significativamente la media estadística, lo que representa una exposición material para la aseguradora.")
        
    if historial and historial >= 3:
        if nivel == "Bajo":
            partes.append(f"• **Historial Activo:** El asegurado registra {historial} siniestros previos. Si bien existe recurrencia, los tipos de reclamos y las resoluciones se alinean con la normalidad del ramo.")
        else:
            partes.append(f"• **Frecuencia Elevada:** El asegurado presenta {historial} siniestros previos, una frecuencia que se desvía del comportamiento típico de la cartera y requiere revisión cruzada de antecedentes.")
        
    if "falsificación" in desc_alertas or "adulteración" in desc_alertas or "dudosa" in desc_alertas:
        partes.append("**Inconsistencia Documental Grave:** Existen fuertes indicios de adulteración o falsificación en los documentos presentados, lo cual constituye una señal crítica y directa de intento de fraude material.")
        
    if "dinámica imposible" in desc_alertas or "incoherente" in desc_alertas:
        partes.append("**Narrativa Incoherente:** La descripción de los hechos entra en contradicción con las leyes de la física o la lógica del daño, lo que indica fuertemente que el relato ha sido fabricado o alterado.")

    if len(alertas) >= 4:
        partes.append(f"**Acumulación de Anomalías:** Aunque algunas señales pueden parecer menores por separado, la concurrencia de **{len(alertas)} factores de riesgo** forma un patrón altamente inusual que amerita investigación profunda.")

    if len(partes) == 1:
        partes.append("No se identificaron anomalías o factores de riesgo relevantes que requieran atención especial.")

    return "<br><br>".join(partes)

@st.cache_data(show_spinner=False)
def obtener_explicacion_ia(siniestro_id: str, siniestro_dict: dict, features_dict: dict) -> str:
    try:
        from src.explainability.explain_score import explicar_siniestro
        return explicar_siniestro(siniestro_dict, features_dict)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════
def page_login():
    col_pad, col_form, col_pad2 = st.columns([1, 1.2, 1])
    with col_form:
        st.markdown('<div style="height:12vh"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;margin-bottom:36px;">
            <div style="font-family:Syne,sans-serif;font-weight:800;font-size:42px;
            color:#fff;letter-spacing:-1.5px;line-height:1;">
                AIS<span style="color:#6366F1">·</span>
            </div>
            <div style="font-size:13px;color:#475569;letter-spacing:0.05em;margin-top:6px;">
                Análisis Inteligente de Siniestros
            </div>
            <div style="font-size:10px;color:#334155;letter-spacing:0.14em;text-transform:uppercase;
            font-family:'Space Mono',monospace;margin-top:10px;">
                Plataforma Antifraude · v2.0
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#0B1120;border:1px solid rgba(99,102,241,0.2);
        border-radius:16px;padding:36px 32px;
        box-shadow:0 40px 100px rgba(0,0,0,0.5),0 0 60px rgba(99,102,241,0.04);">
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown('<p style="font-size:11px;color:#64748B;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Usuario</p>', unsafe_allow_html=True)
            username = st.text_input("", placeholder="analista@empresa.com", label_visibility="collapsed")
            st.markdown('<p style="font-size:11px;color:#64748B;letter-spacing:0.08em;text-transform:uppercase;margin:14px 0 4px;">Contraseña</p>', unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="••••••••••", label_visibility="collapsed")
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("Acceder al sistema →", use_container_width=True, type="primary")

            if submitted:
                if username and password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username.split("@")[0].title()
                    st.rerun()
                else:
                    st.error("Ingresa usuario y contraseña.")

        st.markdown("""
        <div style="margin-top:18px;padding:10px 14px;background:rgba(99,102,241,0.06);
        border-radius:8px;border:1px solid rgba(99,102,241,0.15);">
            <p style="font-size:10px;color:#334155;margin:0;font-family:'Space Mono',monospace;">
            DEMO — Ingresa cualquier usuario y contraseña para continuar
            </p>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TOPBAR
# ═══════════════════════════════════════════════════════════════
def render_topbar(data: list = None):
    col_logo, col_mid, col_right = st.columns([2, 4, 3])
    with col_logo:
        st.markdown("""
        <div style="padding:14px 0;">
          <span style="font-family:Syne,sans-serif;font-weight:800;font-size:20px;color:#fff;letter-spacing:-0.5px;">
            AIS<span style="color:#6366F1;">·</span>
          </span>
          <span style="font-size:10px;color:#475569;font-family:'DM Mono',monospace;
          margin-left:10px;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);
          padding:3px 8px;border-radius:4px;letter-spacing:0.06em;">
          ANÁLISIS INTELIGENTE DE SINIESTROS
          </span>
        </div>""", unsafe_allow_html=True)
    with col_mid:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:14px 0;">
            <span style="width:7px;height:7px;border-radius:50%;background:#10B981;
            box-shadow:0 0 8px #10B981;display:inline-block;"></span>
            <span style="font-size:10px;color:#475569;font-family:'DM Mono',monospace;letter-spacing:0.1em;">
            SISTEMA ACTIVO
            </span>
        </div>""", unsafe_allow_html=True)
    with col_right:
        # usuario + exportar + cerrar sesión alineados en la topbar
        c_user, c_export, c_logout = st.columns([2.2, 2.4, 0.8])
        with c_user:
            st.markdown(f"""
            <div style="padding:14px 0;text-align:right;font-size:11px;color:#64748B;
            font-family:'DM Mono',monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {st.session_state.get('username','Analista')}
            </div>""", unsafe_allow_html=True)
        with c_export:
            if data:
                import io as _io
                df_exp = pd.DataFrame([{
                    "ID": s.get("id_siniestro",""),
                    "Asegurado": s.get("cliente", s.get("id_asegurado","")),
                    "Ramo": s.get("ramo", s.get("tipo_siniestro","")),
                    "Monto Reclamado": s.get("monto_reclamado",0),
                    "Score": s.get("score_riesgo",0),
                    "Nivel Riesgo": s.get("nivel_riesgo",""),
                    "Alertas": "; ".join([a.get("descripcion") if isinstance(a, dict) else str(a) for a in (json.loads(s.get("alertas", "[]")) if isinstance(s.get("alertas"), str) else s.get("alertas", []))]),
                    "Estado": s.get("estado",""),
                    "Ciudad": s.get("ciudad",""),
                    "Sucursal": s.get("sucursal",""),
                    "Fecha Ocurrencia": s.get("fecha_ocurrencia", s.get("fecha_incidente","")),
                } for s in data])
                csv_buf = _io.StringIO()
                df_exp.to_csv(csv_buf, index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Exportar reporte",
                    data=csv_buf.getvalue().encode("utf-8-sig"),
                    file_name=f"AIS_auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Exportar reporte de auditoría en formato CSV",
                )
        with c_logout:
            if st.button("⎋", key="logout_btn", help="Cerrar sesión"):
                st.session_state["logged_in"] = False
                st.rerun()

    st.markdown('<hr style="margin:0 0 32px;border:none;border-top:1px solid rgba(99,102,241,0.15);">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# KPI SECTION — jerarquía visual mejorada
# ═══════════════════════════════════════════════════════════════
def render_kpis(data: list):
    total = len(data)
    altos  = sum(1 for s in data if s.get("nivel_riesgo") == "Alto")
    medios = sum(1 for s in data if s.get("nivel_riesgo") == "Medio")
    monto  = sum(s.get("monto_reclamado", 0) for s in data)
    score_avg = sum(s.get("score_riesgo", 0) for s in data) / total if total else 0
    pct_alto = f"{altos/total*100:.0f}%" if total else "—"

    st.markdown('<div class="ais-section-title">Panel de control · Siniestros</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    cards = [
        (c1, "indigo", "🗂️", "Total de siniestros", str(total),
         f"{medios} en seguimiento", f"{medios} revisión", "indigo"),
        (c2, "red", "🚨", "Riesgo alto", str(altos),
         "Casos críticos activos", pct_alto, "red"),
        (c3, "amber", "📊", "Score de riesgo", f"{score_avg:.0f}",
         "Promedio del portafolio", "Índice global", "amber"),
        (c4, "cyan", "💰", "Monto reclamado", f"${monto/1000:.0f}K" if monto >= 1000 else f"${monto:,.0f}",
         "Suma total reclamada", "USD", "cyan"),
    ]

    for col, cls, icon, label, val, sub, badge, badge_cls in cards:
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls}">
              <div class="kpi-top-row">
                <div class="kpi-label">{label}</div>
                <div class="kpi-icon">{icon}</div>
              </div>
              <div class="kpi-value{'  small' if len(val) > 5 else ''}">{val}</div>
              <div class="kpi-footer">
                <div class="kpi-sub">{sub}</div>
                <div class="kpi-badge {badge_cls}">{badge}</div>
              </div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════
def render_charts(data: list):
    if not PLOTLY or not data:
        st.info("Instala plotly para ver los gráficos: pip install plotly")
        return

    df = pd.DataFrame(data)
    col1, col2 = st.columns(2)

    # Risk distribution donut
    with col1:
        st.markdown('<div class="ais-section-title">Distribución de riesgo</div>', unsafe_allow_html=True)
        risk_counts = df["nivel_riesgo"].value_counts() if "nivel_riesgo" in df.columns else pd.Series()
        colors = {"Alto": "#F43F5E", "Medio": "#F59E0B", "Bajo": "#10B981"}
        if not risk_counts.empty:
            fig = go.Figure(go.Pie(
                labels=risk_counts.index.tolist(),
                values=risk_counts.values.tolist(),
                hole=0.68,
                marker_colors=[colors.get(l, "#6366F1") for l in risk_counts.index],
                textinfo="percent",
                textfont=dict(size=11, color="#CBD5E1"),
                hovertemplate="<b>%{label}</b><br>%{value} casos<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(font=dict(color="#64748B", size=11), bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=0, r=0, t=10, b=10), height=220,
                annotations=[dict(
                    text=f"<b>{len(df)}</b><br><span style='font-size:10px'>casos</span>",
                    showarrow=False, font=dict(color="#E2E8F0", size=18)
                )]
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Score histogram
    with col2:
        st.markdown('<div class="ais-section-title">Distribución de scores</div>', unsafe_allow_html=True)
        if "score_riesgo" in df.columns:
            scores = df["score_riesgo"].dropna().tolist()
            fig2 = go.Figure(go.Histogram(
                x=scores,
                nbinsx=12,
                marker_color="#6366F1",
                marker_line=dict(color="rgba(0,0,0,0)", width=0),
                opacity=0.85,
                hovertemplate="Score: %{x}<br>Casos: %{y}<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, color="#475569", tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="rgba(99,102,241,0.08)",
                           color="#475569", tickfont=dict(size=10)),
                margin=dict(l=0, r=0, t=10, b=30), height=220,
                bargap=0.15,
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Ramo breakdown
    if "ramo" in df.columns or "tipo_siniestro" in df.columns:
        campo_ramo = "ramo" if "ramo" in df.columns else "tipo_siniestro"
        st.markdown('<div class="ais-section-title" style="margin-top:12px;">Siniestros por ramo</div>', unsafe_allow_html=True)
        ramo_counts = df[campo_ramo].value_counts().head(8)
        fig3 = go.Figure(go.Bar(
            x=ramo_counts.values.tolist(),
            y=ramo_counts.index.tolist(),
            orientation="h",
            marker=dict(
                color=ramo_counts.values.tolist(),
                colorscale=[[0, "#22D3EE"], [1, "#6366F1"]],
                line=dict(color="rgba(0,0,0,0)"),
            ),
            hovertemplate="%{y}: %{x} casos<extra></extra>",
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="rgba(99,102,241,0.08)", color="#475569", tickfont=dict(size=10)),
            yaxis=dict(showgrid=False, color="#CBD5E1", tickfont=dict(size=11)),
            margin=dict(l=0, r=0, t=10, b=20), height=240,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════
# RANKING DE PROVEEDORES
# ═══════════════════════════════════════════════════════════════
def render_ranking_proveedores(data: list):
    st.markdown('<div class="ais-section-title">Ranking de proveedores por concentración de alertas</div>', unsafe_allow_html=True)

    if not data:
        st.info("Sin datos disponibles.")
        return

    # Agrupar por proveedor
    prov_stats: dict = {}
    for s in data:
        prov = s.get("proveedor", "") or s.get("beneficiario", "Sin especificar")
        if not prov or prov in ("Sin especificar", "sin especificar", ""):
            prov = "Sin especificar"
        if prov not in prov_stats:
            prov_stats[prov] = {"total": 0, "altos": 0, "monto": 0.0}
        prov_stats[prov]["total"] += 1
        if s.get("nivel_riesgo") == "Alto":
            prov_stats[prov]["altos"] += 1
        prov_stats[prov]["monto"] += s.get("monto_reclamado", 0)

    # Ordenar por número de alertas alto
    ranked = sorted(prov_stats.items(), key=lambda x: x[1]["altos"], reverse=True)[:10]

    if not ranked:
        st.info("No hay datos de proveedores.")
        return

    max_altos = max(v["altos"] for _, v in ranked) or 1

    for prov_name, stats in ranked:
        pct = stats["altos"] / max_altos
        color = "#F43F5E" if pct > 0.6 else "#F59E0B" if pct > 0.3 else "#6366F1"
        st.markdown(f"""
        <div class="rank-bar-wrap">
          <div class="rank-label" title="{prov_name}">{prov_name}</div>
          <div class="rank-bar-track">
            <div class="rank-bar-fill" style="width:{pct*100:.0f}%;background:{color};"></div>
          </div>
          <div class="rank-count">{stats['altos']}🔴</div>
        </div>""", unsafe_allow_html=True)

    # Tabla resumen
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    df_rank = pd.DataFrame([
        {
            "Proveedor": name,
            "Total siniestros": v["total"],
            "Alertas altas": v["altos"],
            "% Alto riesgo": f"{v['altos']/v['total']*100:.0f}%" if v["total"] else "0%",
            "Monto total": f"${v['monto']:,.0f}"
        }
        for name, v in ranked
    ])
    st.dataframe(df_rank, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# RED DE RELACIONES
# ═══════════════════════════════════════════════════════════════
def render_red_relaciones(data: list):
    st.markdown('<div class="ais-section-title">Red de relaciones — Asegurados · Proveedores · Siniestros</div>', unsafe_allow_html=True)

    if not PLOTLY or not data:
        st.info("Instala plotly para ver la red de relaciones.")
        return

    import math, random as rnd

    # Build node lists
    asegurados = list({s.get("cliente", s.get("id_asegurado", "?")) for s in data})
    proveedores = list({s.get("proveedor", "Sin proveedor") or "Sin proveedor" for s in data})

    n_a = len(asegurados)
    n_p = len(proveedores)

    # Positions: asegurados in a circle on left, proveedores on right
    a_pos = {a: (rnd.uniform(-3, -1), rnd.uniform(-n_a/2, n_a/2)) for a in asegurados}
    p_pos = {p: (rnd.uniform(1, 3), rnd.uniform(-n_p/2, n_p/2)) for p in proveedores}

    edge_x, edge_y = [], []
    for s in data:
        a = s.get("cliente", s.get("id_asegurado", "?"))
        p = s.get("proveedor", "Sin proveedor") or "Sin proveedor"
        if a in a_pos and p in p_pos:
            ax, ay = a_pos[a]
            px, py = p_pos[p]
            edge_x += [ax, px, None]
            edge_y += [ay, py, None]

    traces = []
    # Edges
    traces.append(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(99,102,241,0.2)", width=1),
        hoverinfo="none", showlegend=False
    ))

    # Asegurado nodes
    a_x = [a_pos[a][0] for a in asegurados]
    a_y = [a_pos[a][1] for a in asegurados]
    traces.append(go.Scatter(
        x=a_x, y=a_y, mode="markers+text",
        marker=dict(size=14, color="#6366F1", line=dict(color="#818CF8", width=1.5)),
        text=[a[:12] for a in asegurados],
        textposition="top center",
        textfont=dict(size=9, color="#94A3B8"),
        hovertemplate="Asegurado: %{text}<extra></extra>",
        name="Asegurado"
    ))

    # Proveedor nodes
    p_x = [p_pos[p][0] for p in proveedores]
    p_y = [p_pos[p][1] for p in proveedores]
    traces.append(go.Scatter(
        x=p_x, y=p_y, mode="markers+text",
        marker=dict(size=12, color="#22D3EE", symbol="diamond",
                    line=dict(color="#67E8F9", width=1.5)),
        text=[p[:12] for p in proveedores],
        textposition="bottom center",
        textfont=dict(size=9, color="#94A3B8"),
        hovertemplate="Proveedor: %{text}<extra></extra>",
        name="Proveedor"
    ))

    # Alto riesgo siniestros (middle)
    altos = [s for s in data if s.get("nivel_riesgo") == "Alto"]
    if altos:
        s_x = [rnd.uniform(-0.5, 0.5) for _ in altos]
        s_y = [rnd.uniform(-len(altos)/2, len(altos)/2) for _ in altos]
        traces.append(go.Scatter(
            x=s_x, y=s_y, mode="markers",
            marker=dict(size=9, color="#F43F5E", symbol="x",
                        line=dict(color="#FB7185", width=1)),
            hovertemplate="Siniestro alto riesgo: %{customdata}<extra></extra>",
            customdata=[s.get("id_siniestro","?") for s in altos],
            name="Siniestro Alto Riesgo"
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(font=dict(color="#64748B", size=10), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=10, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("""
    <div class="net-legend">
        <span><span class="net-dot" style="background:#6366F1;"></span>Asegurado</span>
        <span><span class="net-dot" style="background:#22D3EE;"></span>Proveedor</span>
        <span><span class="net-dot" style="background:#F43F5E;"></span>Siniestro alto riesgo</span>
        <span><span class="net-dot" style="background:rgba(99,102,241,0.5);"></span>Relación</span>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# SIMULACIÓN DE AHORRO
# ═══════════════════════════════════════════════════════════════
def render_simulacion_ahorro(data: list):
    st.markdown('<div class="ais-section-title">Simulación de ahorro potencial</div>', unsafe_allow_html=True)

    monto_alto = sum(s.get("monto_reclamado", 0) for s in data if s.get("nivel_riesgo") == "Alto")
    monto_total = sum(s.get("monto_reclamado", 0) for s in data)

    tasa = st.slider(
        "Tasa estimada de detección de fraude (%)",
        min_value=5, max_value=80,
        value=st.session_state.get("ahorro_tasa", 30),
        step=5,
        key="slider_ahorro",
        help="Porcentaje de casos de alto riesgo que resultarían ser fraude real"
    )
    st.session_state["ahorro_tasa"] = tasa

    ahorro = monto_alto * (tasa / 100)
    pct_total = (ahorro / monto_total * 100) if monto_total else 0

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="savings-card">
          <div class="savings-label">Ahorro potencial estimado</div>
          <div class="savings-amount">${ahorro:,.0f}</div>
          <div class="savings-label">{pct_total:.1f}% del monto total reclamado</div>
        </div>""", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="info-card">
          <div class="info-card-title">Desglose</div>
          <table style="width:100%;font-size:12px;border-collapse:collapse;">
            <tr><td style="color:#64748B;padding:4px 0;">Monto total reclamado</td>
                <td style="color:#E2E8F0;text-align:right;font-weight:600;">${monto_total:,.0f}</td></tr>
            <tr><td style="color:#64748B;padding:4px 0;">Monto en casos Alto Riesgo</td>
                <td style="color:#F43F5E;text-align:right;font-weight:600;">${monto_alto:,.0f}</td></tr>
            <tr><td style="color:#64748B;padding:4px 0;">Tasa de detección aplicada</td>
                <td style="color:#818CF8;text-align:right;font-weight:600;">{tasa}%</td></tr>
            <tr style="border-top:1px solid rgba(99,102,241,0.2);">
                <td style="color:#22D3EE;padding:8px 0 0;font-weight:600;">Ahorro estimado</td>
                <td style="color:#22D3EE;text-align:right;font-weight:700;font-size:14px;padding-top:8px;">${ahorro:,.0f}</td></tr>
          </table>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# ANÁLISIS NLP DEL RECLAMO
# ═══════════════════════════════════════════════════════════════
def render_analisis_nlp(s: dict, todos_los_datos: list):
    st.markdown('<div class="ais-section-title" style="margin-top:18px;">Análisis del texto del reclamo</div>', unsafe_allow_html=True)

    narrativa = s.get("narrativa", s.get("descripcion", ""))
    if not narrativa:
        st.markdown('<p style="color:#475569;font-size:12px;">Sin narrativa disponible para analizar.</p>', unsafe_allow_html=True)
        return

    # Palabras clave de riesgo
    keywords_riesgo = [
        "urgente", "inmediato", "accidente", "robo", "quemado", "destruido",
        "total", "pérdida total", "hospitalización", "emergencia", "colisión",
        "fallecido", "fallecimiento", "incendio", "fraude", "vehículo",
    ]
    palabras_detectadas = [w for w in keywords_riesgo if w.lower() in narrativa.lower()]

    # Similitud simple con otros casos (longitud de narrativa compartida)
    similares = []
    for otro in todos_los_datos:
        if otro.get("id_siniestro") == s.get("id_siniestro"):
            continue
        otra_narr = otro.get("narrativa", otro.get("descripcion", ""))
        if otra_narr and len(otra_narr) > 20:
            palabras_comunes = set(narrativa.lower().split()) & set(otra_narr.lower().split())
            score_sim = len(palabras_comunes) / max(len(narrativa.split()), 1)
            if score_sim > 0.3:
                similares.append((otro.get("id_siniestro", "?"), score_sim))
    similares = sorted(similares, key=lambda x: x[1], reverse=True)[:3]

    col_nlp1, col_nlp2 = st.columns(2)
    with col_nlp1:
        st.markdown(f"""
        <div class="info-card">
          <div class="info-card-title">Palabras clave detectadas ({len(palabras_detectadas)})</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;">
            {''.join([f'<span style="background:rgba(244,63,94,0.12);color:#FB7185;border:1px solid rgba(244,63,94,0.25);padding:3px 9px;border-radius:12px;font-size:11px;">{w}</span>' for w in palabras_detectadas]) if palabras_detectadas else '<span style="color:#475569;font-size:12px;">Sin palabras de alerta detectadas</span>'}
          </div>
          <div style="margin-top:14px;">
            <div style="font-size:10px;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Narrativa completa</div>
            <div style="font-size:12px;color:#94A3B8;line-height:1.7;font-style:italic;">"{narrativa[:300]}{'...' if len(narrativa) > 300 else ''}"</div>
          </div>
        </div>""", unsafe_allow_html=True)
    with col_nlp2:
        st.markdown(f"""
        <div class="info-card">
          <div class="info-card-title">Casos con narrativa similar</div>
          {''.join([f'<div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(30,41,59,0.4);"><span style="font-family:Space Mono,monospace;font-size:11px;color:#818CF8;">{sid}</span><span style="font-size:11px;color:#F59E0B;">{sim*100:.0f}% similar</span></div>' for sid, sim in similares]) if similares else '<p style="color:#475569;font-size:12px;margin-top:8px;">Sin casos similares detectados en el portafolio actual.</p>'}
          <div style="margin-top:14px;padding:10px;background:rgba(99,102,241,0.06);border-radius:8px;">
            <div style="font-size:11px;color:#64748B;">Longitud de narrativa: <span style="color:#CBD5E1;">{len(narrativa)} caracteres</span></div>
            <div style="font-size:11px;color:#64748B;margin-top:4px;">Palabras únicas: <span style="color:#CBD5E1;">{len(set(narrativa.lower().split()))}</span></div>
          </div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# CLAIMS TABLE
# ═══════════════════════════════════════════════════════════════
def render_table(data: list):
    if not data:
        st.markdown('<p style="color:#475569;font-size:13px;padding:20px 0;">Sin registros.</p>', unsafe_allow_html=True)
        return

    rows = ""
    for s in data:
        nivel = s.get("nivel_riesgo", "Bajo")
        score = s.get("score_riesgo", 0)
        alertas = s.get("alertas", [])
        if isinstance(alertas, str):
            try:
                alertas = json.loads(alertas)
            except Exception:
                alertas = []
        pill = risk_pill_html(nivel)
        bar = score_bar_html(score)
        alert_count = len(alertas)
        alert_badge = (
            f'<span style="background:rgba(244,63,94,0.12);color:#FB7185;'
            f'padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;">'
            f'{alert_count} alertas</span>'
        ) if alert_count else '<span style="color:#334155;font-size:10px;">—</span>'

        rows += f"""
        <tr>
          <td><span class="claim-id">{s.get('id_siniestro','')}</span></td>
          <td style="color:#E2E8F0;">{s.get('cliente','')}</td>
          <td style="color:#94A3B8;">{s.get('ramo', s.get('tipo_siniestro',''))}</td>
          <td class="claim-monto">${s.get('monto_reclamado',0):,.0f}</td>
          <td>{pill}</td>
          <td>{bar}</td>
          <td>{alert_badge}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="claims-table">
      <thead>
        <tr>
          <th>ID Siniestro</th><th>Asegurado</th><th>Ramo</th>
          <th>Monto</th><th>Riesgo</th><th>Score</th>
          <th>Alertas</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# EXPORTACIÓN CSV
# ═══════════════════════════════════════════════════════════════
def render_export_button(data: list):
    if not data:
        return
    df_exp = pd.DataFrame([
        {
            "ID Siniestro": s.get("id_siniestro", ""),
            "Asegurado": s.get("cliente", s.get("id_asegurado", "")),
            "Ramo": s.get("ramo", s.get("tipo_siniestro", "")),
            "Cobertura": s.get("cobertura", ""),
            "Monto Reclamado": s.get("monto_reclamado", 0),
            "Monto Estimado": s.get("monto_estimado", 0),
            "Monto Pagado": s.get("monto_pagado", 0),
            "Estado": s.get("estado", ""),
            "Score Riesgo": s.get("score_riesgo", 0),
            "Nivel Riesgo": s.get("nivel_riesgo", ""),
            "Alertas": "; ".join([a.get("descripcion") if isinstance(a, dict) else str(a) for a in (json.loads(s.get("alertas", "[]")) if isinstance(s.get("alertas"), str) else s.get("alertas", []))]),
            "Sucursal": s.get("sucursal", ""),
            "Fecha Ocurrencia": s.get("fecha_ocurrencia", s.get("fecha_incidente", "")),
            "Fecha Reporte": s.get("fecha_reporte", ""),
            "Proveedor": s.get("proveedor", ""),
        }
        for s in data
    ])
    csv_buffer = io.StringIO()
    df_exp.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Exportar reporte de auditoría (.csv)",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name=f"AIS_reporte_auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ═══════════════════════════════════════════════════════════════
# ALERTS PANEL (right sidebar) — con explicación automática
# ═══════════════════════════════════════════════════════════════
def render_alerts_panel(data: list):
    st.markdown('<div class="ais-section-title">🔴 Alertas activas</div>', unsafe_allow_html=True)
    altos = [s for s in data if s.get("nivel_riesgo") == "Alto"][:6]
    if not altos:
        st.markdown('<p style="color:#475569;font-size:12px;">Sin alertas activas.</p>', unsafe_allow_html=True)
    for s in altos:
        alertas = s.get("alertas", [])
        if isinstance(alertas, str):
            try:
                alertas = json.loads(alertas)
            except Exception:
                alertas = []
        
        # Encontrar descripción de la primera alerta roja o la primera disponible
        desc = "Anomalía crítica detectada"
        for a in alertas:
            if isinstance(a, dict):
                if a.get("severidad") == "roja":
                    desc = a.get("descripcion")
                    break
        else:
            if alertas:
                desc = alertas[0].get("descripcion") if isinstance(alertas[0], dict) else str(alertas[0])
                
        explicacion = generar_explicacion_alerta(s)
        st.markdown(f"""
        <div class="alert-item">
            <div class="alert-id">{s.get('id_siniestro')} · ${s.get('monto_reclamado',0):,.0f}</div>
            <div class="alert-desc">🚨 {desc}</div>
            <div class="alert-explain">{explicacion}</div>
        </div>""", unsafe_allow_html=True)

    medios = [s for s in data if s.get("nivel_riesgo") == "Medio"][:4]
    if medios:
        st.markdown('<div class="ais-section-title" style="margin-top:16px;">🟡 En seguimiento</div>', unsafe_allow_html=True)
        for s in medios:
            alertas = s.get("alertas", [])
            if isinstance(alertas, str):
                try:
                    alertas = json.loads(alertas)
                except Exception:
                    alertas = []
            
            desc = "Requiere revisión rutinaria"
            for a in alertas:
                if isinstance(a, dict):
                    if a.get("severidad") == "amarilla":
                        desc = a.get("descripcion")
                        break
            else:
                if alertas:
                    desc = alertas[0].get("descripcion") if isinstance(alertas[0], dict) else str(alertas[0])
                    
            st.markdown(f"""
            <div class="alert-item medium">
                <div class="alert-id">{s.get('id_siniestro')} · {s.get('cliente','')}</div>
                <div class="alert-desc">🟡 {desc}</div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# CHAT PANEL
# ═══════════════════════════════════════════════════════════════
def render_chat_panel(data: list):
    st.markdown('<div class="ais-section-title">🤖 Asistente AIS</div>', unsafe_allow_html=True)

    sugerencias = [
        "¿Qué casos priorizar?",
        "¿Narrativas similares?",
        "Resumen de riesgo alto",
        "¿Proveedor con más alertas?",
    ]
    cols = st.columns(2)
    for i, sug in enumerate(sugerencias):
        with cols[i % 2]:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state["chat_history"].append({"role": "user", "content": sug})
                _send_chat(sug, data)
                st.rerun()

    if st.session_state["chat_history"]:
        st.markdown('<div style="margin:12px 0 8px;border-top:1px solid rgba(99,102,241,0.15);padding-top:12px;"></div>', unsafe_allow_html=True)
        for msg in st.session_state["chat_history"][-8:]:
            role = msg["role"]
            label = "ANALISTA" if role == "user" else "AIS IA"
            cls = "user" if role == "user" else "ai"
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:{'flex-end' if role=='user' else 'flex-start'};margin-bottom:8px;">
              <div class="chat-label">{label}</div>
              <div class="chat-bubble {cls}">{msg['content']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        query = st.text_input("", placeholder="Consulta al asistente AIS…", label_visibility="collapsed")
        sent = st.form_submit_button("Enviar →", use_container_width=True, type="primary")
        if sent and query.strip():
            st.session_state["chat_history"].append({"role": "user", "content": query})
            _send_chat(query, data)
            st.rerun()

    if st.button("🗑 Limpiar conversación", key="clear_chat"):
        st.session_state["chat_history"] = []
        st.rerun()


def _send_chat(pregunta: str, data: list):
    try:
        from src.ai_agent.claims_agent import agente_responder
        historial_prev = [m for m in st.session_state["chat_history"][:-1]]
        respuesta = agente_responder(pregunta, historial_prev, data)
    except Exception as e:
        respuesta = f"Error en el agente: {str(e)[:100]}"
    st.session_state["chat_history"].append({"role": "assistant", "content": respuesta})


# ═══════════════════════════════════════════════════════════════
# NEW CLAIM FORM
# ═══════════════════════════════════════════════════════════════
def render_new_claim_form():
    import random
    st.markdown("""
    <div style="background:#0B1120;border:1px solid rgba(99,102,241,0.25);
    border-radius:14px;padding:28px 32px;margin-bottom:24px;
    box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 0 1px rgba(99,102,241,0.05);">
    <div style="font-family:Syne,sans-serif;font-weight:800;font-size:16px;color:#fff;
    margin-bottom:22px;display:flex;align-items:center;gap:10px;">
    🛡️ Registrar nuevo siniestro
    <span style="font-size:10px;color:#818CF8;font-family:'Space Mono',monospace;
    font-weight:400;background:rgba(99,102,241,0.1);
    padding:3px 8px;border-radius:4px;border:1px solid rgba(99,102,241,0.2);">ANÁLISIS AUTOMÁTICO AIS</span>
    </div>
    </div>""", unsafe_allow_html=True)

    # Restauramos st.form para evitar que la interfaz se bloquee/recargue en cada interacción
    with st.form("nuevo_siniestro_form", clear_on_submit=True, border=True):
        st.markdown('<p style="color:#818CF8;font-weight:600;font-size:13px;margin-bottom:12px;">1. Información del Siniestro</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            # Auto-generar ID Siniestro
            nuevo_id_sin = "SIN-2024-0001"
            if supabase:
                try:
                    res_ultimo_sin = supabase.table("siniestros").select("id_siniestro").execute()
                    if res_ultimo_sin.data:
                        max_num = 0
                        year_str = "2024"
                        for row in res_ultimo_sin.data:
                            id_val = row.get("id_siniestro", "")
                            partes = id_val.split("-")
                            if len(partes) >= 3 and partes[2].isdigit():
                                num = int(partes[2])
                                if num > max_num:
                                    max_num = num
                                    year_str = partes[1]
                        nuevo_id_sin = f"SIN-{year_str}-{(max_num + 1):04d}"
                except Exception:
                    pass
            
            id_sin  = st.text_input("ID Siniestro", value=nuevo_id_sin, disabled=True)
            id_aseg = st.text_input("ID Asegurado (Debe existir previamente)", placeholder="ASEG-2024-0001")
            
            ramo = st.selectbox("Ramo del siniestro", ["Vehículos", "Salud", "Vida", "Hogar", "Generales", "Otro"])
            cobertura = st.selectbox("Cobertura / Tipo", ["Choque", "Robo", "Atención médica", "Incendio", "Daño", "Otro"])
            
            placa_vehiculo = st.text_input("Placa del Vehículo", placeholder="ABC-1234 (Dejar vacío si no aplica)").upper()

            monto   = st.number_input("Monto reclamado ($ USD)", min_value=0.0, step=100.0)
            monto_est = st.number_input("Monto estimado ($ USD)", min_value=0.0, step=100.0)
        with c2:
            monto_pag = st.number_input("Monto pagado ($ USD)", min_value=0.0, step=100.0)
            estado = st.selectbox("Estado del siniestro", ["Reserva", "Pago Total", "Pago Parcial", "Anticipo", "Negativa", "Cierre Sin Consecuencia", "Liquidado"])
            fecha_ocurrencia = st.date_input("Fecha del incidente (ocurrencia)", value=date.today())
            fecha_reporte    = st.date_input("Fecha del reporte (notificación)", value=date.today())
            sucursal = st.selectbox("Sucursal", [
                "Sucursal Quito Norte", "Sucursal Guayaquil Centro", "Sucursal Cuenca El Sagrario",
                "Sucursal Manta Tarqui", "Sucursal Portoviejo Real", "Sucursal Loja Sur",
                "Sucursal Ambato Ficoa"
            ])
            beneficiario = st.selectbox("Beneficiario", ["Taller", "Clínica", "Perito", "Asegurado", "Otro"])
            proveedor = st.text_input("Proveedor / Taller (Opcional)", placeholder="Nombre del taller/clínica")

        descripcion = st.text_area("Descripción detallada del reclamo (narrativa)",
                                   placeholder="Describe detalladamente el incidente reportado…",
                                   height=80)

        st.markdown('<hr style="margin:20px 0 18px;border-top:1px solid rgba(99,102,241,0.15);">', unsafe_allow_html=True)
        st.markdown('<p style="color:#818CF8;font-weight:600;font-size:13px;margin-bottom:12px;">2. Documentación Adjunta</p>', unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            tipos_doc_opciones = [
                "Factura de reparación", "Denuncia policial", "Parte policial", 
                "Peritaje", "Fotografías", "Informe técnico", "Fotografías de daño", 
                "Historia clínica", "Exámenes", "Factura hospitalaria", "Orden médica", "Otros"
            ]
            tipo_doc  = st.multiselect("Tipo de Documento", tipos_doc_opciones, default=[])
            entregado = st.selectbox("¿Entregado?", ["Sí", "No"])
            legible   = st.selectbox("¿Legible?", ["Sí", "No"])
        with c4:
            fecha_emision_doc   = st.date_input("Fecha de emisión del documento", value=date.today())
            inconsistencia_doc  = st.selectbox("¿Inconsistencia detectada?", ["No", "Sí"])
            observacion_doc     = st.text_input("Observación del Documento", placeholder="Observación sobre el documento...")

        col_s, col_c = st.columns([2, 1])
        with col_s:
            submitted = st.form_submit_button("🔍 Registrar, Analizar y Guardar", use_container_width=True, type="primary")
        with col_c:
            cancelar  = st.form_submit_button("Cancelar", use_container_width=True)

        if cancelar:
            st.session_state["show_form"] = False
            st.rerun()

        if submitted:
            placa_vehiculo = placa_vehiculo.strip()
            if not placa_vehiculo:
                placa_vehiculo = "N/A"

            if not id_aseg or not descripcion:
                st.error("ID Asegurado y Descripción son obligatorios.")
            elif not tipo_doc:
                st.error("Debe adjuntar al menos un Tipo de Documento.")
            elif not supabase:
                st.error("Error: Supabase no está configurado. Configura el archivo .env para continuar.")
            else:
                with st.spinner("Validando IDs en Supabase y ejecutando análisis AIS…"):
                    res_aseg = supabase.table("asegurados").select("*").eq("id_asegurado", id_aseg).execute()
                    if not res_aseg.data:
                        st.error(f"❌ El ID de Asegurado '{id_aseg}' no existe en la base de datos.")
                        return

                    asegurado_obj = res_aseg.data[0]
                    nombre_asegurado = asegurado_obj.get("nombre", "Desconocido")
                    ciudad_asegurado = asegurado_obj.get("ciudad", "Ecuador")
                    reclamos_previos = asegurado_obj.get("reclamos_ultimos_12_meses", 0)

                    res_pol = supabase.table("polizas").select("*").eq("id_asegurado", id_aseg).execute()
                    if not res_pol.data:
                        st.error(f"❌ El asegurado '{id_aseg}' no tiene ninguna póliza registrada.")
                        return
                    
                    polizas_activas = [p for p in res_pol.data if p.get("estado", "").lower() == "activa"]
                    poliza_obj = polizas_activas[0] if polizas_activas else res_pol.data[0]
                    id_pol = poliza_obj.get("id_poliza")

                    fp_inicio = datetime.strptime(poliza_obj.get("fecha_inicio"), "%Y-%m-%d").date()
                    fp_fin    = datetime.strptime(poliza_obj.get("fecha_fin"),   "%Y-%m-%d").date()
                    dias_inicio = (fecha_ocurrencia - fp_inicio).days
                    dias_fin    = (fp_fin - fecha_ocurrencia).days
                    dias_entre  = (fecha_reporte - fecha_ocurrencia).days

                    historial_count_res = supabase.table("siniestros").select("id", count="exact").eq("id_asegurado", id_aseg).execute()
                    siniestros_en_bd = historial_count_res.count if historial_count_res.count is not None else 0
                    
                    # Incluimos el siniestro actual que se está registrando (+1)
                    total_historial  = siniestros_en_bd + reclamos_previos + 1

                    prov_id = None
                    if proveedor:
                        res_prov = supabase.table("proveedores").select("id").ilike("nombre", f"%{proveedor}%").limit(1).execute()
                        if res_prov.data:
                            prov_id = res_prov.data[0].get("id")

                    nuevo = {
                        "id_siniestro": id_sin,
                        "id_poliza": id_pol,
                        "id_asegurado": id_aseg,
                        "ramo": ramo,
                        "cobertura": cobertura,
                        "placa_vehiculo": placa_vehiculo,
                        "fecha_ocurrencia": str(fecha_ocurrencia),
                        "fecha_reporte": str(fecha_reporte),
                        "monto_reclamado": float(monto),
                        "monto_estimado": float(monto_est),
                        "monto_pagado": float(monto_pag),
                        "estado": estado,
                        "sucursal": sucursal,
                        "descripcion": descripcion,
                        "documentos_completos": entregado == "Sí",
                        "beneficiario": beneficiario,
                        "dias_desde_inicio_poliza": dias_inicio,
                        "dias_desde_fin_poliza": dias_fin,
                        "dias_entre_ocurrencia_reporte": dias_entre,
                        "historial_siniestros_asegurado": total_historial,
                        "etiqueta_fraude_simulada": 0,
                        "cliente": nombre_asegurado,
                        "tipo_siniestro": cobertura,
                        "fecha_incidente": str(fecha_ocurrencia),
                        "fecha_poliza": str(fp_inicio),
                        "ciudad": ciudad_asegurado,
                        "proveedor": proveedor or "Sin especificar",
                        "proveedor_id": prov_id,
                        "historial_reclamos": total_historial,
                        "narrativa": descripcion,
                        "score_riesgo": 0,
                        "nivel_riesgo": "Bajo",
                        "alertas": [],
                    }

                    try:
                        from src.rules.fraud_rules import evaluar_todas_las_reglas
                        from src.models.fraud_model import calcular_score_ml

                        # Contar reclamos con el mismo proveedor en st.session_state["siniestros"]
                        conteo_prov = 1
                        if proveedor:
                            conteo_prov = sum(1 for x in st.session_state.get("siniestros", []) if x.get("proveedor") == proveedor)

                        # Enriquecer contexto para las 10 señales
                        contexto_reglas = {
                            "conteo_proveedor": conteo_prov,
                            "ramo_poliza": poliza_obj.get("ramo"),
                            "placa_vehiculo_asegurado": poliza_obj.get("placa_vehiculo_asegurado", "N/A"),
                            "narrativas_previas": [x.get("narrativa", x.get("descripcion", "")) for x in st.session_state.get("siniestros", [])],
                            "siniestros_vehiculo": random.choice([0, 0, 2, 3]) if "reincidente" in descripcion.lower() or "historial" in descripcion.lower() else 0,
                            "siniestros_rc": 3 if "responsabilidad civil" in cobertura.lower() or "rc" in cobertura.lower() else 0,
                            "hora_siniestro": 3 if "madrugada" in descripcion.lower() else -1,
                            "fecha_emision_anterior": inconsistencia_doc == "Sí"
                        }
                        
                        res_reglas = evaluar_todas_las_reglas(nuevo, contexto_reglas)
                        res_ml     = calcular_score_ml(nuevo)

                        # Si se activaron alertas rojas críticas, elevar score mínimo
                        tiene_rojas = any(a.get("severidad") == "roja" for a in res_reglas["alertas_detalle"])
                        score_base = int(res_reglas["score_reglas"] * 0.50 + res_ml["score_ml"] * 0.50)
                        if tiene_rojas:
                            score_base = max(score_base, 75)

                        score_final  = min(max(score_base, 5), 99)
                        nivel_riesgo = "Alto" if score_final >= 70 else "Medio" if score_final >= 40 else "Bajo"

                        nuevo["score_riesgo"]  = score_final
                        nuevo["nivel_riesgo"]  = nivel_riesgo
                        nuevo["alertas"]       = res_reglas["alertas_detalle"]  # Estructurado
                        nuevo["score_reglas"]  = res_reglas["score_reglas"]
                        nuevo["score_ml"]      = res_ml["score_ml"]
                        nuevo["score_nlp"]     = 30 if tiene_rojas else 0
                        nuevo["similitud_max"] = 0.85 if tiene_rojas else 0.2
                        nuevo["es_anomalia"]   = score_final >= 60
                        nuevo["explicacion_ia"] = generar_explicacion_alerta(nuevo)
                    except Exception as scoring_err:
                        st.warning(f"Error en pipeline AIS: {scoring_err}")
                        nuevo["score_riesgo"] = 10
                        nuevo["nivel_riesgo"] = "Bajo"
                        nuevo["alertas"]      = []

                    alertas_raw = nuevo["alertas"]
                    nuevo["alertas"] = json.dumps(nuevo["alertas"])
                    res_ins_sin = supabase.table("siniestros").insert(nuevo).execute()
                    if not res_ins_sin.data:
                        st.error("Error insertando el siniestro en Supabase.")
                        return

                    for t_doc in tipo_doc:
                        nuevo_doc = {
                            "id_siniestro": id_sin,
                            "tipo_documento": t_doc,
                            "entregado": entregado == "Sí",
                            "legible": legible == "Sí",
                            "fecha_emision": str(fecha_emision_doc),
                            "inconsistencia_detectada": inconsistencia_doc == "Sí",
                            "observacion": observacion_doc or "Registrado manualmente."
                        }
                        supabase.table("documentos").insert(nuevo_doc).execute()

                    nuevo["alertas"] = alertas_raw
                    st.session_state["siniestros"].insert(0, nuevo)
                    st.session_state["show_form"] = False

                    if nuevo["nivel_riesgo"] == "Alto":
                        st.error(f"⚠️ Siniestro registrado · Riesgo **ALTO** (score {nuevo['score_riesgo']}). {nuevo.get('explicacion_ia','')}")
                    elif nuevo["nivel_riesgo"] == "Medio":
                        st.warning(f"🟡 Siniestro registrado · Riesgo **MEDIO** (score {nuevo['score_riesgo']}).")
                    else:
                        st.success(f"✅ Siniestro registrado · Riesgo **BAJO** (score {nuevo['score_riesgo']}).")
                    
                    st.info(f"🔄 Historial sincronizado: El asegurado {id_aseg} tiene ahora un total de {total_historial} siniestros registrados.")
                    
                    cargar_datos_demo.clear()
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
# DETAIL VIEW — con explicación automática y NLP
# ═══════════════════════════════════════════════════════════════
def render_detail(s: dict, todos: list):
    st.markdown(f"""
    <div style="background:#0B1120;border:1px solid rgba(99,102,241,0.18);
    border-radius:12px;padding:22px 26px;margin-bottom:18px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
        <div>
            <div style="font-family:'Space Mono',monospace;font-size:11px;color:#818CF8;margin-bottom:4px;">{s.get('id_siniestro')}</div>
            <div style="font-family:Syne,sans-serif;font-weight:700;font-size:20px;color:#fff;">{s.get('cliente', s.get('id_asegurado',''))}</div>
        </div>
        <div>{risk_pill_html(s.get('nivel_riesgo','Bajo'))}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;font-size:13px;">
        <div><span style="color:#64748B;">Ramo:</span> <span style="color:#CBD5E1;">{s.get('ramo', s.get('tipo_siniestro',''))}</span></div>
        <div><span style="color:#64748B;">Monto:</span> <span style="color:#E2E8F0;font-weight:600;">${s.get('monto_reclamado',0):,.0f}</span></div>
        <div><span style="color:#64748B;">Incidente:</span> <span style="color:#CBD5E1;">{s.get('fecha_ocurrencia', s.get('fecha_incidente',''))}</span></div>
        <div><span style="color:#64748B;">Póliza:</span> <span style="color:#CBD5E1;">{s.get('id_poliza', s.get('fecha_poliza',''))}</span></div>
        <div><span style="color:#64748B;">Historial:</span> <span style="color:#CBD5E1;">{s.get('historial_reclamos', s.get('historial_siniestros_asegurado',0))} siniestros</span></div>
    </div>
    <div style="margin-top:14px;padding-top:14px;border-top:1px solid rgba(99,102,241,0.12);">
        <div style="font-size:10px;color:#64748B;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.08em;">Narrativa</div>
        <div style="font-size:13px;color:#94A3B8;line-height:1.7;">{s.get('narrativa', s.get('descripcion', '—'))}</div>
    </div>
    </div>""", unsafe_allow_html=True)

    alertas = s.get("alertas", [])
    if isinstance(alertas, str):
        try:
            import json
            alertas = json.loads(alertas)
        except Exception:
            alertas = []

    if alertas:
        st.markdown('<div class="ais-section-title">Indicadores de riesgo detectados</div>', unsafe_allow_html=True)
        for a in alertas:
            if isinstance(a, dict):
                desc = a.get("descripcion", "")
                sev = a.get("severidad", "roja")
                pts = a.get("puntos", 0)
                cls = "medium" if sev == "amarilla" else ""
                icon = "🟡" if sev == "amarilla" else "🚨"
                pts_str = f" (+{pts} pts)" if pts > 0 else ""
                st.markdown(f'<div class="alert-item {cls}"><div class="alert-desc">{icon} <b>{desc}</b>{pts_str}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-item"><div class="alert-desc">⚡ {a}</div></div>', unsafe_allow_html=True)

    # Explicación automática (INDISPENSABLE)
    st.markdown('<div class="ais-section-title" style="margin-top:18px;">Explicación automática de la alerta</div>', unsafe_allow_html=True)
    try:
        features = {
            "score_final": s.get("score_riesgo", 0),
            "nivel_riesgo": s.get("nivel_riesgo", "Bajo"),
            "alertas": alertas,
            "nlp": {"max_similitud": 0},
        }
        explicacion_modulo = obtener_explicacion_ia(s.get("id_siniestro"), s, features)
    except Exception:
        explicacion_modulo = None

    # Siempre mostramos la explicación automática generada
    explicacion_auto = generar_explicacion_alerta(s)
    
    st.markdown("""
    <div style="background-color:rgba(234, 179, 8, 0.1); border-left: 4px solid #EAB308; padding: 12px 16px; margin-top:18px; margin-bottom: 12px; border-radius: 4px;">
        <p style="color:#FDE047; font-size:12px; margin:0; line-height:1.5;">
            ⚖️ <b>Aviso Ético y Operativo:</b> Las alertas y el análisis generados por la IA representan únicamente indicadores preventivos de riesgo y deben ser validados por un analista humano. El sistema puede generar falsos positivos y sus hallazgos no constituyen una acusación ni determinación definitiva de fraude.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="explain-card">
        <h5>🤖 Análisis AI de Factores</h5>
        <p>{explicacion_auto}</p>
        {f'<p style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(99,102,241,0.15);font-size:12px;color:#64748B;">{explicacion_modulo}</p>' if explicacion_modulo else ''}
    </div>""", unsafe_allow_html=True)

    # Análisis NLP
    render_analisis_nlp(s, todos)


# ═══════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_dashboard():
    if not st.session_state.get("siniestros"):
        with st.spinner("Cargando portafolio de siniestros..."):
            st.session_state["siniestros"] = cargar_datos_demo()
            
    data = st.session_state["siniestros"]
    render_topbar(data)

    left_col, right_col = st.columns([3.2, 1])

    with left_col:
        # KPIs rediseñadas
        render_kpis(data)

        st.markdown('<div class="ais-separator"></div>', unsafe_allow_html=True)

        # Controls row — export moved to topbar
        c_btn, c_filter, c_search = st.columns([1.5, 1.2, 3])
        with c_btn:
            if st.button("＋ Nuevo siniestro", key="open_form_btn", use_container_width=True, type="primary"):
                st.session_state["show_form"] = not st.session_state.get("show_form", False)
        with c_filter:
            filtro = st.selectbox("Filtrar", ["Todos", "Alto", "Medio", "Bajo"],
                                  key="risk_filter", label_visibility="collapsed")
        with c_search:
            busqueda = st.text_input("", placeholder="🔍 Buscar por asegurado, ID…",
                                     label_visibility="collapsed")

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        # Form inline
        if st.session_state.get("show_form", False):
            render_new_claim_form()

        # Filter data
        filtered = data
        if filtro != "Todos":
            filtered = [s for s in data if s.get("nivel_riesgo") == filtro]
        if busqueda:
            q = busqueda.lower()
            filtered = [s for s in filtered if
                        q in s.get("cliente", "").lower() or
                        q in s.get("id_siniestro", "").lower() or
                        q in s.get("tipo_siniestro", "").lower() or
                        q in s.get("ramo", "").lower()]
        # Sort dynamically by risk score descending (Alto -> Medio -> Bajo)
        filtered = sorted(filtered, key=lambda x: x.get("score_riesgo", 0), reverse=True)

        # Tabs principales
        tab_table, tab_charts, tab_detail, tab_red, tab_ranking, tab_ahorro = st.tabs([
            "📋 Tabla de Siniestros",
            "📊 Análisis Visual",
            "🔍 Detalle & NLP",
            "🕸️ Red de Relaciones",
            "🏆 Ranking Proveedores",
            "💡 Simulación Ahorro",
        ])

        with tab_table:
            st.markdown(f'<p style="font-size:11px;color:#475569;margin-bottom:14px;">{len(filtered)} registros mostrados</p>', unsafe_allow_html=True)
            render_table(filtered)

        with tab_charts:
            render_charts(filtered)

        with tab_detail:
            if filtered:
                opciones = {f"{s.get('id_siniestro','?')} — {s.get('cliente', s.get('id_asegurado',''))}": s for s in filtered}
                sel = st.selectbox("Seleccionar siniestro", list(opciones.keys()), label_visibility="collapsed")
                if sel:
                    render_detail(opciones[sel], data)
            else:
                st.markdown('<p style="color:#475569;font-size:13px;padding:20px 0;">Sin registros para mostrar.</p>', unsafe_allow_html=True)

        with tab_red:
            render_red_relaciones(data)

        with tab_ranking:
            render_ranking_proveedores(data)

        with tab_ahorro:
            render_simulacion_ahorro(data)

    with right_col:
        tab_alerts, tab_chat = st.tabs(["🔴 Alertas", "🤖 IA Chat"])
        with tab_alerts:
            render_alerts_panel(data)
        with tab_chat:
            render_chat_panel(data)


# ═══════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════
if st.session_state.get("logged_in"):
    page_dashboard()
else:
    page_login()
