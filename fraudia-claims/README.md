# 🛡️ FraudIA Claims

**Plataforma de Análisis de Siniestros y Detección de Fraude para el Sector Asegurador**

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)](https://streamlit.io)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-orange)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ¿Qué es FraudIA?

FraudIA es un sistema inteligente de análisis antifraude para aseguradoras, diseñado para **asistir a analistas humanos** mediante IA, machine learning y NLP. No acusa fraude automáticamente: genera alertas, puntúa riesgos y entrega explicaciones claras para que el analista tome decisiones informadas.

---

## Características principales

| Módulo | Descripción |
|---|---|
| 📊 **Dashboard** | Panel operativo con KPIs, semáforo de riesgo y filtros |
| 🤖 **Agente IA** | Chat conversacional con contexto del portafolio |
| 🧠 **ML** | Isolation Forest para detección de anomalías |
| 📝 **NLP** | Similitud semántica de narrativas |
| ⚡ **Reglas** | Motor de reglas de negocio configurable |
| 📄 **Reportes** | Exportación PDF ejecutiva |

---

## Instalación rápida

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/fraudia-claims.git
cd fraudia-claims

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Ejecutar la aplicación
streamlit run src/app/main.py
```

---

## Estructura del proyecto

```
fraudia-claims/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/              # Datos originales sin procesar
│   ├── processed/        # Modelos ML entrenados
│   └── synthetic/        # Datos demo generados
├── notebooks/            # Exploración y evaluación
├── src/
│   ├── ingestion/        # Carga de datos
│   ├── features/         # NLP y construcción de features
│   ├── rules/            # Motor de reglas de negocio
│   ├── models/           # Isolation Forest + ML
│   ├── explainability/   # Explicaciones con GPT
│   ├── ai_agent/         # Agente conversacional
│   └── app/              # Dashboard Streamlit
├── docs/                 # Documentación técnica + SQL
└── tests/                # Tests unitarios
```

---

## Stack tecnológico

- **Frontend**: Streamlit (tema enterprise custom)
- **ML**: scikit-learn (Isolation Forest)
- **NLP**: sentence-transformers
- **LLM**: OpenAI GPT-4o-mini
- **DB**: PostgreSQL / Supabase
- **Análisis**: pandas, plotly, numpy

---

## Demo

El sistema incluye **20 siniestros precargados** con perfiles de riesgo variados para demostración inmediata. Para acceder: cualquier usuario/contraseña válidos.

---

## ⚠️ Importante

FraudIA es una **herramienta de asistencia**. Ningún resultado automatizado debe interpretarse como acusación o determinación definitiva de fraude. La decisión final siempre corresponde al analista humano.

---

## Licencia

MIT License — Ver [LICENSE](LICENSE)
