# Arquitectura Técnica — AIS (Análisis Inteligente de Siniestros)

## 1. Objetivo Arquitectónico
El sistema **AIS - Análisis Inteligente de Siniestros** tiene como propósito técnico proporcionar una plataforma unificada, escalable y en tiempo real para la evaluación de reclamos de seguros. El objetivo principal es automatizar la ingesta de datos, aplicar múltiples capas de análisis (reglas duras, Machine Learning y NLP) y presentar los resultados a través de una interfaz interactiva de alta fidelidad para asistir en la toma de decisiones y prevenir fraudes.

## 2. Arquitectura General Actual
La arquitectura actual sigue un patrón de **Monolito de Datos Interactivos**, altamente optimizado para el desarrollo rápido y visualización de datos.

- **Frontend & App Core:** Construido en `Streamlit`. Actúa tanto como interfaz de usuario como controlador de la lógica de negocio.
- **Capa de Análisis (Inteligencia):** Módulos Python integrados que ejecutan Reglas de Negocio, Feature Engineering, y llamadas a LLMs.
- **Base de Datos:** PostgreSQL administrado vía `Supabase`.
- **Servicios Externos:** `OpenAI API` para procesamiento de lenguaje natural y generación de explicaciones.
- *(Nota: No hay un API Gateway ni servicios de Redis implementados en la versión actual. Toda la interacción es directa desde la app Streamlit a la base de datos).*

## 3. Diagrama Arquitectónico

```text
    [Usuario / Analista]
             │
             ▼
┌──────────────────────────┐
│      Frontend (UI)       │
│      (Streamlit App)     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│        App Core          │      │  Servicios Cognitivos    │
│  - Autenticación         │◄────►│  - OpenAI API (LLM)      │
│  - Enrutamiento UI       │      │  - Explicabilidad (XAI)  │
│  - Dashboards (Plotly)   │      │  - Agente Conversacional │
└────────────┬─────────────┘      └──────────────────────────┘
             │
             ▼
┌──────────────────────────┐
│  Motor de Análisis       │
│  - Motor de Reglas       │
│  - Machine Learning      │
│  - Generación de Score   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  Capa de Persistencia    │
│  - PostgreSQL (Supabase) │
│  - Seguridad RLS         │
└──────────────────────────┘
```

## 4. Componentes Principales

### 4.1. Interfaz de Usuario (UI)
- **Tecnología:** Streamlit (`src/app/main.py`).
- **Función:** Provee vistas de Dashboard, Listado de Siniestros, Detalles de Expediente y Chatbot.

### 4.2. Motor de Análisis y Riesgo
- **Tecnología:** Python (Lógica pura, Pandas).
- **Función:** Módulo (`src/rules/fraud_rules.py`) encargado de procesar los atributos del siniestro para detectar irregularidades de forma determinista.
- **Scoring:** Consolida puntos basados en reglas de negocio críticas (ej. Dinámicas Imposibles) y señales acumulativas (ej. Demoras en denuncia, frecuencias altas).

### 4.3. Motor de Machine Learning y NLP
- **Función:** Generación de variables derivadas (`src/features/build_features.py`) y ejecución de modelos predictivos o algoritmos de similitud textual para detectar narrativas clonadas.

### 4.4. Explicabilidad y Agente IA
- **Tecnología:** OpenAI.
- **Función:** 
  - `explain_score.py`: Analiza las alertas detectadas y formula un texto coherente explicando por qué un siniestro se categorizó en cierto nivel de riesgo.
  - `claims_agent.py`: Mantiene contexto del portafolio completo y permite que el analista realice preguntas en texto libre sobre tendencias y riesgos.

### 4.5. Persistencia (Base de Datos)
- **Tecnología:** Supabase / PostgreSQL.
- **Diseño:** Relacional, con índices optimizados para búsquedas (ej. `pg_trgm` para narrativas) y seguridad a nivel de fila (RLS).

## 5. Flujo de Procesamiento de Siniestros
1. **Registro:** El siniestro es insertado en la base de datos (PostgreSQL).
2. **Evaluación de Reglas:** El sistema (`evaluar_todas_las_reglas`) analiza el caso contra las políticas de fraude.
3. **Validación:** Se revisan documentos obligatorios, inconsistencias temporales (ej. fecha de emisión vs accidente) e historiales.
4. **Scoring:** Se asignan puntos por cada alerta disparada. El score va de 0 a 100.
5. **Categorización:** Dependiendo del score final, se clasifica en Riesgo Bajo, Medio o Alto.
6. **Alertas & Explicabilidad:** Se guardan las alertas estructuradas y el LLM genera el texto justificativo de auditoría.
7. **Presentación:** La información consolidada queda disponible en tiempo real en la UI.

## 6. Arquitectura de Datos
- **Tablas Core:** `asegurados`, `polizas`, `proveedores`.
- **Tabla Transaccional:** `siniestros`. Almacena la data dura del accidente más los metadatos generados (scores, alertas JSONB, nivel de riesgo).
- **Manejo Sintético:** El proyecto contiene scripts y archivos locales en `data/synthetic` para popular la base de datos y simular operaciones para entornos de desarrollo y pruebas, evitando comprometer información sensible.

## 7. Reglas Antifraude y Motor de Riesgo (Técnico)
Técnicamente, el motor en `fraud_rules.py` utiliza validaciones lógicas, búsquedas de palabras clave en texto libre (narrativa) y cruces con datos relacionales o de contexto (historiales).

**Factores Considerados:**
- **Inconsistencias Semánticas:** Búsqueda en texto de dinámicas contradictorias (ej. "choque frontal" y "daño trasero").
- **Ventanas Temporales Extremas:** Fechas de siniestro colindantes con el inicio/fin de la vigencia de la póliza.
- **Concentración de Frecuencias:** Conteos anómalos de siniestralidad por individuo, vehículo o proveedor.
- **Listas de Restricción:** Comparación directa con listas negras cargadas en memoria/BD.
**Cálculo:** Cada regla activada tiene una "severidad" (amarilla, roja) y suma "puntos_adicionales" a un score acumulativo que determina el nivel de riesgo final.

## 8. Seguridad
- **Manejo de Credenciales:** Inyección a través de variables de entorno (archivo `.env`).
- **Acceso a Base de Datos:** Uso de `SUPABASE_SERVICE_ROLE_KEY` o similares en backend, restringiendo acceso público a través de Row Level Security (RLS) en la base de PostgreSQL.
- **Autenticación en App:** Gestión propia dentro de la app Streamlit (actualmente usando accesos demo).

## 9. Escalabilidad y Rendimiento
- **Modularidad del Código:** Separación clara entre scripts de interfaz (`app`), lógica de reglas (`rules`), y capacidades cognitivas (`ai_agent`), lo que facilita la futura separación en microservicios si fuese requerido.
- **Separación Futura:** La arquitectura actual fuertemente acoplada a Streamlit (Monolito) puede escalar dividiendo el "Motor de Análisis" hacia una API REST independiente (ej. con FastAPI) para permitir el consumo desde otras plataformas u orígenes de datos.
- *(Nota: No hay Redis implementado; el caché actual se maneja vía decoradores nativos como `@st.cache_data` en memoria).*

## 10. Estado Actual de Arquitectura
- **Implementado e Integrado:** 
  - UI interactiva (Streamlit).
  - Persistencia de datos en Supabase.
  - Motor determinista de reglas críticas y de alertas.
  - Integración funcional con LLMs (Agente y XAI).
- **Prototipo / Parcial:** 
  - Modelos predictivos estadísticos (ML puros para scoring).
  - Autenticación robusta y control de sesión multi-tenant.
- **Ausente:** 
  - Backend API (FastAPI/REST) separada del cliente web.
  - Colas de mensajería (RabbitMQ/Redis) para el procesamiento asíncrono de siniestros pesados.
