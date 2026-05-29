# AIS - Análisis Inteligente de Siniestros

## 1. Descripción del Sistema
**AIS - Análisis Inteligente de Siniestros** es una plataforma avanzada diseñada para la automatización, evaluación y detección de fraudes en siniestros de seguros. El sistema resuelve el problema de la revisión manual exhaustiva al procesar y analizar reclamos en tiempo real, identificando patrones anómalos, calculando un *score* de riesgo y generando alertas tempranas para los analistas.

El sistema maneja diversos ramos de seguros, incluyendo:
- Vehículos
- Salud
- Vida
- Hogar
- Generales
- Otros

## 2. Características Principales
- **Dashboard Interactivo:** Interfaz corporativa para la gestión y visualización de siniestros, alertas y KPIs.
- **Motor de Reglas de Negocio:** Evaluación automática de reglas críticas y señales de alerta configuradas.
- **Scoring Híbrido:** Combinación de reglas duras, modelos de Machine Learning (ML) y Procesamiento de Lenguaje Natural (NLP).
- **Agente de IA Conversacional:** Un asistente basado en LLM que permite interactuar con el portafolio de siniestros y obtener explicaciones detalladas.
- **Explicabilidad (XAI):** Generación de justificaciones textuales automáticas sobre por qué un siniestro ha sido catalogado con cierto nivel de riesgo.
- **Generación de Reportes:** Exportación de análisis detallados.

## 3. Arquitectura General
El sistema implementa una arquitectura monolítica moderna enfocada en datos:
- **Frontend / UI:** Desarrollado íntegramente en Streamlit, proporcionando una interfaz rica e interactiva.
- **Backend / Lógica Core:** Integrado en la misma aplicación Python, maneja el procesamiento de datos, feature engineering, y la invocación de modelos/LLMs.
- **Base de Datos:** PostgreSQL administrado a través de Supabase.
- **Flujo de Comunicación:** La UI (Streamlit) se conecta directamente a la base de datos (PostgreSQL/Supabase) y consume APIs externas (OpenAI) para las capacidades generativas.

## 4. Tecnologías Utilizadas
- **Frontend & App Core:** Streamlit, Plotly.
- **Análisis de Datos y ML:** Pandas, NumPy, Scikit-learn, SciPy, Joblib.
- **NLP & IA:** OpenAI API (gpt-4o-mini), Sentence-Transformers.
- **Base de Datos e Infraestructura:** PostgreSQL, Supabase, SQLAlchemy, psycopg2.
- **Utilidades:** python-dotenv, ReportLab (generación de PDFs).

## 5. Estructura del Proyecto
```text
fraudia-claims/
├── data/
│   └── synthetic/          # Scripts y datos generados para simulación
├── docs/                   # Documentación técnica y esquemas de BD
├── src/
│   ├── ai_agent/           # Lógica del agente conversacional LLM
│   ├── app/                # Interfaz principal (main.py en Streamlit)
│   ├── explainability/     # Módulo para generar explicaciones textuales del score
│   ├── features/           # Construcción y procesamiento de características (Feature Engineering)
│   ├── models/             # Modelos predictivos de Machine Learning
│   └── rules/              # Motor de reglas de negocio y señales de fraude
├── tests/                  # Pruebas automatizadas
├── .env.example            # Plantilla de variables de entorno
├── requirements.txt        # Dependencias del proyecto
└── migrations.sql          # Scripts de migración de base de datos
```

## 6. Módulos Funcionales
- **Dashboard Principal:** Visualización de KPIs, ranking de alertas, y listado general de siniestros.
- **Motor de Riesgo (Scoring):** Consolida puntuaciones de reglas, ML y NLP para determinar el nivel de riesgo (Bajo, Medio, Alto).
- **Motor Antifraude (Reglas):** Evalúa el contexto del siniestro contra patrones conocidos de fraude.
- **Auditoría y Explicabilidad:** Genera textos comprensibles justificando las alertas y puntuaciones obtenidas.
- **Agente IA (Chat):** Permite a los analistas realizar consultas en lenguaje natural sobre el portafolio actual y siniestros específicos.

## 7. Reglas Antifraude Implementadas
El motor de reglas detecta automáticamente múltiples escenarios, divididos en **Reglas Críticas** (inconsistencias severas) y **Señales de Fraude** (acumuladores de riesgo):

**Reglas Críticas:**
- **PTxRB:** Reclamos de Pérdida Total por Robo con alta probabilidad de inconsistencia.
- **Falsificación Documental:** Evidencia o indicios de documentos adulterados o firmas dudosas.
- **Lista Restrictiva:** Asegurados, beneficiarios o proveedores coincidentes en listas de exclusión.
- **Dinámica Imposible:** Narrativas físicamente incoherentes (ej. colisión frontal con daños solo traseros).
- **Borde de Vigencia:** Siniestros ocurridos a menos de 48 horas del inicio o fin de la póliza.
- **Demora Atípica (Robo):** Notificación de robo con más de 4 días de demora.
- **Narrativa Clonada:** Descripción idéntica o copiada de otros siniestros históricos.
- **Inconsistencia de Placa y Ramo:** Discrepancias entre los datos del vehículo/ramo asegurado y el siniestro reportado.

**Señales de Alerta (Ponderadas):**
- Demoras generales en denuncias.
- Frecuencia elevada de siniestralidad del asegurado o vehículo.
- Concentración anómala en coberturas de Responsabilidad Civil.
- Falta de documentación soporte obligatoria.
- Inconsistencias en horarios de ocurrencia (madrugada sin testigos).
- Siniestros graves contra objetos fijos sin terceros identificados.

## 8. Base de Datos
La persistencia de datos se maneja en PostgreSQL. Las tablas principales incluyen:
- `usuarios`: Gestión de accesos y roles (admin, analista, supervisor).
- `asegurados` & `polizas`: Información central de los clientes y sus coberturas.
- `proveedores`: Talleres, clínicas y otros servicios involucrados, con seguimiento de su siniestralidad.
- `siniestros`: Tabla transaccional principal con datos del reclamo, resultados de análisis (scores, nivel de riesgo, alertas) y datos de auditoría.
- `documentos`: Control de la documentación entregada por siniestro.
- `historial_alertas`: Registro de alertas activadas por el motor de reglas.
- `conversaciones_ia` & `reportes`: Persistencia de interacciones con el bot y reportes generados.

Se implementa seguridad a nivel de filas (RLS - Row Level Security) gestionada por Supabase.

## 9. Dataset
- **Datos 100% Sintéticos:** El proyecto actual opera con datos generados artificialmente para fines de simulación, demostración y pruebas.
- **Ramos Soportados:** Vehículo, Hogar, Salud, Vida y Generales.

## 10. Variables de Entorno
El sistema requiere configuración mediante un archivo `.env` basado en `.env.example`:
- `DATABASE_URL` / `SUPABASE_URL` / `SUPABASE_KEY`: Credenciales de PostgreSQL y Supabase.
- `OPENAI_API_KEY` / `OPENAI_MODEL`: Acceso y modelo para NLP/XAI (ej. gpt-4o-mini).
- `SECRET_KEY` / `JWT_ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES`: Configuración de seguridad local.

## 11. Instalación y Ejecución
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv .venv` y activarlo.
3. Instalar dependencias: `pip install -r requirements.txt`.
4. Configurar el archivo `.env` con las credenciales correspondientes.
5. Ejecutar la aplicación:
   ```bash
   streamlit run src/app/main.py
   ```

## 12. Estado Actual del Proyecto
- **Funcional:** Interfaz gráfica completa en Streamlit, autenticación (demo), motor de reglas estáticas, explicabilidad basada en IA y agente conversacional.
- **Parcial:** Modelos predictivos de ML (actualmente simulados/basados en scripts de feature engineering y scoring híbrido), integración profunda en tiempo real con sistemas core de seguros (uso actual de mock/synthetic data).
- **Falta:** Despliegue en producción, APIs REST dedicadas si se requiere separar frontend de backend, y entrenamiento de modelos con datos reales.

## 13. Seguridad y Consideraciones
- El acceso a datos se protege mediante roles y políticas RLS de Supabase.
- El análisis automatizado sirve como sistema de **apoyo a la decisión**; la determinación final siempre corresponde a un analista.
- Todo el conjunto de datos de prueba es sintético, garantizando que no se exponga PII (Personal Identifiable Information) real durante el desarrollo y demostración.
