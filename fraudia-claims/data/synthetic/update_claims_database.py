"""
data/synthetic/update_claims_database.py
Script para reevaluar y actualizar masivamente todos los siniestros en Supabase
usando el nuevo motor de reglas de negocio y señales de fraude críticas de AIS.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Configuración de Rutas de Importación
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

load_dotenv(os.path.join(ROOT, ".env"))

supabase_url = os.environ.get("SUPABASE_URL", "")
if "/rest/v1/" in supabase_url:
    supabase_url = supabase_url.replace("/rest/v1/", "").strip("/")
supabase_key = os.environ.get("SUPABASE_KEY", "")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL o SUPABASE_KEY no configurados en .env")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)


def generar_explicacion_alerta_local(s: dict) -> str:
    nivel = s.get("nivel_riesgo", "Bajo")
    score = s.get("score_riesgo", 0)
    monto = s.get("monto_reclamado", 0)
    historial = s.get("historial_reclamos", s.get("historial_siniestros_asegurado", 0))
    dias_entre = s.get("dias_entre_ocurrencia_reporte", 0)
    ramo = s.get("ramo", s.get("tipo_siniestro", "desconocido"))

    partes = []

    alertas = s.get("alertas", [])
    if isinstance(alertas, str):
        import json
        try:
            alertas = json.loads(alertas)
        except:
            alertas = []

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
        partes.append("• **Inconsistencia Fuerte:** Se identificaron características irregulares en la documentación física que deben ser autenticadas por el equipo pericial.")
        
    if "dinámica imposible" in desc_alertas or "incoherente" in desc_alertas:
        partes.append("• **Contradicción Física:** La declaración de los hechos muestra discrepancias frente a las marcas físicas de los daños.")

    if len(alertas) >= 4 and nivel != "Bajo":
        partes.append(f"• **Confluencia de Señales:** Se identifican {len(alertas)} factores atípicos simultáneos, lo que amerita un escalamiento del caso para una revisión integral.")

    return "<br><br>".join(partes)


def main():
    print("=== Iniciando Actualización del Portafolio AIS ===")
    
    # 1. Obtener todos los siniestros
    print("Consultando siniestros en Supabase...")
    res_sin = supabase.table("siniestros").select("*").execute()
    if not res_sin.data:
        print("No se encontraron siniestros en la base de datos.")
        return
    
    siniestros = res_sin.data
    print(f"Se encontraron {len(siniestros)} siniestros para reevaluar.")

    # 2. Obtener todos los documentos
    print("Consultando documentos para verificar inconsistencias...")
    res_doc = supabase.table("documentos").select("*").execute()
    documentos = res_doc.data if res_doc.data else []
    print(f"Se encontraron {len(documentos)} documentos registrados.")

    # Crear mapa de inconsistencias de documentos por id_siniestro
    inconsistencias_docs = {}
    for doc in documentos:
        id_sin = doc.get("id_siniestro")
        inconsistente = doc.get("inconsistencia_detectada", False)
        if inconsistente:
            inconsistencias_docs[id_sin] = True

    # 3. Obtener todas las pólizas para validar ramo
    print("Consultando pólizas...")
    res_pol = supabase.table("polizas").select("id_poliza, ramo").execute()
    polizas_map = {p["id_poliza"]: p["ramo"] for p in res_pol.data} if res_pol.data else {}

    # Pre-calcular narrativas para detectar duplicados
    todas_narrativas = [s.get("narrativa", s.get("descripcion", "")) for s in siniestros]
    todas_narrativas = [n for n in todas_narrativas if n and len(n) > 10]

    from src.rules.fraud_rules import evaluar_todas_las_reglas
    from src.models.fraud_model import calcular_score_ml

    actualizados = 0

    for s in siniestros:
        id_sin = s.get("id_siniestro")
        id_pol = s.get("id_poliza")
        
        # Enriquecer siniestro con inconsistencia de documentos
        if id_sin in inconsistencias_docs:
            s["inconsistencia_detectada"] = True

        # --- Calcular historial REAL del asegurado en la base de datos ---
        id_aseg = s.get("id_asegurado")
        if id_aseg:
            historial_real = sum(1 for x in siniestros if x.get("id_asegurado") == id_aseg)
        else:
            historial_real = 1
        
        s["historial_reclamos"] = historial_real
        s["historial_siniestros_asegurado"] = historial_real
        # -----------------------------------------------------------------

        # Crear contexto de reglas
        ramo_pol = polizas_map.get(id_pol, "")
        
        # Contar siniestros con el mismo proveedor
        prov_name = s.get("proveedor", "")
        conteo_prov = 1
        if prov_name and prov_name != "Sin especificar":
            conteo_prov = sum(1 for x in siniestros if x.get("proveedor") == prov_name)
            
        # Simular otros conteos para enriquecer las señales
        # (por ejemplo, siniestros de vehículo o de RC previos)
        siniestros_vehiculo = 0
        if "reincidente" in str(s.get("narrativa", "")).lower():
            siniestros_vehiculo = 3
        elif s.get("score_riesgo", 0) > 60:
            siniestros_vehiculo = 2
            
        siniestros_rc = 0
        if "responsabilidad civil" in str(s.get("cobertura", "")).lower() or "rc" in str(s.get("cobertura", "")).lower():
            siniestros_rc = 3 if s.get("score_riesgo", 0) > 70 else 1

        contexto_reglas = {
            "ramo_poliza": ramo_pol,
            "conteo_proveedor": conteo_prov,
            "narrativas_previas": [n for n in todas_narrativas if n != s.get("narrativa", s.get("descripcion", ""))],
            "siniestros_vehiculo": siniestros_vehiculo,
            "siniestros_rc": siniestros_rc,
            "hora_siniestro": 3 if "madrugada" in str(s.get("narrativa", "")).lower() else -1,
            "siniestros_asegurado": s["historial_reclamos"]
        }

        # Evaluar nuevas reglas y señales de fraude
        res_reglas = evaluar_todas_las_reglas(s, contexto_reglas)
        res_ml = calcular_score_ml(s)

        # Score final unificado
        # Si tiene alertas rojas graves, el score se eleva
        tiene_rojas = any(a.get("severidad") == "roja" for a in res_reglas["alertas_detalle"])
        alertas_amarillas = sum(1 for a in res_reglas["alertas_detalle"] if a.get("severidad") == "amarilla")
        score_base = int(res_reglas["score_reglas"] * 0.50 + res_ml["score_ml"] * 0.50)
        
        # --- LÓGICA DE ACUMULACIÓN DE RIESGO ---
        # Si hay demasiadas alertas amarillas, sube el riesgo automáticamente
        if alertas_amarillas >= 6:
            score_base = max(score_base, 75) # Riesgo Alto por acumulación masiva
        elif alertas_amarillas >= 4:
            score_base = max(score_base, 55) # Riesgo Medio por acumulación
        
        if tiene_rojas:
            score_base = max(score_base, 75) # Elevar a riesgo alto si hay reglas críticas rojas

        score_final = min(max(score_base, 5), 99)
        nivel_riesgo = "Alto" if score_final >= 70 else "Medio" if score_final >= 40 else "Bajo"

        s["score_riesgo"] = score_final
        s["nivel_riesgo"] = nivel_riesgo
        s["alertas"] = json.dumps(res_reglas["alertas_detalle"])  # Guardar alertas detalladas como JSON
        s["score_reglas"] = res_reglas["score_reglas"]
        s["score_ml"] = res_ml["score_ml"]
        s["es_anomalia"] = score_final >= 60
        s["explicacion_ia"] = generar_explicacion_alerta_local(s)

        # Actualizar en Supabase
        update_data = {
            "score_riesgo": s["score_riesgo"],
            "nivel_riesgo": s["nivel_riesgo"],
            "alertas": s["alertas"],
            "score_reglas": s["score_reglas"],
            "score_ml": s["score_ml"],
            "es_anomalia": s["es_anomalia"],
            "explicacion_ia": s["explicacion_ia"],
            "historial_reclamos": s["historial_reclamos"],
            "historial_siniestros_asegurado": s["historial_siniestros_asegurado"]
        }

        res_upd = supabase.table("siniestros").update(update_data).eq("id_siniestro", id_sin).execute()
        if res_upd.data:
            actualizados += 1
            print(f"   [OK] Siniestro {id_sin} actualizado con Score {score_final} ({nivel_riesgo}) · {len(res_reglas['alertas_detalle'])} alertas.")
        else:
            print(f"   [ERROR] No se pudo actualizar siniestro {id_sin}")

    print(f"\nProceso finalizado. Se actualizaron con éxito {actualizados} de {len(siniestros)} siniestros.")


if __name__ == "__main__":
    main()
