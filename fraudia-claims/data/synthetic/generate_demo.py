"""
Generador de datos sintéticos para demostración de FraudIA.
Produce ~20 siniestros con perfiles de riesgo variados.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

random.seed(42)

CLIENTES = [
    "María González López", "Carlos Mendoza Ruiz", "Ana Sofía Herrera", "Roberto Jiménez Castro",
    "Luisa Fernanda Mora", "Andrés Felipe Vargas", "Patricia Elena Soto", "Diego Alejandro Ríos",
    "Carmen Rosa Delgado", "Fernando José Reyes", "Valentina Cruz Pinto", "Sergio Antonio Luna",
    "Natalia Beatriz Campos", "Manuel Eduardo Torres", "Isabel Cristina Vega", "Javier Ernesto Paredes",
    "Gabriela Marcela Aguilar", "Héctor Daniel Romero", "Daniela Pilar Núñez", "Oscar Mauricio Blanco",
]

TIPOS = ["Robo de vehículo", "Accidente de tránsito", "Daño parcial", "Incendio",
         "Robo de contenido", "Responsabilidad civil", "Asistencia vial", "Granizo"]

CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
            "Bucaramanga", "Pereira", "Manizales", "Ibagué", "Santa Marta"]

PROVEEDORES = [
    "Taller AutoExpress S.A.", "Servicios Viales del Norte", "AutoTech Premium",
    "Centro de Reparación Rápida", "Multiservicios El Dorado", "Taller Hermanos Pérez",
    "Soluciones Automotrices JM", "Taller El Rincón Mecánico",
]

NARRATIVAS_SOSPECHOSAS = [
    "El vehículo fue hurtado en horas de la madrugada mientras se encontraba parqueado frente al domicilio. No hay testigos ni cámaras disponibles.",
    "El vehículo fue robado en la madrugada estando parqueado frente a la residencia. No existen testigos ni grabaciones del incidente.",
    "El automóvil desapareció durante la noche mientras permanecía estacionado en frente de la casa. No había nadie que viera lo ocurrido.",
    "Colisión con vehículo desconocido que se dio a la fuga sin dejar rastro. No hay placas ni descripción del conductor.",
    "Impacto con vehículo no identificado que escapó del lugar. Imposible obtener datos del responsable.",
]

NARRATIVAS_NORMALES = [
    "El asegurado reporta accidente de tránsito en intersección de la Calle 80 con Carrera 50. Colisión lateral con motocicleta. Se adjunta informe policial.",
    "Daños por granizo ocurridos el 15 de octubre durante tormenta fuerte en sector norte. Vehículo se encontraba en parqueadero descubierto.",
    "Incidente de responsabilidad civil. El asegurado impactó por detrás a vehículo detenido en semáforo. Conductor afectado acepta el informe.",
    "Asistencia vial solicitada por falla mecánica en autopista. Vehículo remolcado a taller autorizado.",
    "Accidente en parqueadero de centro comercial. Raspón en puerta delantera derecha causado por maniobra de otro vehículo. Hay testigo.",
    "Robo en intento con daños a cerradura de puerta izquierda. El asegurado presentó denuncia ante autoridades competentes el mismo día.",
    "Colisión en vía secundaria bajo lluvia intensa. Pérdida de control por acuaplaning. Informe de tránsito anexado al expediente.",
]


def generar_siniestro(idx: int) -> Dict:
    fecha_base = datetime.now()
    dias_atras = random.randint(1, 180)
    fecha_incidente = fecha_base - timedelta(days=dias_atras)
    fecha_poliza = fecha_incidente - timedelta(days=random.choice([15, 30, 60, 90, 180, 365, 730]))

    es_sospechoso = idx in [2, 5, 8, 11, 14]  # Algunos casos sospechosos por diseño

    monto = random.randint(800, 45000) if not es_sospechoso else random.randint(25000, 85000)
    historial = random.randint(0, 2) if not es_sospechoso else random.randint(3, 7)

    if es_sospechoso and random.random() > 0.5:
        narrativa = random.choice(NARRATIVAS_SOSPECHOSAS)
    else:
        narrativa = random.choice(NARRATIVAS_NORMALES)

    # Score de riesgo calculado de forma determinista para demo
    score = calcular_score_demo(monto, historial, fecha_poliza, fecha_incidente, es_sospechoso)
    nivel = "Alto" if score >= 70 else "Medio" if score >= 40 else "Bajo"

    alertas = generar_alertas(monto, historial, fecha_poliza, fecha_incidente, es_sospechoso)

    tipo = random.choice(TIPOS)
    es_vehicular = "vehículo" in tipo.lower() or "tránsito" in tipo.lower() or "granizo" in tipo.lower()
    placa = f"{random.choice(['ABC', 'PBR', 'XTR', 'GSM'])}-{random.randint(1000, 9999)}" if es_vehicular else "N/A"
    
    return {
        "id": idx + 1,
        "id_siniestro": f"SIN-2024-{str(idx + 1).zfill(4)}",
        "cliente": CLIENTES[idx % len(CLIENTES)],
        "tipo_siniestro": tipo,
        "ramo": "Vehículos" if es_vehicular else "Otros",
        "placa_vehiculo": placa,
        "monto_reclamado": monto,
        "fecha_incidente": fecha_incidente.strftime("%Y-%m-%d"),
        "fecha_poliza": fecha_poliza.strftime("%Y-%m-%d"),
        "ciudad": random.choice(CIUDADES),
        "proveedor": random.choice(PROVEEDORES),
        "historial_reclamos": historial,
        "narrativa": narrativa,
        "score_riesgo": score,
        "nivel_riesgo": nivel,
        "alertas": alertas,
        "fecha_registro": (fecha_base - timedelta(days=random.randint(0, dias_atras))).strftime("%Y-%m-%d %H:%M:%S"),
    }


def calcular_score_demo(monto, historial, fecha_poliza, fecha_incidente, sospechoso) -> int:
    score = 0
    dias_poliza = (fecha_incidente - fecha_poliza).days

    if monto > 40000:
        score += 30
    elif monto > 20000:
        score += 15
    else:
        score += 5

    if historial >= 4:
        score += 30
    elif historial >= 2:
        score += 15
    else:
        score += 0

    if dias_poliza < 30:
        score += 25
    elif dias_poliza < 90:
        score += 10

    if sospechoso:
        score += random.randint(10, 20)

    return min(score + random.randint(-5, 10), 99)


def generar_alertas(monto, historial, fecha_poliza, fecha_incidente, sospechoso) -> List[str]:
    alertas = []
    dias_poliza = (fecha_incidente - fecha_poliza).days

    if monto > 40000:
        alertas.append("Monto reclamado excede percentil 90")
    if historial >= 3:
        alertas.append(f"Alto historial de reclamos: {historial} previos")
    if dias_poliza < 60:
        alertas.append(f"Siniestro a {dias_poliza} días de contratación de póliza")
    if sospechoso:
        alertas.append("Narrativa con similitud alta a casos previos")
        if random.random() > 0.4:
            alertas.append("Proveedor con múltiples alertas activas")

    return alertas


def generar_dataset() -> List[Dict]:
    return [generar_siniestro(i) for i in range(20)]


if __name__ == "__main__":
    import os
    data = generar_dataset()
    out_path = os.path.join(os.path.dirname(__file__), "siniestros_demo.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(data)} siniestros demo generados en {out_path}")
