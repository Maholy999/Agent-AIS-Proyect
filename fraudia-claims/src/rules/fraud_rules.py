"""
src/rules/fraud_rules.py
Reglas de negocio críticas y señales de posible fraude para el sistema AIS.
Cada regla y señal devuelve detalladamente si está activada, su descripción, severidad y puntos.
"""

from datetime import datetime
from typing import List, Dict, Any, Tuple


def evaluar_todas_las_reglas(siniestro: Dict[str, Any], contexto: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Ejecuta todas las reglas críticas de negocio y señales de fraude sobre un siniestro.
    Devuelve un resumen con alertas activadas, score parcial y nivel de riesgo.
    """
    if contexto is None:
        contexto = {}

    alertas_activadas: List[Dict[str, Any]] = []
    detalle_reglas: List[Dict[str, Any]] = []
    score_total = 0

    # --- CAMPOS AUXILIARES DEL SINIESTRO ---
    monto = float(siniestro.get("monto_reclamado", 0))
    cobertura = str(siniestro.get("cobertura", "")).strip().lower()
    ramo = str(siniestro.get("ramo", "")).strip().lower()
    narrativa = str(siniestro.get("narrativa", siniestro.get("descripcion", "")))
    cliente = str(siniestro.get("cliente", siniestro.get("id_asegurado", "")))
    beneficiario = str(siniestro.get("beneficiario", ""))
    proveedor = str(siniestro.get("proveedor", ""))

    dias_inicio = siniestro.get("dias_desde_inicio_poliza")
    if dias_inicio is None:
        dias_inicio = 999
    else:
        dias_inicio = int(dias_inicio)

    dias_fin = siniestro.get("dias_desde_fin_poliza")
    if dias_fin is None:
        dias_fin = 999
    else:
        dias_fin = int(dias_fin)

    dias_entre = siniestro.get("dias_entre_ocurrencia_reporte")
    if dias_entre is None:
        dias_entre = 0
    else:
        dias_entre = int(dias_entre)

    historial_aseg = int(contexto.get("siniestros_asegurado", siniestro.get("historial_siniestros_asegurado", siniestro.get("historial_reclamos", 0))))
    documentos_completos = siniestro.get("documentos_completos")
    if documentos_completos is None:
        documentos_completos = True
    elif isinstance(documentos_completos, str):
        documentos_completos = documentos_completos.lower() in ("sí", "si", "true", "1")
    else:
        documentos_completos = bool(documentos_completos)

    inconsistencia_detectada = siniestro.get("inconsistencia_detectada", False)
    if isinstance(inconsistencia_detectada, str):
        inconsistencia_detectada = inconsistencia_detectada.lower() in ("sí", "si", "true", "1")
    else:
        inconsistencia_detectada = bool(inconsistencia_detectada)

    # ==========================================
    # 1. EVALUACIÓN DE REGLAS CRÍTICAS
    # ==========================================

    # Rule A: Cobertura Pérdida Total por Robo (PTxRB) -> roja
    es_ptxrb = False
    if "robo" in cobertura:
        narrativa_lower = narrativa.lower()
        if any(keyword in narrativa_lower for keyword in ["pérdida total", "perdida total", "ptxrb", "robo total", "sustracción total"]):
            es_ptxrb = True
    
    detalle_reglas.append({
        "regla": "PTxRB",
        "activada": es_ptxrb,
        "descripcion": "Cobertura Pérdida Total por Robo (PTxRB) detectada en la narrativa",
        "severidad": "roja",
        "puntos_adicionales": 30 if es_ptxrb else 0
    })
    if es_ptxrb:
        alertas_activadas.append({
            "descripcion": "Pérdida Total por Robo (PTxRB) con alta probabilidad de inconsistencia",
            "severidad": "roja",
            "puntos": 0
        })
        score_total += 30

    # Rule B: Evidencia de Falsificación o Adulteración Documental Evidente -> roja
    es_falsificacion = False
    narrativa_lower = narrativa.lower()
    if inconsistencia_detectada or any(keyword in narrativa_lower for keyword in ["falsificado", "adulterado", "alteración", "alteracion", "tachadura", "firma dudosa", "firma falsa"]):
        es_falsificacion = True
    
    detalle_reglas.append({
        "regla": "FalsificacionDocumental",
        "activada": es_falsificacion,
        "descripcion": "Evidencia de falsificación, adulteración documental o firmas dudosas",
        "severidad": "roja",
        "puntos_adicionales": 35 if es_falsificacion else 0
    })
    if es_falsificacion:
        alertas_activadas.append({
            "descripcion": "Evidencia de Falsificación o Adulteración Documental Evidente",
            "severidad": "roja",
            "puntos": 0
        })
        score_total += 35

    # Rule C: Asegurado, Beneficiario o APS con Coincidencia Exacta en “Lista Restrictiva” -> roja
    LISTA_RESTRICTIVA = [
        "juan perez restringido", "taller patito restringido", "clinica fantasma", 
        "pedro lopez prohibido", "aps fraudulento", "juan miguel chimbo restringido"
    ]
    es_lista_restrictiva = False
    for entity in [cliente, beneficiario, proveedor]:
        if entity and entity.strip().lower() in LISTA_RESTRICTIVA:
            es_lista_restrictiva = True
            matched_entity = entity
            break
    
    detalle_reglas.append({
        "regla": "ListaRestrictiva",
        "activada": es_lista_restrictiva,
        "descripcion": f"Coincidencia exacta en lista restrictiva: {matched_entity if es_lista_restrictiva else ''}",
        "severidad": "roja",
        "puntos_adicionales": 40 if es_lista_restrictiva else 0
    })
    if es_lista_restrictiva:
        alertas_activadas.append({
            "descripcion": f"Asegurado, Beneficiario o Proveedor coincide con 'Lista Restrictiva'",
            "severidad": "roja",
            "puntos": 0
        })
        score_total += 40

    # Rule D: Dinámica del Accidente Físicamente Imposible -> roja
    es_dinamica_imposible = False
    narrativa_lower = narrativa.lower()
    incoherencias = [
        "daño trasero colisión frontal", 
        "colisión frontal con daños solo en la parte trasera", 
        "colision frontal con daños solo en la parte trasera",
        "daños solo traseros en colisión frontal",
        "choque de frente daño trasero",
        "caída de puente sin daños en chasis",
        "choque a 100km/h sin deformación",
        "dinámica imposible",
        "dinamica imposible"
    ]
    if any(inc in narrativa_lower for inc in incoherencias):
        es_dinamica_imposible = True

    detalle_reglas.append({
        "regla": "DinamicaImposible",
        "activada": es_dinamica_imposible,
        "descripcion": "Dinámica del accidente descrita resulta físicamente imposible o incoherente",
        "severidad": "roja",
        "puntos_adicionales": 30 if es_dinamica_imposible else 0
    })
    if es_dinamica_imposible:
        alertas_activadas.append({
            "descripcion": "Dinámica del Accidente Físicamente Imposible / Incoherente",
            "severidad": "roja",
            "puntos": 0
        })
        score_total += 30

    # Rule E: Siniestro Extremo al Borde de Vigencia (< 48 hrs) -> amarilla
    es_borde_extremo = (0 <= dias_inicio < 2) or (0 <= dias_fin < 2)
    detalle_reglas.append({
        "regla": "BordeVigenciaExtremo",
        "activada": es_borde_extremo,
        "descripcion": f"Siniestro registrado en ventana extrema de vigencia (< 48 horas). Días inicio: {dias_inicio}, Días fin: {dias_fin}",
        "severidad": "amarilla",
        "puntos_adicionales": 15 if es_borde_extremo else 0
    })
    if es_borde_extremo:
        alertas_activadas.append({
            "descripcion": f"El siniestro ocurrió a menos de 48 horas del inicio o fin de vigencia de la póliza",
            "severidad": "amarilla",
            "puntos": 0
        })
        score_total += 15

    # Rule F: Demora Atípica en Denuncia de Robo (> 4 días) -> amarilla
    es_demora_robo = "robo" in cobertura and dias_entre > 4
    detalle_reglas.append({
        "regla": "DemoraRoboAtipica",
        "activada": es_demora_robo,
        "descripcion": f"Demora atípica en reporte de robo: {dias_entre} días (umbral: > 4 días)",
        "severidad": "amarilla",
        "puntos_adicionales": 15 if es_demora_robo else 0
    })
    if es_demora_robo:
        alertas_activadas.append({
            "descripcion": f"El reclamo por robo fue notificado a la aseguradora {dias_entre} días después del incidente, superando el tiempo habitual",
            "severidad": "amarilla",
            "puntos": 0
        })
        score_total += 15

    # Rule G: Narrativa Idéntica o Clonada -> amarilla
    es_clonada = False
    if contexto.get("es_clonada") or "narrativa clonada" in narrativa_lower or "narrativa identica" in narrativa_lower:
        es_clonada = True
    else:
        # Comparar con lista de narrativas si existe
        narrativas_previas = contexto.get("narrativas_previas", [])
        for np in narrativas_previas:
            if np and len(np) > 20 and np.strip().lower() == narrativa.strip().lower():
                es_clonada = True
                break

    detalle_reglas.append({
        "regla": "NarrativaClonada",
        "activada": es_clonada,
        "descripcion": "Narrativa idéntica o copiada de otro siniestro del portafolio",
        "severidad": "amarilla",
        "puntos_adicionales": 15 if es_clonada else 0
    })
    if es_clonada:
        alertas_activadas.append({
            "descripcion": "La descripción del siniestro es idéntica a otro caso previamente registrado",
            "severidad": "amarilla",
            "puntos": 0
        })
        score_total += 15


    # ==========================================
    # 2. EVALUACIÓN DE SEÑALES DE FRAUDE (PUNTUACIONES)
    # ==========================================

    # Signal 1: Borde de Vigencia (Proximidad al Inicio/Fin)
    pts_s1 = 0
    desc_s1 = ""
    if dias_inicio <= 10 or dias_fin <= 10:
        pts_s1 = 8
        desc_s1 = "Siniestro a menos de 10 días del borde de vigencia de la póliza (+8 pts)"
    elif dias_inicio <= 30 or dias_fin <= 30:
        pts_s1 = 4
        desc_s1 = "Siniestro entre 11 y 30 días del borde de vigencia de la póliza (+4 pts)"
    
    if pts_s1 > 0:
        score_total += pts_s1
        alertas_activadas.append({
            "descripcion": desc_s1,
            "severidad": "amarilla",
            "puntos": pts_s1
        })
    detalle_reglas.append({"regla": "Signal_Vigencia", "activada": pts_s1 > 0, "descripcion": desc_s1 or "Vigencia regular", "severidad": "amarilla", "puntos": pts_s1})

    # Signal 2: Demora en Denuncia (Especialmente en Robo/Vehículos)
    pts_s2 = 0
    desc_s2 = ""
    if "robo" in cobertura or "vehículo" in ramo or "vehiculo" in ramo:
        if dias_entre > 2:  # > 48 horas
            pts_s2 = 8
            desc_s2 = f"El reclamo fue notificado a la aseguradora más de 48 horas después del evento (+8 pts)"
        elif dias_entre >= 1:  # entre 24 y 48 horas
            pts_s2 = 4
            desc_s2 = f"El reclamo fue notificado a la aseguradora entre 24 y 48 horas después del evento (+4 pts)"

    if pts_s2 > 0:
        score_total += pts_s2
        alertas_activadas.append({
            "descripcion": desc_s2,
            "severidad": "amarilla",
            "puntos": pts_s2
        })
    detalle_reglas.append({"regla": "Signal_DemoraDenuncia", "activada": pts_s2 > 0, "descripcion": desc_s2 or "Reporte a tiempo", "severidad": "amarilla", "puntos": pts_s2})

    # Signal 3: Frecuencia de Siniestralidad del Asegurado
    pts_s3 = 0
    desc_s3 = ""
    if historial_aseg >= 3:
        pts_s3 = 8
        desc_s3 = f"El asegurado registra {historial_aseg} siniestros previos, lo cual representa una frecuencia elevada para este tipo de póliza (+8 pts)"
    elif historial_aseg == 2:
        pts_s3 = 4
        desc_s3 = f"El asegurado registra 2 siniestros previos en su historial (+4 pts)"

    if pts_s3 > 0:
        score_total += pts_s3
        alertas_activadas.append({
            "descripcion": desc_s3,
            "severidad": "amarilla",
            "puntos": pts_s3
        })
    detalle_reglas.append({"regla": "Signal_FrecuenciaAsegurado", "activada": pts_s3 > 0, "descripcion": desc_s3 or "Historial normal", "severidad": "amarilla", "puntos": pts_s3})

    # Signal 4: Frecuencia de Siniestralidad del Vehículo (Misma Placa/Chasis)
    pts_s4 = 0
    desc_s4 = ""
    siniestros_vehiculo = int(contexto.get("siniestros_vehiculo", 0))
    # Detectar también por narrativa si se indica
    if "placa reincidente" in narrativa_lower or "vehículo con historial" in narrativa_lower:
        siniestros_vehiculo = max(siniestros_vehiculo, 3)

    if siniestros_vehiculo >= 3:
        pts_s4 = 6
        desc_s4 = f"El vehículo involucrado registra {siniestros_vehiculo} siniestros previos, lo que representa una frecuencia elevada para una sola unidad (+6 pts)"
    elif siniestros_vehiculo == 2:
        pts_s4 = 3
        desc_s4 = f"El vehículo involucrado registra 2 siniestros previos en su historial (+3 pts)"

    if pts_s4 > 0:
        score_total += pts_s4
        alertas_activadas.append({
            "descripcion": desc_s4,
            "severidad": "amarilla",
            "puntos": pts_s4
        })
    detalle_reglas.append({"regla": "Signal_FrecuenciaVehiculo", "activada": pts_s4 > 0, "descripcion": desc_s4 or "Vehículo sin historial adverso", "severidad": "amarilla", "puntos": pts_s4})

    # Signal 5: Concentración de Siniestros en Coberturas de Responsabilidad Civil (RC)
    pts_s5 = 0
    desc_s5 = ""
    siniestros_rc = int(contexto.get("siniestros_rc", 0))
    if "responsabilidad civil" in cobertura or "rc" in cobertura:
        siniestros_rc = max(siniestros_rc, 1) # Asegurar al menos 1 si esta es la cobertura afectada

    if siniestros_rc > 2:
        pts_s5 = 6
        desc_s5 = f"El asegurado presenta {siniestros_rc} reclamos afectando cobertura de Responsabilidad Civil, una concentración atípica (+6 pts)"
    elif siniestros_rc in [1, 2]:
        pts_s5 = 3
        desc_s5 = f"Este reclamo involucra cobertura de Responsabilidad Civil (+3 pts)"

    if pts_s5 > 0:
        score_total += pts_s5
        alertas_activadas.append({
            "descripcion": desc_s5,
            "severidad": "amarilla",
            "puntos": pts_s5
        })
    detalle_reglas.append({"regla": "Signal_ResponsabilidadCivil", "activada": pts_s5 > 0, "descripcion": desc_s5 or "Cobertura regular", "severidad": "amarilla", "puntos": pts_s5})

    # Signal 6: Falta de Documentación de Soporte Obligatoria
    pts_s6 = 0
    desc_s6 = ""
    # Si falta cédula o informe policial
    if not documentos_completos or any(keyword in narrativa_lower for keyword in ["falta cédula", "falta cedula", "falta informe", "sin informe policial", "sin parte policial"]):
        pts_s6 = 4
        desc_s6 = "El expediente carece de documentos obligatorios (cédula de identidad o informe policial) necesarios para la validación del hecho (+4 pts)"

    if pts_s6 > 0:
        score_total += pts_s6
        alertas_activadas.append({
            "descripcion": desc_s6,
            "severidad": "amarilla",
            "puntos": pts_s6
        })
    detalle_reglas.append({"regla": "Signal_FaltaDocumentacion", "activada": pts_s6 > 0, "descripcion": desc_s6 or "Documentación completa", "severidad": "amarilla", "puntos": pts_s6})

    # Signal 7: Narrativa del Siniestro Inconsistente o Incoherente (Madrugada)
    pts_s7 = 0
    desc_s7 = ""
    es_madrugada = False
    
    # Comprobar madrugada (1:00 AM a 5:00 AM) en la narrativa
    madrugada_keywords = ["1 am", "2 am", "3 am", "4 am", "5 am", "1:00 am", "2:00 am", "3:00 am", "4:00 am", "5:00 am", "1:30 am", "2:30 am", "3:30 am", "4:30 am", "madrugada", "altas horas"]
    if any(keyword in narrativa_lower for keyword in madrugada_keywords) or 1 <= int(contexto.get("hora_siniestro", -1)) <= 5:
        es_madrugada = True

    if es_dinamica_imposible or "inconsistente" in narrativa_lower or "ilógico" in narrativa_lower or "ilogico" in narrativa_lower:
        pts_s7 = 6
        desc_s7 = "La descripción de los daños o la secuencia de eventos presenta contradicciones que requieren verificación pericial (+6 pts)"
    elif es_madrugada:
        pts_s7 = 3
        desc_s7 = "El siniestro fue declarado en horario nocturno entre 1:00 AM y 5:00 AM, lo que dificulta la verificación de testigos (+3 pts)"

    if pts_s7 > 0:
        score_total += pts_s7
        alertas_activadas.append({
            "descripcion": desc_s7,
            "severidad": "amarilla",
            "puntos": pts_s7
        })
    detalle_reglas.append({"regla": "Signal_InconsistenciaNarrativa", "activada": pts_s7 > 0, "descripcion": desc_s7 or "Narrativa coherente en horario normal", "severidad": "amarilla", "puntos": pts_s7})

    # Signal 8: Daños Graves sin Terceros Identificados
    pts_s8 = 0
    desc_s8 = ""
    # "choque contra objeto fijo" sin testigos ni fotos, o "objeto fijo" o se dio a la fuga
    choque_objeto_fijo = "objeto fijo" in narrativa_lower or "poste" in narrativa_lower or "árbol" in narrativa_lower or "arbol" in narrativa_lower
    sin_terceros = "se dio a la fuga" in narrativa_lower or "desconocido" in narrativa_lower or "sin tercero" in narrativa_lower or "no hay tercero" in narrativa_lower or "sin testigos" in narrativa_lower
    
    if (choque_objeto_fijo or sin_terceros) and (monto > 5000 or "severo" in narrativa_lower or "grave" in narrativa_lower):
        pts_s8 = 5
        desc_s8 = "El siniestro reporta daños graves sin que haya testigos ni terceros identificados que corroboren los hechos (+5 pts)"

    if pts_s8 > 0:
        score_total += pts_s8
        alertas_activadas.append({
            "descripcion": desc_s8,
            "severidad": "amarilla",
            "puntos": pts_s8
        })
    detalle_reglas.append({"regla": "Signal_SinTerceros", "activada": pts_s8 > 0, "descripcion": desc_s8 or "Terceros identificados", "severidad": "amarilla", "puntos": pts_s8})

    # Signal 9: Inconsistencias en los Documentos Presentados
    pts_s9 = 0
    desc_s9 = ""
    
    # Fecha de emisión anterior a la de ocurrencia
    fecha_emision_anterior = contexto.get("fecha_emision_anterior", False)
    if "fecha de emisión anterior" in narrativa_lower or "fecha de emision anterior" in narrativa_lower:
        fecha_emision_anterior = True

    if es_falsificacion or "tachadura" in narrativa_lower or "firma dudosa" in narrativa_lower:
        pts_s9 = 10
        desc_s9 = "Se detectaron características físicas irregulares en la documentación que requieren autenticación pericial (+10 pts)"
    elif fecha_emision_anterior:
        pts_s9 = 10
        desc_s9 = "La fecha de emisión de un documento es anterior a la fecha del siniestro declarado, lo que genera una inconsistencia temporal (+10 pts)"

    if pts_s9 > 0:
        score_total += pts_s9
        alertas_activadas.append({
            "descripcion": desc_s9,
            "severidad": "amarilla",
            "puntos": pts_s9
        })
    detalle_reglas.append({"regla": "Signal_DocumentosInconsistentes", "activada": pts_s9 > 0, "descripcion": desc_s9 or "Documentos válidos", "severidad": "amarilla", "puntos": pts_s9})

    # Signal 10: Reporte del Siniestro Fuera de los Plazos Establecidos
    pts_s10 = 0
    desc_s10 = ""
    if dias_entre > 7:
        pts_s10 = 5
        desc_s10 = f"El siniestro fue notificado a la aseguradora {dias_entre} días después del evento, superando el plazo contractual máximo (+5 pts)"
    elif 4 <= dias_entre <= 7:
        pts_s10 = 3
        desc_s10 = f"El reclamo fue notificado {dias_entre} días después del incidente, dentro de un rango que requiere atención (+3 pts)"

    if pts_s10 > 0:
        score_total += pts_s10
        alertas_activadas.append({
            "descripcion": desc_s10,
            "severidad": "amarilla",
            "puntos": pts_s10
        })
    detalle_reglas.append({"regla": "Signal_ReporteExtemporaneo", "activada": pts_s10 > 0, "descripcion": desc_s10 or "Reporte inmediato", "severidad": "amarilla", "puntos": pts_s10})

    # Regla: Inconsistencia de Placa (Placa de Siniestro vs Póliza)
    placa_vehiculo = str(siniestro.get("placa_vehiculo", "")).strip().upper()
    placa_poliza = str(contexto.get("placa_vehiculo_asegurado", "")).strip().upper()
    
    es_placa_inconsistente = False
    if ramo in ["vehículos", "vehiculos"]:
        if placa_vehiculo and placa_poliza and placa_poliza != "N/A" and placa_vehiculo != "N/A":
            if placa_vehiculo != placa_poliza:
                es_placa_inconsistente = True
                
    if es_placa_inconsistente:
        desc_placa = f"Placa del siniestro ({placa_vehiculo}) no coincide con la placa registrada en la póliza ({placa_poliza})"
        score_total += 30
        alertas_activadas.append({
            "descripcion": desc_placa,
            "severidad": "roja",
            "puntos": 0
        })
        detalle_reglas.append({
            "regla": "PlacaInconsistente",
            "activada": True,
            "descripcion": desc_placa,
            "severidad": "roja",
            "puntos_adicionales": 30
        })


    # Ramo inconsistente (Regla preexistente mantenida)
    ramo_poliza = str(contexto.get("ramo_poliza", "")).strip().lower()
    es_ramo_inconsistente = False
    if ramo and ramo_poliza and ramo != ramo_poliza:
        es_ramo_inconsistente = True
        
    if es_ramo_inconsistente:
        desc_ramo = f"Ramo del siniestro ({siniestro.get('ramo')}) no coincide con el ramo de la póliza"
        score_total += 35
        alertas_activadas.append({
            "descripcion": desc_ramo,
            "severidad": "roja",
            "puntos": 0
        })
        detalle_reglas.append({
            "regla": "RamoInconsistente",
            "activada": True,
            "descripcion": desc_ramo,
            "severidad": "roja",
            "puntos_adicionales": 35
        })

    # Asegurar que el score final esté capado en 100 y mínimo 0
    score_final_reglas = min(max(score_total, 0), 100)

    # Lista de alertas como texto para compatibilidad
    alertas_activas = [a["descripcion"] for a in alertas_activadas if isinstance(a, dict)]

    # Retorno unificado
    return {
        "score_reglas": score_final_reglas,
        "alertas": alertas_activas,  # Mantenemos por compatibilidad con el resto del sistema
        "alertas_detalle": alertas_activadas,  # Formato detallado de alertas con severidades y puntos
        "detalle_reglas": detalle_reglas,
        "total_alertas": len(alertas_activadas)
    }
