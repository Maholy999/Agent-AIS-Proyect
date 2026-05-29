"""
Script de generación de datos sintéticos para AIS.
Pobla Supabase con ~40 asegurados, ~50 pólizas y ~50 siniestros + documentos.
50% de siniestros son de riesgo ALTO con anomalías variadas.

Columnas reales verificadas:
  asegurados : id_asegurado, nombre, ciudad, reclamos_ultimos_12_meses
  polizas    : id_poliza, id_asegurado, ramo, fecha_inicio, fecha_fin,
               prima, suma_asegurada, deducible, canal_venta, ciudad,
               estado_poliza, placa_vehiculo_asegurado
  siniestros : id_siniestro, id_poliza, id_asegurado, ramo, cobertura,
               placa_vehiculo, fecha_ocurrencia, fecha_reporte, monto_reclamado,
               monto_estimado, monto_pagado, estado, sucursal, descripcion,
               documentos_completos, beneficiario, dias_desde_inicio_poliza,
               dias_desde_fin_poliza, dias_entre_ocurrencia_reporte,
               historial_siniestros_asegurado, etiqueta_fraude_simulada,
               cliente, tipo_siniestro, fecha_incidente, fecha_poliza, ciudad,
               proveedor, proveedor_id, historial_reclamos, narrativa,
               score_riesgo, nivel_riesgo, alertas
  documentos : id_siniestro, tipo_documento, entregado, legible,
               fecha_emision, inconsistencia_detectada, observacion
"""

import os
import sys
import random
import uuid
import datetime
from datetime import timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_URL = SUPABASE_URL.replace("/rest/v1/", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Faltan credenciales de Supabase en .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Importar motor de reglas
try:
    from src.rules.fraud_rules import evaluar_todas_las_reglas
    REGLAS_OK = True
except Exception as e:
    print(f"AVISO: No se pudo importar fraud_rules ({e}). Se usarán scores estimados.")
    REGLAS_OK = False

# ==========================================
# CATÁLOGOS
# ==========================================
RAMOS = ["Vehículos", "Salud", "Vida", "Hogar", "Generales"]
COBERTURAS = {
    "Vehículos": ["Choque", "Robo", "Daño"],
    "Salud":     ["Atención médica", "Otro"],
    "Vida":      ["Otro"],
    "Hogar":     ["Incendio", "Robo", "Daño"],
    "Generales": ["Daño", "Otro"],
}
NOMBRES = [
    "Carlos","María","José","Ana","Juan","Luis","Laura","Pedro",
    "Marta","Jorge","Lucía","Diego","Carmen","Fernando","Elena",
    "Andrés","Sofía","Miguel","Isabel","Rafael","Paula","Alejandro",
    "Teresa","Manuel","Rosa","Daniel","Beatriz","Pablo","Silvia","Javier"
]
APELLIDOS = [
    "García","López","Pérez","González","Sánchez","Martínez","Rodríguez",
    "Fernández","Gómez","Díaz","Ruiz","Hernández","Jiménez","Álvarez",
    "Moreno","Muñoz","Romero","Alonso","Gutiérrez","Navarro"
]
CIUDADES = [
    "Quito","Guayaquil","Cuenca","Manta","Portoviejo",
    "Loja","Ambato","Santo Domingo","Machala","Riobamba"
]
SUCURSALES = [
    "Sucursal Quito Norte","Sucursal Guayaquil Centro",
    "Sucursal Cuenca El Sagrario","Sucursal Manta Tarqui",
    "Sucursal Ambato Ficoa"
]
CANALES = ["Agente","Directo","Broker","Digital"]
PROVEEDORES_SOSPECHOSOS = [
    "Taller El Rápido","Clínica Sanación Express","Peritajes Rápidos S.A."
]
PROVEEDORES_NORMALES = [
    "Taller Autorizado Motors","Hospital Metropolitano","Clínica Kennedy",
    "Taller AutoFix","Peritajes Certificados","Clínica del Sur","Taller Premium"
]
DOCS_OFICIALES = [
    "Factura de reparación","Denuncia policial","Parte policial","Peritaje",
    "Fotografías","Informe técnico","Fotografías de daño","Historia clínica",
    "Exámenes","Factura hospitalaria","Orden médica","Otros"
]
DOCS_POR_RAMO = {
    "Vehículos": ["Parte policial","Denuncia policial","Fotografías","Factura de reparación","Peritaje", "Informe técnico", "Fotografías de daño"],
    "Salud":     ["Historia clínica","Exámenes","Orden médica","Factura hospitalaria"],
    "Vida":      ["Historia clínica", "Parte policial", "Exámenes"],
    "Hogar":     ["Fotografías de daño","Informe técnico","Denuncia policial", "Peritaje", "Fotografías", "Factura de reparación"],
    "Generales": ["Parte policial","Historia clínica","Fotografías de daño", "Denuncia policial", "Informe técnico", "Factura hospitalaria", "Exámenes", "Orden médica"],
}

# Narrativas variadas
NARR_ALTO = [
    "Vehículo robado a las 3am frente al domicilio, sin testigos ni cámaras.",
    "Incendio de vivienda la noche anterior al vencimiento de póliza. No hay testigos.",
    "Accidente con vehículo que se dio a la fuga sin dejar rastro ni placas.",
    "El asegurado indica que extraviaron todos los documentos del siniestro.",
    "Factura del taller con sellos y fechas que no corresponden al período del siniestro.",
    "Colisión con objeto fijo en zona sin cámaras. El asegurado no pudo precisar hora exacta.",
    "Reclamación de daños graves el mismo mes en que se contrató la póliza de vida.",
    "Proveedor indicado tiene múltiples reclamos activos en la aseguradora este mes.",
    "El monto reclamado supera en 3 veces el valor de mercado del vehículo asegurado.",
    "Asegurado con 4 siniestros en los últimos 8 meses en distintas sucursales.",
]
NARR_MEDIO = [
    "Colisión en intersección semaforizada. Se adjunta informe policial con demora.",
    "El asegurado reportó el incendio parcial de la vivienda 20 días después de ocurrido.",
    "Daños por lluvia intensa en vehículo. El reporte tardó más de dos semanas.",
    "Asegurado solicita atención médica urgente fuera de su ciudad habitual.",
    "Accidente en zona poco transitada. Testigo confirma pero no firma el acta.",
]
NARR_BAJO = [
    "Colisión leve en parqueadero. Cámaras del lugar registraron el incidente.",
    "Asegurado presentó todos los documentos el mismo día del siniestro.",
    "Accidente de tránsito con parte policial adjunto y dos testigos identificados.",
    "Daños menores por granizo durante tormenta certificada por la alcaldía.",
    "Paciente ingresó a urgencias, diagnóstico confirmado, documentación completa.",
]


def rand_date(start: datetime.date, end: datetime.date) -> datetime.date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def gen_placa() -> str:
    letras = "".join(random.choices("ABCDEFGHJKLMNPRSTUVWXYZ", k=3))
    nums   = str(random.randint(1000, 9999))
    return f"{letras}-{nums}"


def score_estimado(score_reglas: int, es_alto: bool, es_medio: bool) -> int:
    if es_alto:
        return max(score_reglas, random.randint(65, 95))
    if es_medio:
        return max(score_reglas, random.randint(30, 64))
    return min(score_reglas, random.randint(5, 29))


# ==========================================
# 1. ASEGURADOS
# ==========================================
print("Generando 40 asegurados...")
asegurados = []
for i in range(40):
    nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
    reclamos = random.choices([0, 1, 2, 3, 5], weights=[50, 20, 15, 10, 5])[0]
    asegurados.append({
        "id_asegurado": f"ASEG-2026-{random.randint(10000, 99999)}-{uuid.uuid4().hex[:4]}",
        "nombre":  nombre,
        "ciudad":  random.choice(CIUDADES),
        "reclamos_ultimos_12_meses": reclamos,
    })

supabase.table("asegurados").insert(asegurados).execute()
print(f"  OK: {len(asegurados)} asegurados insertados.")


# ==========================================
# 2. PÓLIZAS
# ==========================================
print("Generando polizas...")
polizas = []
for aseg in asegurados:
    ramo = random.choice(RAMOS)
    # 10% polizas muy recientes, 5% a punto de vencer
    roll = random.random()
    if roll < 0.10:
        fi = datetime.date.today() - timedelta(days=random.randint(2, 8))
    elif roll < 0.15:
        fi = datetime.date.today() - timedelta(days=355)   # vence pronto
    else:
        fi = rand_date(datetime.date(2022, 1, 1),
                       datetime.date.today() - timedelta(days=30))
    ff = fi + timedelta(days=365)
    activa = ff >= datetime.date.today()
    placa  = gen_placa() if ramo == "Vehículos" else "N/A"

    polizas.append({
        "id_poliza":               f"POL-{random.randint(10000, 99999)}-{uuid.uuid4().hex[:4]}",
        "id_asegurado":            aseg["id_asegurado"],
        "ramo":                    ramo,
        "fecha_inicio":            str(fi),
        "fecha_fin":               str(ff),
        "prima":                   round(random.uniform(200, 1500), 2),
        "suma_asegurada":          round(random.uniform(5000, 80000), 2),
        "deducible":               round(random.uniform(100, 1000), 2),
        "canal_venta":             random.choice(CANALES),
        "ciudad":                  aseg["ciudad"],
        "estado_poliza":           "Activa" if activa else "Vencida",
        "placa_vehiculo_asegurado": placa,
    })

supabase.table("polizas").insert(polizas).execute()
print(f"  OK: {len(polizas)} polizas insertadas.")

# Solo pólizas activas para vincular siniestros
polizas_activas = [p for p in polizas if p["estado_poliza"] == "Activa"]
if not polizas_activas:
    polizas_activas = polizas          # fallback


# ==========================================
# 3. SINIESTROS + DOCUMENTOS
# ==========================================
print("Generando 50 siniestros (50% riesgo alto)...")

# Índices: 0-24 → ALTO, 25-34 → MEDIO, 35-49 → BAJO
ALTO_IDX  = set(range(0, 25))
MEDIO_IDX = set(range(25, 35))

siniestros_batch = []
documentos_batch = []

for i in range(50):
    es_alto  = i in ALTO_IDX
    es_medio = i in MEDIO_IDX

    pol  = random.choice(polizas_activas)
    aseg = next(a for a in asegurados if a["id_asegurado"] == pol["id_asegurado"])

    fi_pol = datetime.datetime.strptime(pol["fecha_inicio"], "%Y-%m-%d").date()
    ff_pol = datetime.datetime.strptime(pol["fecha_fin"],   "%Y-%m-%d").date()
    today  = datetime.date.today()

    # ── Defaults ──────────────────────────────────────────────────────────
    placa_sin        = pol["placa_vehiculo_asegurado"]
    fecha_ocurrencia = rand_date(fi_pol, min(ff_pol, today))
    fecha_reporte    = fecha_ocurrencia + timedelta(days=random.randint(0, 2))
    proveedor        = random.choice(PROVEEDORES_NORMALES)
    docs_faltantes   = False
    incons_doc       = False
    narrativa        = random.choice(NARR_BAJO)
    monto            = float(random.randint(300, 4000))
    hora_madrug      = False
    prov_sospechoso  = False

    # ── Inyección de anomalías (ALTO) ─────────────────────────────────────
    if es_alto:
        escenario = random.randint(1, 7)

        if escenario == 1 and pol["ramo"] == "Vehículos":
            # Placa inconsistente
            placa_sin = gen_placa()           # distinta a la de la póliza
            narrativa = random.choice(NARR_ALTO)
            monto     = float(random.randint(8000, 25000))

        elif escenario == 2:
            # Siniestro muy temprano (póliza recién emitida)
            fecha_ocurrencia = fi_pol + timedelta(days=random.randint(1, 5))
            fecha_reporte    = fecha_ocurrencia
            narrativa = "Siniestro grave reportado a los pocos días de contratar la póliza."
            monto     = float(random.randint(20000, 60000))

        elif escenario == 3:
            # Proveedor sospechoso + documentos inconsistentes
            proveedor    = random.choice(PROVEEDORES_SOSPECHOSOS)
            incons_doc   = True
            prov_sospechoso = True
            narrativa    = "Las facturas presentadas tienen inconsistencias en fechas y sellos."
            monto        = float(random.randint(12000, 40000))

        elif escenario == 4:
            # Monto atípico + madrugada
            monto      = float(random.randint(55000, 90000))
            hora_madrug= True
            narrativa  = "Accidente grave a las 2:30 am sin testigos ni cámaras en el lugar."

        elif escenario == 5:
            # Documentación faltante
            docs_faltantes = True
            narrativa = "El asegurado indica que extravió la documentación del siniestro."
            monto     = float(random.randint(10000, 35000))

        elif escenario == 6:
            # Siniestro justo antes del vencimiento
            dias_antes = random.randint(1, 4)
            fo = ff_pol - timedelta(days=dias_antes)
            if fo <= today:
                fecha_ocurrencia = fo
                fecha_reporte    = fo
            narrativa = "Incidente reportado a días del vencimiento de la póliza."
            monto     = float(random.randint(15000, 50000))

        elif escenario == 7:
            # Múltiples reclamos (historial alto)
            narrativa = random.choice(NARR_ALTO)
            monto     = float(random.randint(8000, 30000))
            aseg["reclamos_ultimos_12_meses"] = max(
                aseg["reclamos_ultimos_12_meses"], 4
            )

    # ── Riesgo medio ──────────────────────────────────────────────────────
    elif es_medio:
        narrativa = random.choice(NARR_MEDIO)
        monto     = float(random.randint(5000, 15000))
        if random.random() < 0.6:
            fecha_reporte = fecha_ocurrencia + timedelta(days=random.randint(12, 28))

    # ── Calcular días ─────────────────────────────────────────────────────
    dias_inicio = (fecha_ocurrencia - fi_pol).days
    dias_fin    = (ff_pol - fecha_ocurrencia).days
    dias_entre  = (fecha_reporte - fecha_ocurrencia).days

    # ── Motor de reglas antifraude ────────────────────────────────────────
    if REGLAS_OK:
        sin_dummy = {
            "monto_reclamado":              monto,
            "dias_entre_ocurrencia_reporte": dias_entre,
            "dias_desde_inicio_poliza":     dias_inicio,
            "dias_desde_fin_poliza":        dias_fin,
            "placa_vehiculo":               placa_sin,
            "ramo":                         pol["ramo"],
            "documentos_completos":         not docs_faltantes,
            "descripcion":                  narrativa,
        }
        ctx = {
            "conteo_proveedor":         4 if prov_sospechoso else 1,
            "ramo_poliza":              pol["ramo"],
            "placa_vehiculo_asegurado": pol["placa_vehiculo_asegurado"],
            "narrativas_previas":       [],
            "siniestros_vehiculo":      3 if aseg["reclamos_ultimos_12_meses"] >= 3 else 0,
            "siniestros_rc":            0,
            "hora_siniestro":           3 if hora_madrug else 14,
            "fecha_emision_anterior":   incons_doc,
        }
        resultado = evaluar_todas_las_reglas(sin_dummy, ctx)
        score_raw      = resultado["score_reglas"]
        alertas_list   = resultado.get("alertas_detalle", [])
    else:
        score_raw    = random.randint(65, 90) if es_alto else (
                       random.randint(30, 64) if es_medio else random.randint(5, 29))
        alertas_list = []

    score_final = score_estimado(score_raw, es_alto, es_medio)
    nivel = "Alto" if score_final >= 65 else ("Medio" if score_final >= 30 else "Bajo")

    id_sin = f"SIN-2026-{random.randint(10000, 99999)}-{uuid.uuid4().hex[:4]}"

    # ── Registro siniestro ────────────────────────────────────────────────
    siniestros_batch.append({
        "id_siniestro":                  id_sin,
        "id_poliza":                     pol["id_poliza"],
        "id_asegurado":                  aseg["id_asegurado"],
        "ramo":                          pol["ramo"],
        "cobertura":                     random.choice(COBERTURAS[pol["ramo"]]),
        "placa_vehiculo":                placa_sin,
        "fecha_ocurrencia":              str(fecha_ocurrencia),
        "fecha_reporte":                 str(fecha_reporte),
        "monto_reclamado":               monto,
        "monto_estimado":                round(monto * random.uniform(0.9, 1.2), 2),
        "monto_pagado":                  0.0,
        "estado":                        "Reserva",
        "sucursal":                      random.choice(SUCURSALES),
        "descripcion":                   narrativa,
        "documentos_completos":          not docs_faltantes,
        "beneficiario":                  random.choice(["Asegurado","Taller","Clínica","Perito"]),
        "dias_desde_inicio_poliza":      dias_inicio,
        "dias_desde_fin_poliza":         dias_fin,
        "dias_entre_ocurrencia_reporte": dias_entre,
        "historial_siniestros_asegurado": aseg["reclamos_ultimos_12_meses"] + 1,
        "etiqueta_fraude_simulada":      1 if es_alto else 0,
        "cliente":                       aseg["nombre"],
        "tipo_siniestro":                random.choice(["Choque", "Robo", "Atención médica", "Incendio", "Daño", "Otro"]),
        "fecha_incidente":               str(fecha_ocurrencia),
        "fecha_poliza":                  pol["fecha_inicio"],
        "ciudad":                        aseg["ciudad"],
        "proveedor":                     proveedor,
        "proveedor_id":                  None,
        "historial_reclamos":            aseg["reclamos_ultimos_12_meses"] + 1,
        "narrativa":                     narrativa,
        "score_riesgo":                  score_final,
        "nivel_riesgo":                  nivel,
        "alertas":                       alertas_list,
    })

    # ── Documentos ────────────────────────────────────────────────────────
    docs_ramo = DOCS_POR_RAMO.get(pol["ramo"], ["Otros"])
    num_docs  = random.randint(0, 1) if docs_faltantes else random.randint(1, 3)
    elegidos  = random.sample(docs_ramo, min(num_docs, len(docs_ramo)))
    for t in elegidos:
        documentos_batch.append({
            "id_siniestro":           id_sin,
            "tipo_documento":         t,
            "entregado":              not docs_faltantes,
            "legible":                not incons_doc,
            "fecha_emision":          str(fecha_ocurrencia),
            "inconsistencia_detectada": incons_doc,
            "observacion":            (
                "Documento con inconsistencia detectada." if incons_doc else
                "Falta de documentación." if docs_faltantes else
                "Documento en regla."
            ),
        })


# ── Inserción en bloques ──────────────────────────────────────────────────
print("Insertando siniestros...")
CHUNK = 10
for j in range(0, len(siniestros_batch), CHUNK):
    supabase.table("siniestros").insert(siniestros_batch[j:j+CHUNK]).execute()
print(f"  OK: {len(siniestros_batch)} siniestros insertados.")

print("Insertando documentos...")
for j in range(0, len(documentos_batch), CHUNK):
    supabase.table("documentos").insert(documentos_batch[j:j+CHUNK]).execute()
print(f"  OK: {len(documentos_batch)} documentos insertados.")

# ── Resumen final ──────────────────────────────────────────────────────────
altos  = sum(1 for s in siniestros_batch if s["nivel_riesgo"] == "Alto")
medios = sum(1 for s in siniestros_batch if s["nivel_riesgo"] == "Medio")
bajos  = sum(1 for s in siniestros_batch if s["nivel_riesgo"] == "Bajo")
print(f"\nResumen: {altos} Alto | {medios} Medio | {bajos} Bajo")
print("Generacion completada exitosamente.")
