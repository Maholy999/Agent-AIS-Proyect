# Arquitectura del Sistema — FraudIA Claims

## Visión general

FraudIA adopta una arquitectura modular en capas, diseñada para ser extensible y mantenible.

```
┌─────────────────────────────────────────────────────┐
│                  CAPA PRESENTACIÓN                  │
│              Streamlit Dashboard (main.py)          │
│   Login → Dashboard → Formulario → Chat IA         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               CAPA DE ANÁLISIS                      │
│  ┌───────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Reglas   │ │ ML Model │ │   NLP / Similitud │   │
│  │ (rules/)  │ │(models/) │ │   (features/)    │   │
│  └─────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
│        └────────────┴────────────────┘             │
│                      │ build_features.py            │
│              score_final ponderado                  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               CAPA IA / LLM                         │
│   explain_score.py  ←→  claims_agent.py             │
│   OpenAI GPT-4o-mini / modo local fallback          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               CAPA DATOS                            │
│   PostgreSQL / Supabase / JSON demo local            │
└─────────────────────────────────────────────────────┘
```

## Flujo de análisis de un siniestro

1. **Ingreso** → El analista completa el formulario en el dashboard
2. **Reglas** → `fraud_rules.py` evalúa condiciones de negocio (monto, póliza, historial)
3. **ML** → `fraud_model.py` ejecuta Isolation Forest y genera score de anomalía
4. **NLP** → `build_features.py` compara la narrativa contra el historial (Jaccard/transformers)
5. **Consolidación** → `construir_features_completas()` pondera los tres scores (40/45/15%)
6. **Explicación** → `explain_score.py` llama al LLM para generar narrativa explicativa
7. **Persistencia** → El siniestro con resultados se almacena en BD y actualiza el dashboard

## Ponderación del score final

| Componente | Peso | Descripción |
|---|---|---|
| Reglas de negocio | 40% | Heurísticas expertas configurables |
| Isolation Forest | 45% | Anomalías estadísticas en features numéricas |
| Similitud NLP | 15% | Patrones repetitivos en narrativas |

## Escalabilidad

- Los módulos son independientes y testables por separado
- El pipeline puede extenderse con nuevos modelos sin modificar la UI
- La BD está diseñada para millones de registros con índices apropiados
- El agente IA puede conectarse a modelos adicionales mediante configuración
