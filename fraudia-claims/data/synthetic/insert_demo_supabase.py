"""
data/synthetic/insert_demo_supabase.py
Script para poblar la base de datos de Supabase con 20 registros demo realistas
coherentes orientados a Ecuador con ramos, pólizas, asegurados, proveedores,
siniestros y documentos.
"""

import os
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
import sys
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, ".env"))

# Clean Supabase URL
supabase_url = os.environ.get("SUPABASE_URL", "")
if "/rest/v1/" in supabase_url:
    supabase_url = supabase_url.replace("/rest/v1/", "").strip("/")
supabase_key = os.environ.get("SUPABASE_KEY", "")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL o SUPABASE_KEY no configurados en el archivo .env")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

# Configuration for Ecuador
CIUDADES_ECUADOR = [
    "Quito", "Guayaquil", "Cuenca", "Santo Domingo", "Machala", 
    "Durán", "Manta", "Portoviejo", "Loja", "Ambato"
]

SUCURSALES = [
    "Sucursal Quito Norte", "Sucursal Guayaquil Centro", "Sucursal Cuenca El Sagrario",
    "Sucursal Manta Tarqui", "Sucursal Portoviejo Real", "Sucursal Loja Sur",
    "Sucursal Ambato Ficoa"
]

NOMBRES_SINTETICOS = [
    "José Miguel Chimbo", "María Beatriz Espinoza", "Luis Alfredo Carranza", "Diana Carolina Vaca",
    "Carlos Andrés Zambrano", "Ana Lucía Freire", "Juan Fernando Galarza", "Patricia Elizabeth Ortiz",
    "Pedro Javier Noboa", "Laura Estefanía Mendoza", "Jorge Enrique Morejón", "Gabriela Fernanda Cisneros",
    "Ángel Gabriel Cueva", "Silvia Patricia Guamán", "Christian Rolando Lasso", "Sandra Marina Correa",
    "Héctor Vinicio Jaramillo", "Verónica Alexandra Narváez", "Diego Marcelo Borja", "Mónica del Rocío Andrade"
]

RAMOS = ["Vehículos", "Salud", "Vida", "Hogar", "Generales"]
COBERTURAS = {
    "Vehículos": ["Choque", "Robo", "Otro"],
    "Salud": ["Atención médica", "Otro"],
    "Vida": ["Otro"],
    "Hogar": ["Incendio", "Robo", "Daño", "Otro"],
    "Generales": ["Daño", "Otro"]
}

PROVEEDORES_LIST = [
    {"id_prov": "PROV-EC-001", "nombre": "Talleres Casabaca Quito", "tipo": "Taller", "ciudad": "Quito"},
    {"id_prov": "PROV-EC-002", "nombre": "Clínica Kennedy Guayaquil", "tipo": "Clínica", "ciudad": "Guayaquil"},
    {"id_prov": "PROV-EC-003", "nombre": "AutoServicios Continental Cuenca", "tipo": "Taller", "ciudad": "Cuenca"},
    {"id_prov": "PROV-EC-004", "nombre": "Clínica Santa Inés Cuenca", "tipo": "Clínica", "ciudad": "Cuenca"},
    {"id_prov": "PROV-EC-005", "nombre": "Taller El Chamo Portoviejo", "tipo": "Taller", "ciudad": "Portoviejo"},
    {"id_prov": "PROV-EC-006", "nombre": "Clínica Metropolitana Quito", "tipo": "Clínica", "ciudad": "Quito"},
    {"id_prov": "PROV-EC-007", "nombre": "Peritajes del Ecuador", "tipo": "Perito", "ciudad": "Quito"},
    {"id_prov": "PROV-EC-008", "nombre": "Taller Multimarcas Manta", "tipo": "Taller", "ciudad": "Manta"},
    {"id_prov": "PROV-EC-009", "nombre": "Clínica Hospital del Día Loja", "tipo": "Clínica", "ciudad": "Loja"},
    {"id_prov": "PROV-EC-010", "nombre": "Hogar Seguro Cía. Ltda.", "tipo": "Otro", "ciudad": "Ambato"}
]

NARRATIVAS_NORMALES = [
    "El asegurado reporta colisión lateral por parte de otro vehículo que no respetó el disco PARE en la Av. Eloy Alfaro, Quito. Se adjunta informe policial.",
    "Ingreso de emergencia del asegurado por apendicitis aguda en la Clínica Kennedy, Guayaquil. Atención médica urgente prestada.",
    "Robo parcial de accesorios (espejos y mascarilla) del auto estacionado frente al domicilio del asegurado en Cuenca. Denuncia ante Fiscalía adjunta.",
    "Daños menores por filtración de agua debido a rotura de tubería interna en cocina del domicilio en Loja. Reportado el mismo día.",
    "El asegurado solicita reembolso de gastos médicos por consulta de control general y exámenes de laboratorio autorizados previamente.",
    "Colisión trasera menor en tráfico denso en Av. de las Américas, Cuenca. Daños leves en parachoques trasero. Se llegó a acuerdo amistoso.",
    "Cortocircuito en caja de disyuntores de residencia en Portoviejo que causó daños a electrodomésticos en la cocina. Técnico avala desperfecto."
]

NARRATIVAS_SOSPECHOSAS = [
    "El vehículo fue hurtado en horas de la madrugada mientras se encontraba parqueado en calle oscura de Guayaquil. No existen testigos ni grabaciones del incidente y las llaves originales se extraviaron el día anterior.",
    "Colisión con auto desconocido que se dio a la fuga a alta velocidad en la autopista Terminal-Pascuales. El asegurado no recuerda placas ni características.",
    "El asegurado reporta robo total del vehículo que supuestamente dejó parqueado en el centro de Quito. No obstante, las cámaras de seguridad del sector no registran el paso del auto en el rango de horas indicado.",
    "Daño total por incendio de vehículo en vía perimetral de Durán. El incendio comenzó súbitamente en la cabina y el asegurado no pudo apagarlo. Reporte de bomberos tiene inconsistencias de origen del fuego.",
    "El asegurado reporta que un televisor de alta gama y joyas desaparecieron de su hogar en Quito tras supuesta intrusión sin forzamiento de cerraduras."
]

def clear_tables():
    print("Limpiando tablas previas...")
    # We clean using API, but to avoid RLS issues or restrictions, we delete records
    try:
        supabase.table("documentos").delete().neq("id_documento", 0).execute()
        supabase.table("siniestros").delete().neq("id", 0).execute()
        supabase.table("polizas").delete().neq("id_poliza", "").execute()
        supabase.table("asegurados").delete().neq("id_asegurado", "").execute()
        supabase.table("proveedores").delete().neq("id", 0).execute()
        print("Tablas limpias.")
    except Exception as e:
        print(f"Error limpiando algunas tablas (es normal si están vacías o no tienen registros): {e}")

def main():
    clear_tables()

    random.seed(42)

    # 1. Insertar Proveedores
    print("\nCreando e Insertando Proveedores...")
    proveedores_db = []
    for i, p in enumerate(PROVEEDORES_LIST):
        prov_data = {
            "id_proveedor": p["id_prov"],
            "nombre": p["nombre"],
            "tipo": p["tipo"],
            "ciudad": p["ciudad"],
            "reclamos_asociados": random.randint(5, 50),
            "monto_promedio_reclamado": float(random.randint(1200, 8500)),
            "porcentaje_casos_observados": float(random.choice([0.0, 5.0, 10.0, 20.0, 35.0])),
            "antiguedad": random.randint(1, 10),
            "total_siniestros": random.randint(5, 50),
            "alertas_activas": random.choice([0, 1, 2, 3]),
            "score_riesgo": random.randint(5, 60)
        }
        res = supabase.table("proveedores").insert(prov_data).execute()
        if res.data:
            proveedores_db.append(res.data[0])
            print(f"   + Insertado: {p['nombre']}")

    # 2. Insertar Asegurados
    print("\nCreando e Insertando Asegurados Sintéticos...")
    asegurados_db = []
    for i, nombre in enumerate(NOMBRES_SINTETICOS):
        id_asegurado = f"ASEG-{2024}-{str(i+1).zfill(4)}"
        aseg_data = {
            "id_asegurado": id_asegurado,
            "nombre": nombre,
            "segmento": random.choice(["Estándar", "VIP", "Corporativo"]),
            "antiguedad": random.randint(1, 12),
            "ciudad": random.choice(CIUDADES_ECUADOR),
            "numero_polizas": random.randint(1, 3),
            "reclamos_ultimos_12_meses": random.randint(0, 4),
            "mora_actual": random.choice([False, False, False, True]), # 25% prob of mora
            "score_cliente_simulado": random.randint(40, 95)
        }
        res = supabase.table("asegurados").insert(aseg_data).execute()
        if res.data:
            asegurados_db.append(res.data[0])
            print(f"   + Insertado Asegurado: {nombre} ({id_asegurado})")

    # 3. Insertar Pólizas
    print("\nCreando e Insertando Pólizas...")
    polizas_db = []
    for i, aseg in enumerate(asegurados_db):
        id_poliza = f"POL-{2024}-{str(i+1).zfill(4)}"
        
        # Coherencia de fecha: inicio entre 2023 y 2025
        inicio_atras = random.randint(120, 600)
        fecha_inicio = datetime.now() - timedelta(days=inicio_atras)
        fecha_fin = fecha_inicio + timedelta(days=365) # Vigencia de 1 año
        
        ramo = random.choice(RAMOS)
        
        pol_data = {
            "id_poliza": id_poliza,
            "id_asegurado": aseg["id_asegurado"],
            "ramo": ramo,
            "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
            "prima": float(random.randint(250, 4500)),
            "suma_asegurada": float(random.randint(5000, 150000)),
            "deducible": float(random.randint(100, 1500)),
            "canal_venta": random.choice(["Directo", "Bróker", "Digital", "Banca Seguros"]),
            "ciudad": aseg["ciudad"],
            "estado_poliza": "Activa" if fecha_fin > datetime.now() else "Vencida"
        }
        res = supabase.table("polizas").insert(pol_data).execute()
        if res.data:
            polizas_db.append(res.data[0])
            print(f"   + Insertada Póliza: {id_poliza} (Ramo: {ramo})")

    # 4. Insertar Siniestros
    print("\nCreando e Insertando Siniestros...")
    siniestros_db = []
    
    # We will generate exactly 20 claims
    # Let's ensure some are suspicious (e.g. indices 2, 5, 8, 11, 14) and 
    # a few have ramo mismatch for demo!
    for i in range(20):
        aseg = asegurados_db[i % len(asegurados_db)]
        pol = polizas_db[i % len(polizas_db)]
        
        # Decide if this is a ramo mismatch (e.g. index 3 and 9)
        es_descalce_ramo = i in [3, 9]
        
        ramo_siniestro = pol["ramo"]
        if es_descalce_ramo:
            # Change claim ramo so it doesn't match policy ramo
            available_ramos = [r for r in RAMOS if r != pol["ramo"]]
            ramo_siniestro = random.choice(available_ramos)
            
        coberturas_disp = COBERTURAS.get(ramo_siniestro, ["Otro"])
        cobertura = random.choice(coberturas_disp)
        
        # Fechas del siniestro: entre 2024 y mayo 2026
        # Debe ocurrir mientras la póliza esté activa (para casos normales)
        # O puede ocurrir con inconsistencia
        fp_inicio = datetime.strptime(pol["fecha_inicio"], "%Y-%m-%d")
        fp_fin = datetime.strptime(pol["fecha_fin"], "%Y-%m-%d")
        
        # Siniestro ocurrió entre el inicio de la póliza y hoy
        max_days = min((datetime.now() - fp_inicio).days, (fp_fin - fp_inicio).days)
        if max_days <= 1:
            max_days = 30
        dias_ocurrencia = random.randint(1, max_days)
        fecha_ocurrencia = fp_inicio + timedelta(days=dias_ocurrencia)
        
        # Aseguramos que caiga entre 2024 y Mayo 2026
        if fecha_ocurrencia.year < 2024:
            fecha_ocurrencia = datetime(2024, random.randint(1, 12), random.randint(1, 28))
        elif fecha_ocurrencia > datetime(2026, 5, 27):
            fecha_ocurrencia = datetime(2026, random.randint(1, 4), random.randint(1, 28))
            
        # Fecha reporte: entre 0 y 15 días después
        dias_reporte = random.randint(0, 15)
        fecha_reporte = fecha_ocurrencia + timedelta(days=dias_reporte)
        
        es_sospechoso = i in [2, 5, 8, 11, 14]
        
        monto_reclamado = random.randint(500, 15000) if not es_sospechoso else random.randint(16000, 65000)
        monto_estimado = monto_reclamado * random.choice([0.9, 0.95, 1.0, 1.05])
        
        estado_siniestro = random.choice(["Reserva", "Liquidado", "Pago Parcial"])
        if es_sospechoso:
            estado_siniestro = "Reserva"
            
        monto_pagado = 0
        if estado_siniestro == "Liquidado":
            monto_pagado = monto_estimado
        elif estado_siniestro == "Pago Parcial":
            monto_pagado = monto_estimado * 0.5
            
        # Select provider matching claim type or general
        taller_tipo = "Taller" if ramo_siniestro == "Vehículos" else "Clínica" if ramo_siniestro == "Salud" else "Otro"
        prov_matching = [p for p in proveedores_db if p["tipo"] == taller_tipo]
        if not prov_matching:
            prov_matching = proveedores_db
        prov = random.choice(prov_matching)
        
        desc = random.choice(NARRATIVAS_SOSPECHOSAS) if es_sospechoso else random.choice(NARRATIVAS_NORMALES)
        
        # Calculate days differences
        dias_inicio = (fecha_ocurrencia - fp_inicio).days
        dias_fin = (fp_fin - fecha_ocurrencia).days
        dias_entre = (fecha_reporte - fecha_ocurrencia).days
        
        historial_previo = aseg["reclamos_ultimos_12_meses"]
        
        # Build claim dictionary for scoring logic
        nuevo_sin = {
            "id_siniestro": f"SIN-2024-{str(i+1).zfill(4)}",
            "id_poliza": pol["id_poliza"],
            "id_asegurado": aseg["id_asegurado"],
            "ramo": ramo_siniestro,
            "cobertura": cobertura,
            "fecha_ocurrencia": fecha_ocurrencia.strftime("%Y-%m-%d"),
            "fecha_reporte": fecha_reporte.strftime("%Y-%m-%d"),
            "monto_reclamado": float(monto_reclamado),
            "monto_estimado": float(monto_estimado),
            "monto_pagado": float(monto_pagado),
            "estado": estado_siniestro,
            "sucursal": random.choice(SUCURSALES),
            "descripcion": desc,
            "documentos_completos": not es_sospechoso,
            "beneficiario": prov["tipo"],
            "dias_desde_inicio_poliza": dias_inicio,
            "dias_desde_fin_poliza": dias_fin,
            "dias_entre_ocurrencia_reporte": dias_entre,
            "historial_siniestros_asegurado": historial_previo,
            "etiqueta_fraude_simulada": 1 if es_sospechoso or es_descalce_ramo else 0,
            
            # Compatibility fields
            "cliente": aseg["nombre"],
            "tipo_siniestro": cobertura,
            "fecha_incidente": fecha_ocurrencia.strftime("%Y-%m-%d"),
            "fecha_poliza": pol["fecha_inicio"],
            "ciudad": aseg["ciudad"],
            "proveedor": prov["nombre"],
            "proveedor_id": prov["id"],
            "historial_reclamos": historial_previo,
            "narrativa": desc
        }
        
        # Calculate score using our business rules and heuristic ML
        # Incorporating the new Ramo Inconsistency rule in the evaluation!
        try:
            from src.rules.fraud_rules import evaluar_todas_las_reglas
            from src.models.fraud_model import calcular_score_ml
            
            contexto_reglas = {"conteo_proveedor": random.randint(1, 4), "ramo_poliza": pol["ramo"]}
            res_reglas = evaluar_todas_las_reglas(nuevo_sin, contexto_reglas)
            res_ml = calcular_score_ml(nuevo_sin) # fallback heuristic
            
            score_final = int(res_reglas["score_reglas"] * 0.45 + res_ml["score_ml"] * 0.45 + (30 if es_sospechoso else 0) * 0.1)
            score_final = min(max(score_final, 5), 99)
            
            nivel_riesgo = "Alto" if score_final >= 70 else "Medio" if score_final >= 40 else "Bajo"
            alertas = res_reglas["alertas"]
            if es_sospechoso and "Monto reclamado excede percentil 90" not in alertas:
                alertas.append("Monto reclamado es inusualmente elevado")
                
            nuevo_sin["score_riesgo"] = score_final
            nuevo_sin["nivel_riesgo"] = nivel_riesgo
            nuevo_sin["alertas"] = json.dumps(alertas)
            nuevo_sin["score_reglas"] = res_reglas["score_reglas"]
            nuevo_sin["score_ml"] = res_ml["score_ml"]
            nuevo_sin["score_nlp"] = 30 if es_sospechoso else 0
            nuevo_sin["similitud_max"] = 0.85 if es_sospechoso else 0.23
            nuevo_sin["es_anomalia"] = score_final >= 60
            nuevo_sin["explicacion_ia"] = f"Análisis preliminar completado. Riesgo {nivel_riesgo} debido a los indicadores: {', '.join(alertas) if alertas else 'Ninguno destacado'}."
        except Exception as err:
            print(f"Error scoring claim {i}: {err}")
            nuevo_sin["score_riesgo"] = 15
            nuevo_sin["nivel_riesgo"] = "Bajo"
            nuevo_sin["alertas"] = "[]"
            
        res = supabase.table("siniestros").insert(nuevo_sin).execute()
        if res.data:
            siniestros_db.append(res.data[0])
            print(f"   + Insertado Siniestro: {nuevo_sin['id_siniestro']} (Riesgo: {nuevo_sin['nivel_riesgo']}, Score: {nuevo_sin['score_riesgo']})")

    # 5. Insertar Documentos
    print("\nCreando e Insertando Documentos...")
    tipos_documento = ["Factura de Reparación", "Cédula del Asegurado", "Informe de Tránsito", "Historia Clínica", "Prescripción Médica"]
    for i, sin in enumerate(siniestros_db):
        num_docs = random.randint(1, 3)
        for d in range(num_docs):
            doc_data = {
                "id_siniestro": sin["id_siniestro"],
                "tipo_documento": random.choice(tipos_documento),
                "entregado": True,
                "legible": random.choice([True, True, True, False]), # 25% prob of illegible
                "fecha_emision": (datetime.strptime(sin["fecha_ocurrencia"], "%Y-%m-%d") - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d"),
                "inconsistencia_detectada": random.choice([False, False, False, True]) if sin["score_riesgo"] >= 50 else False,
                "observacion": "Verificado e ingresado en sistema."
            }
            supabase.table("documentos").insert(doc_data).execute()
            
    print("\nCarga inicial de 20 registros demo de Ecuador en Supabase COMPLETADA con éxito!")

if __name__ == "__main__":
    main()
