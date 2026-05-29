"""
data/synthetic/add_additional_claims.py
Agrega 6 nuevos siniestros a la base de datos de Supabase,
asignándolos a usuarios existentes (por ejemplo, Mónica del Rocío Andrade)
para simular reincidencias reales.
"""

import os
import sys
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

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

def main():
    print("=== Añadiendo Siniestros Reincidentes Reales ===")
    
    # 1. Obtener todos los siniestros para encontrar pólizas, asegurados y proveedores
    res_sin = supabase.table("siniestros").select("*").execute()
    siniestros_existentes = res_sin.data if res_sin.data else []
    
    if not siniestros_existentes:
        print("No hay siniestros existentes. Corre primero insert_demo_supabase.py")
        return
        
    print(f"Siniestros existentes encontrados: {len(siniestros_existentes)}")

    # Filtrar siniestros existentes para escoger a quién duplicarle
    # Trataremos de encontrar a 'Mónica del Rocío Andrade' u otros
    candidatos_reincidencia = []
    
    monica_claims = [s for s in siniestros_existentes if "mónica" in s.get("cliente", "").lower() or "monica" in s.get("cliente", "").lower()]
    cristiano_claims = [s for s in siniestros_existentes if "cristiano" in s.get("cliente", "").lower()]
    
    if monica_claims:
        candidatos_reincidencia.append(monica_claims[0])
    if cristiano_claims:
        candidatos_reincidencia.append(cristiano_claims[0])
        
    # Llenar el resto de candidatos hasta tener 6 nuevos siniestros que asignar
    # Queremos que Mónica tenga 3 adicionales (total 4)
    # y otros 3 se asignen aleatoriamente a otra persona (ej. Cristiano u otro)
    
    asignaciones = []
    if monica_claims:
        asignaciones.extend([monica_claims[0]] * 3) # Mónica tendrá 4 siniestros
    
    # Añadimos otros 3 reclamos a otras personas aleatorias (o Cristiano si existe)
    otros = [s for s in siniestros_existentes if s.get("id_asegurado") != (monica_claims[0].get("id_asegurado") if monica_claims else "")]
    if otros:
        random.shuffle(otros)
        asignaciones.append(otros[0]) # tendrá 2
        asignaciones.append(otros[0]) # tendrá 3
        if len(otros) > 1:
            asignaciones.append(otros[1]) # tendrá 2
    else:
        # Si no hay otros, todos a Mónica
        asignaciones.extend([monica_claims[0]] * 3)
        
    # Si por alguna razón la lista es menor a 6 (ej. DB vacía), rellenamos con aleatorios
    while len(asignaciones) < 6:
        asignaciones.append(random.choice(siniestros_existentes))

    print(f"Preparando {len(asignaciones)} nuevos siniestros...")
    
    # Obtener el máximo ID de siniestro para generar los nuevos
    max_id = 0
    for s in siniestros_existentes:
        id_str = s.get("id_siniestro", "")
        try:
            num = int(id_str.split("-")[-1])
            if num > max_id:
                max_id = num
        except:
            pass

    # Insertar los nuevos siniestros
    for i, claim_base in enumerate(asignaciones):
        max_id += 1
        nuevo_id = f"SIN-2024-{str(max_id).zfill(4)}"
        
        # Clonar datos base
        nuevo_sin = dict(claim_base)
        
        # Limpiar IDs de base de datos
        for key in ["id", "created_at", "updated_at", "fecha_registro"]:
            if key in nuevo_sin:
                del nuevo_sin[key]
                
        nuevo_sin["id_siniestro"] = nuevo_id
        
        # Variar las fechas para que no sea exactamente el mismo día
        try:
            fecha_oc_base = datetime.strptime(claim_base["fecha_ocurrencia"], "%Y-%m-%d")
            nueva_fecha_oc = fecha_oc_base + timedelta(days=random.randint(15, 120))
            if nueva_fecha_oc > datetime.now():
                nueva_fecha_oc = datetime.now() - timedelta(days=random.randint(1, 5))
            nuevo_sin["fecha_ocurrencia"] = nueva_fecha_oc.strftime("%Y-%m-%d")
            nuevo_sin["fecha_incidente"] = nueva_fecha_oc.strftime("%Y-%m-%d")
            
            nueva_fecha_rep = nueva_fecha_oc + timedelta(days=random.randint(0, 5))
            nuevo_sin["fecha_reporte"] = nueva_fecha_rep.strftime("%Y-%m-%d")
        except:
            pass
            
        # Variar montos y narrativas
        nuevo_sin["monto_reclamado"] = float(claim_base["monto_reclamado"]) * random.uniform(0.5, 1.5)
        nuevo_sin["monto_estimado"] = nuevo_sin["monto_reclamado"] * 0.9
        nuevo_sin["estado"] = "Reserva"
        nuevo_sin["monto_pagado"] = 0
        
        narrativas_adicionales = [
            "El vehículo sufrió un raspón en el parqueadero del centro comercial. No hay responsables identificados.",
            "Rotura de parabrisas por impacto de piedra en la carretera a la costa.",
            "Daño por filtración de agua debido a las fuertes lluvias de la madrugada.",
            "Atención médica de emergencia por intoxicación alimentaria leve."
        ]
        nuevo_sin["descripcion"] = random.choice(narrativas_adicionales)
        nuevo_sin["narrativa"] = nuevo_sin["descripcion"]
        
        # Los scores e historial los seteamos por defecto, el script de update_claims_database.py los corregirá
        nuevo_sin["historial_reclamos"] = 0
        nuevo_sin["historial_siniestros_asegurado"] = 0
        nuevo_sin["score_riesgo"] = 10
        nuevo_sin["nivel_riesgo"] = "Bajo"
        nuevo_sin["alertas"] = "[]"
        nuevo_sin["explicacion_ia"] = "Siniestro añadido por simulación de reincidencia."

        res = supabase.table("siniestros").insert(nuevo_sin).execute()
        if res.data:
            print(f"   + Insertado Siniestro: {nuevo_id} para {nuevo_sin['cliente']}")
            
            # Agregar un documento de prueba también
            supabase.table("documentos").insert({
                "id_siniestro": nuevo_id,
                "tipo_documento": "Formulario de Reclamo",
                "entregado": True,
                "legible": True,
                "fecha_emision": nuevo_sin["fecha_reporte"],
                "inconsistencia_detectada": False,
                "observacion": "Generado automáticamente"
            }).execute()
        else:
            print(f"   - Error insertando {nuevo_id}")

    print("\n¡6 siniestros de reincidencia insertados!")
    print("Nota: Ahora debes correr 'update_claims_database.py' para que se recalculen las frecuencias y alertas.")

if __name__ == "__main__":
    main()
