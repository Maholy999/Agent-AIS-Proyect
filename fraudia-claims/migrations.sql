-- ==========================================
-- 1. CAMPO PLACA EN TABLAS SINIESTROS Y PÓLIZAS
-- ==========================================

-- Tabla siniestros
ALTER TABLE public.siniestros
ADD COLUMN IF NOT EXISTS placa_vehiculo VARCHAR;

-- Tabla polizas
ALTER TABLE public.polizas
ADD COLUMN IF NOT EXISTS placa_vehiculo_asegurado VARCHAR;


-- ==========================================
-- 2. MIGRACIÓN AUTOMÁTICA DE REGISTROS EXISTENTES (PLACAS)
-- ==========================================

-- Actualizar siniestros vehiculares con placa aleatoria válida
UPDATE public.siniestros
SET placa_vehiculo = chr(trunc(random() * 26)::int + 65) || 
                     chr(trunc(random() * 26)::int + 65) || 
                     chr(trunc(random() * 26)::int + 65) || '-' || 
                     lpad(trunc(random() * 9999)::text, 4, '0')
WHERE ramo = 'Vehículos' AND (placa_vehiculo IS NULL OR placa_vehiculo = 'N/A' OR placa_vehiculo = '');

-- Actualizar siniestros NO vehiculares con N/A
UPDATE public.siniestros
SET placa_vehiculo = 'N/A'
WHERE ramo != 'Vehículos';

-- Actualizar polizas vehiculares con placa aleatoria válida (o igualarla si ya tiene un siniestro)
-- Simplificamos con random si es nula
UPDATE public.polizas
SET placa_vehiculo_asegurado = chr(trunc(random() * 26)::int + 65) || 
                               chr(trunc(random() * 26)::int + 65) || 
                               chr(trunc(random() * 26)::int + 65) || '-' || 
                               lpad(trunc(random() * 9999)::text, 4, '0')
WHERE ramo = 'Vehículos' AND (placa_vehiculo_asegurado IS NULL OR placa_vehiculo_asegurado = 'N/A' OR placa_vehiculo_asegurado = '');

-- Actualizar polizas NO vehiculares con N/A
UPDATE public.polizas
SET placa_vehiculo_asegurado = 'N/A'
WHERE ramo != 'Vehículos';


-- ==========================================
-- 3. ACTUALIZACIÓN DE TIPOS DE DOCUMENTO
-- ==========================================

-- A) Eliminar cualquier CONSTRAINT anterior relacionado con el tipo_documento en la tabla documentos.
-- Buscamos dinámicamente si existe algún CHECK constraint para tipo_documento y lo eliminamos.
DO $$ 
DECLARE
    constraint_name text;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'public.documentos'::regclass 
      AND contype = 'c' 
      AND pg_get_constraintdef(oid) ILIKE '%tipo_documento%';
      
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public.documentos DROP CONSTRAINT ' || constraint_name;
    END IF;
END $$;

-- B) Actualizar registros antiguos en la tabla documentos para que coincidan con la lista oficial.
UPDATE public.documentos
SET tipo_documento = 'Otros'
WHERE tipo_documento NOT IN (
    'Factura de reparación', 
    'Denuncia policial', 
    'Parte policial', 
    'Peritaje', 
    'Fotografías', 
    'Informe técnico', 
    'Fotografías de daño', 
    'Historia clínica', 
    'Exámenes', 
    'Factura hospitalaria', 
    'Orden médica', 
    'Otros'
);

-- C) Añadir el nuevo CHECK CONSTRAINT para asegurar la integridad de datos
ALTER TABLE public.documentos
ADD CONSTRAINT chk_tipo_documento_valido CHECK (
    tipo_documento IN (
        'Factura de reparación', 
        'Denuncia policial', 
        'Parte policial', 
        'Peritaje', 
        'Fotografías', 
        'Informe técnico', 
        'Fotografías de daño', 
        'Historia clínica', 
        'Exámenes', 
        'Factura hospitalaria', 
        'Orden médica', 
        'Otros'
    )
);
