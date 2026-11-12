/**
 * Verificador y Registro de Ejecución de los 12 Casos de Prueba Manuales + Matriz de Defectos
 * Caso Práctico Final - Aseguramiento de la Calidad (ACS) - ITM
 * Responsables: Emanuel Ortiz, Manuela Sánchez, Juan Torres
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPORTS_DIR = path.resolve(__dirname, '..', 'reports');

fs.mkdirSync(REPORTS_DIR, { recursive: true });

const manualTestCases = [
  {
    id: 'CP-MAN-01',
    name: 'Autenticación Basic Auth rechazada cuando el usuario tiene MFA activo',
    responsible: 'Juan Torres',
    requirement: 'RF01 / RNF03',
    technique: 'Tabla de Decisión',
    preconditions: 'BASIC_AUTH_ENABLED=True; Usuario "jtorres" activo con MFA TOTP habilitado (is_mfa_enabled=True).',
    inputData: 'Header Authorization: Basic anRvcnJlczpTZWN1cmVQYXNzMTIzIQ== hacia GET /api/part/',
    steps: [
      '1. Configurar cuenta de usuario con dispositivo TOTP MFA activo.',
      '2. Enviar petición HTTP GET /api/part/ usando cabecera Basic Authentication.',
      '3. Inspeccionar respuesta de InvenTreeBasicAuthentication.authenticate_credentials (users/authentication.py:L51-L60).'
    ],
    expectedResult: 'HTTP 401 Unauthorized con mensaje "INVE-W20: Password authentication not allowed due to MFA".',
    obtainedResult: 'HTTP 401 Unauthorized: password_auth_allowed(user) retorna False cuando is_mfa_enabled(user) es True, lanzando AuthenticationFailed("INVE-W20: Password authentication not allowed due to MFA").',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-02',
    name: 'Rechazo de creación o eliminación de Parte bloqueada (Part.locked=True)',
    responsible: 'Manuela Sánchez',
    requirement: 'RF02',
    technique: 'Transición de Estados',
    preconditions: 'Ajuste global PART_ENABLE_LOCKING=True; Parte ID=104 ("PCB Controlador V2") en estado locked=True, active=False.',
    inputData: 'DELETE /api/part/104/ y POST /api/part/parameter/ con {"part": 104, "template": 1, "data": "12V"}',
    steps: [
      '1. Marcar la parte ID=104 con el atributo locked=True.',
      '2. Intentar modificar o agregar un parámetro mediante Part.check_parameter_save (part/models.py:L592-L596).',
      '3. Intentar eliminar la parte mediante Part.delete (part/models.py:L597-L607).'
    ],
    expectedResult: 'Se bloquea tanto la modificación de parámetros ("Cannot modify parameters of a locked part") como la eliminación ("Cannot delete this part as it is locked").',
    obtainedResult: 'Ambas operaciones lanzan ValidationError (HTTP 400) preservando la inmutabilidad de la parte bloqueada.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-03',
    name: 'Prevención de recursividad directa e indirecta en Lista de Materiales (BOM)',
    responsible: 'Manuela Sánchez',
    requirement: 'RF02',
    technique: 'Partición de Equivalencia (Grafo de Dependencias)',
    preconditions: 'Parte A (Ensamble padre, pk=10, tree_id=5) y Parte B (Sub-ensamble hijo, pk=11, tree_id=5 variante de A).',
    inputData: 'POST /api/bom/ con {"part": 10, "sub_part": 10, "quantity": 1} y {"part": 10, "sub_part": 11, "quantity": 2}',
    steps: [
      '1. Intentar agregar la Parte A como sub_part de sí misma en Part.check_add_to_bom (part/models.py:L682-L742).',
      '2. Intentar agregar la Parte B (misma familia variant tree_id=5) como sub_part de la Parte A.'
    ],
    expectedResult: 'Ambos intentos fallan con ValidationError indicando referencia recursiva ("cannot be used in BOM for ... (recursive)").',
    obtainedResult: 'Part.check_add_to_bom detecta pk == parent.pk (línea 695) y tree_id == parent.tree_id (línea 709), rechazando la relación circular.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-04',
    name: 'Validación de conversión a categoría estructural con partes asignadas',
    responsible: 'Manuela Sánchez',
    requirement: 'RF02',
    technique: 'Tabla de Decisión',
    preconditions: 'Categoría "Sensores Industriales" (pk=4, structural=False) con 3 partes activas asociadas directamente.',
    inputData: 'PATCH /api/part/category/4/ con {"structural": true}',
    steps: [
      '1. Verificar que partcount(False, False) de la categoría pk=4 es > 0 (3 partes).',
      '2. Cambiar el flag structural=True y ejecutar PartCategory.clean() (part/models.py:L174-L186).'
    ],
    expectedResult: 'Rechaza el cambio con ValidationError: "You cannot make this part category structural because some parts are already assigned to it!".',
    obtainedResult: 'Se lanza ValidationError en PartCategory.clean() (línea 180) impidiendo que una categoría con partes pase a ser estructural.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-05',
    name: 'Serialización de lote de Stock en valores límite (Cantidad = 0, 1, 1000 y 1001)',
    responsible: 'Emanuel Ortiz',
    requirement: 'RF03',
    technique: 'Análisis de Valores Límite (BVA)',
    preconditions: 'Parte rastreable (trackable=True) con lote StockItem de quantity=1500 unidades sin serializar.',
    inputData: 'Caso A: qty=0 | Caso B: qty=1, serial="SN0001" | Caso C: qty=1000, serial="1+" | Caso D: qty=1001, serial="1+"',
    steps: [
      '1. Invocar StockItem.serializeStock con quantity=0 (stock/models.py:L2528).',
      '2. Invocar extract_serial_numbers y serializeStock con quantity=1 y quantity=1000 (helpers.py:L647).',
      '3. Invocar extract_serial_numbers con quantity=1001.'
    ],
    expectedResult: 'Caso A falla ("Quantity must be greater than zero"); Casos B y C tienen éxito; Caso D falla ("Cannot serialize more than 1000 items at once").',
    obtainedResult: 'Las 4 fronteras se comportan exactamente según especificación: 0 y 1001 son rechazados, mientras que 1 y 1000 generan los StockItems serializados.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-06',
    name: 'Bloqueo de desinstalación de StockItem hacia una ubicación estructural',
    responsible: 'Emanuel Ortiz',
    requirement: 'RF04',
    technique: 'Partición de Equivalencia',
    preconditions: 'StockItem hijo (pk=88) instalado dentro de un ensamble padre (belongs_to=50); StockLocation "Bodega Central" marcada con structural=True.',
    inputData: 'POST /api/stock/88/uninstall/ con {"location": 12, "notes": "Retiro por mantenimiento"}',
    steps: [
      '1. Seleccionar el ítem instalado pk=88.',
      '2. Ejecutar StockItem.uninstall_into_location(location, user, notes) (stock/models.py:L1997-L2036) apuntando a una ubicación con structural=True.'
    ],
    expectedResult: 'Se rechaza la operación con ValidationError({"location": "Cannot assign stock to structural location"}).',
    obtainedResult: 'La validación en stock/models.py:L2009-L2012 intercepta location.structural == True y aborta la transacción atómica.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-07',
    name: 'Fusión de lotes de Stock (merge_stock_items) con asignaciones activas de Órdenes de Venta',
    responsible: 'Emanuel Ortiz',
    requirement: 'RF06 / RNF02',
    technique: 'Transición de Estados / Prueba de Integración',
    preconditions: 'StockItem A (pk=201, qty=50) y StockItem B (pk=202, qty=30) de la misma parte no serializada y misma ubicación. StockItem B tiene una SalesOrderAllocation activa (pk=501, qty=10) y una TransferOrderAllocation (pk=601, qty=5).',
    inputData: 'POST /api/stock/merge/ fusionando other_items=[StockItem(202)] dentro de StockItem(201).',
    steps: [
      '1. Verificar que can_merge() permite fusionar StockItem A y StockItem B (ninguno tiene sales_order directo, sino SalesOrderAllocation).',
      '2. Ejecutar StockItem.merge_stock_items([other]) (stock/models.py:L2781-L2875).',
      '3. Consultar SalesOrderAllocation(501) y TransferOrderAllocation(601) tras other.delete().'
    ],
    expectedResult: 'StockItem A queda con quantity=80 y las asignaciones SalesOrderAllocation(501) y TransferOrderAllocation(601) quedan vinculadas a StockItem A (item_id=201).',
    obtainedResult: 'FALLO CRÍTICO (DEF-01): En stock/models.py:L2866 se asigna "allocation.stock_item = self", pero el campo FK en SalesOrderAllocation se llama "item". Al ejecutarse other.delete() en la línea 2874 (con on_delete=CASCADE), las asignaciones de venta y de transferencia se ELIMINAN por cascada en la base de datos.',
    status: 'FALLIDO'
  },
  {
    id: 'CP-MAN-08',
    name: 'Validación de completitud de embarque de Orden de Venta (SalesOrderShipment.check_can_complete)',
    responsible: 'Manuela Sánchez',
    requirement: 'RF05',
    technique: 'Tabla de Decisión',
    preconditions: 'Ajuste global SALESORDER_SHIPMENT_REQUIRES_CHECK=True; Embarque SO-SHIP-09 con 2 asignaciones pero con checked_by=None.',
    inputData: 'POST /api/order/so/shipment/9/ship/ con {"shipment_date": "2026-11-11"}',
    steps: [
      '1. Crear SalesOrderShipment sin ítems asignados e intentar completarlo -> debe fallar.',
      '2. Asignar 2 StockItems al embarque dejando checked_by=None con SALESORDER_SHIPMENT_REQUIRES_CHECK=True.',
      '3. Invocar SalesOrderShipment.check_can_complete() (order/models.py:L2950-L2978).'
    ],
    expectedResult: 'Rechaza el despacho con ValidationError("Shipment must be checked before it can be completed") hasta que se marque como verificado.',
    obtainedResult: 'check_can_complete() valida secuencialmente shipment_date, allocations.count() == 0 e is_checked(), lanzando los errores esperados.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-09',
    name: 'Limpieza e importación de cantidades decimales con múltiples separadores de miles (clean_decimal)',
    responsible: 'Emanuel Ortiz',
    requirement: 'RF09',
    technique: 'Partición de Equivalencia',
    preconditions: 'Módulo de importación tabular procesando valores numéricos mediante InvenTree.helpers.clean_decimal (helpers.py:L901-L938).',
    inputData: 'Entrada 1: "1.250,50" | Entrada 2: "1,250.50" | Entrada 3: "1,234,567" (dos comas de miles, sin decimales)',
    steps: [
      '1. Evaluar clean_decimal("1.250,50") y clean_decimal("1,250.50").',
      '2. Evaluar clean_decimal("1,234,567") donde count_comma == 2 y count_point == 0.'
    ],
    expectedResult: 'Entradas 1 y 2 retornan Decimal("1250.5"); Entrada 3 retorna Decimal("1234567").',
    obtainedResult: 'FALLO (DEF-04): Las Entradas 1 y 2 retornan 1250.5 correctamente, pero para "1,234,567" count_comma es 2; ninguna rama condicional elimina las comas, Decimal("1,234,567") lanza InvalidOperation y clean_decimal retorna silenciosamente Decimal(0).',
    status: 'FALLIDO'
  },
  {
    id: 'CP-MAN-10',
    name: 'Sanitización de etiquetas HTML y entidades comerciales en campos de texto (strip_html_tags)',
    responsible: 'Juan Torres',
    requirement: 'RF07 / RNF03',
    technique: 'Partición de Equivalencia + Valores Límite',
    preconditions: 'Validación activa mediante InvenTree.helpers.strip_html_tags(value, raise_error=True) (helpers.py:L941-L961).',
    inputData: 'Caso 1: "<script>evil()</script> Capacitor" | Caso 2: "Modulo R&amp;D Industrial" (texto sin etiquetas HTML pero con entidad &amp;)',
    steps: [
      '1. Pasar el Caso 1 con etiqueta <script> a strip_html_tags(value, raise_error=True).',
      '2. Pasar el Caso 2 ("Modulo R&amp;D Industrial") a strip_html_tags(value, raise_error=True).'
    ],
    expectedResult: 'Caso 1 debe lanzar ValidationError por contener HTML; Caso 2 debe aceptarse por no contener etiquetas HTML.',
    obtainedResult: 'FALLO (DEF-05): El Caso 1 se bloquea correctamente, pero en el Caso 2 nh3.clean mantiene "&amp;" y el reemplazo posterior (línea 954) lo convierte en "&", cambiando len(cleaned) de 25 a 21 y disparando un falso positivo ValidationError("Remove HTML tags from this value").',
    status: 'FALLIDO'
  },
  {
    id: 'CP-MAN-11',
    name: 'Validación de unidades físicas del Sistema Internacional con Pint (validate_physical_units)',
    responsible: 'Juan Torres',
    requirement: 'RF09',
    technique: 'Partición de Equivalencia',
    preconditions: 'Registro de unidades físicas InvenTree.conversion.get_unit_registry() inicializado (validators.py:L20-L44).',
    inputData: 'Partición válida: "kohm", "mm", "uF", "" (vacío) | Partición inválida: "unidad_inexistente_xyz", "123///["',
    steps: [
      '1. Invocar validate_physical_units con unidades válidas ("kohm", "mm", "uF", "").',
      '2. Invocar validate_physical_units con una unidad inexistente y con una expresión malformada que rompe el tokenizador.'
    ],
    expectedResult: 'Las unidades válidas y vacías pasan sin error; las inválidas o malformadas lanzan ValidationError("Invalid physical unit").',
    obtainedResult: 'Todas las particiones válidas son aceptadas y las inválidas/malformadas son capturadas por los bloques except (UndefinedUnitError, TokenError, Exception) lanzando ValidationError.',
    status: 'APROBADO'
  },
  {
    id: 'CP-MAN-12',
    name: 'Diagnóstico de URL de sitio sin dominio de nivel superior (invalid_site_url_hint)',
    responsible: 'Juan Torres',
    requirement: 'RNF04',
    technique: 'Partición de Equivalencia',
    preconditions: 'Configuración de SITE_URL evaluada por InvenTree.validators.invalid_site_url_hint (validators.py:L93-L124).',
    inputData: 'URL 1: "http://localhost:8000" | URL 2: "http://192.168.1.50:8000" | URL 3: "http://warehouse:8000"',
    steps: [
      '1. Evaluar invalid_site_url_hint para localhost e IPv4.',
      '2. Evaluar invalid_site_url_hint para el hostname local sin TLD "http://warehouse:8000" e inspeccionar la redacción del mensaje INVE-E17.'
    ],
    expectedResult: 'URL 1 y URL 2 retornan cadena vacía ""; URL 3 retorna advertencia INVE-E17 bien formateada indicando "' + "'warehouse' has no top-level domain" + '".',
    obtainedResult: 'FALLO MENOR DE USABILIDAD (DEF-06): En validators.py:L118 la cadena f-string tiene un carácter "i" erróneo tras el salto de línea: "\\ni\'warehouse\' has no top-level domain".',
    status: 'FALLIDO'
  }
];

const passedManual = manualTestCases.filter((c) => c.status === 'APROBADO').length;
const failedManual = manualTestCases.filter((c) => c.status === 'FALLIDO').length;

const logLines = [
  '========================================================================================',
  '  REGISTRO DE EJECUCIÓN DE CASOS DE PRUEBA MANUALES - CASO PRÁCTICO FINAL ACS (ITM)',
  '  Sistema Bajo Prueba (SUT): InvenTree v1.7.0 (Commit af5055b33)',
  `  Fecha de Consolidación: ${new Date().toISOString()}`,
  '  Equipo QA: Emanuel Ortiz (4 casos) | Manuela Sánchez (4 casos) | Juan Torres (4 casos)',
  '========================================================================================',
  ''
];

for (const tc of manualTestCases) {
  logLines.push(`[${tc.status}] ${tc.id} - ${tc.name}`);
  logLines.push(`  Responsable        : ${tc.responsible}`);
  logLines.push(`  Requisito Asociado : ${tc.requirement}`);
  logLines.push(`  Técnica Aplicada   : ${tc.technique}`);
  logLines.push(`  Precondiciones     : ${tc.preconditions}`);
  logLines.push(`  Datos de Entrada   : ${tc.inputData}`);
  logLines.push(`  Resultado Esperado : ${tc.expectedResult}`);
  logLines.push(`  Resultado Obtenido : ${tc.obtainedResult}`);
  logLines.push('----------------------------------------------------------------------------------------');
}

logLines.push(
  `RESUMEN MANUALES: Total=${manualTestCases.length} | Aprobados=${passedManual} (${((passedManual / manualTestCases.length) * 100).toFixed(2)}%) | Fallidos=${failedManual} (${((failedManual / manualTestCases.length) * 100).toFixed(2)}%)`
);
logLines.push('========================================================================================');

fs.writeFileSync(path.join(REPORTS_DIR, 'manual_test_execution_log.txt'), logLines.join('\n'), 'utf8');

// Exportación de Matriz de Defectos (CSV)
const defects = [
  {
    id: 'DEF-01',
    title: 'Pérdida por borrado en cascada de SalesOrderAllocation y TransferOrderAllocation al fusionar StockItems',
    severity: 'Crítico',
    priority: 'Alta (P1)',
    status: 'Abierto / Parche Propuesto',
    responsible: 'Emanuel Ortiz',
    file: 'src/backend/InvenTree/stock/models.py#L2864-L2874',
    relatedCases: 'CP-MAN-07, CP-AUT-04',
    description: 'En StockItem.merge_stock_items() se asigna allocation.stock_item = self sobre SalesOrderAllocation, pero el campo FK real es "item". Al ejecutar other.delete() en la línea 2874 con on_delete=CASCADE, todas las asignaciones de venta y transferencia del lote fusionado se eliminan silenciosamente.'
  },
  {
    id: 'DEF-02',
    title: 'Exposición total de token secreto en sanitize_token() cuando el parámetro back=0',
    severity: 'Alto',
    priority: 'Alta (P1)',
    status: 'Abierto / Parche Propuesto',
    responsible: 'Juan Torres',
    file: 'src/backend/InvenTree/InvenTree/helpers.py#L1173-L1196',
    relatedCases: 'CP-AUT-06',
    description: 'En sanitize_token(), cuando back=0, la expresión Python token_value[-back:] se evalúa como token_value[-0:] == token_value[0:], concatenando el token secreto completo sin enmascarar al final de los asteriscos.'
  },
  {
    id: 'DEF-03',
    title: 'Retorno de números negativos en extract_int() cuando allow_negative=False y el valor es menor que -clip',
    severity: 'Medio',
    priority: 'Media (P2)',
    status: 'Abierto / Parche Propuesto',
    responsible: 'Emanuel Ortiz',
    file: 'src/backend/InvenTree/InvenTree/helpers.py#L52-L85',
    relatedCases: 'CP-AUT-07',
    description: 'En la función interna do_clip() de extract_int(), la condición elif value < -clip: return -clip retorna un valor negativo antes de evaluar if not allow_negative: value = abs(value). Además, si clip=None retorna el negativo sin aplicar valor absoluto.'
  },
  {
    id: 'DEF-04',
    title: 'Corrupción a cero en clean_decimal() para números con dos o más separadores de miles',
    severity: 'Medio',
    priority: 'Media (P2)',
    status: 'Abierto',
    responsible: 'Emanuel Ortiz',
    file: 'src/backend/InvenTree/InvenTree/helpers.py#L901-L938',
    relatedCases: 'CP-MAN-09, CP-AUT-02',
    description: 'En clean_decimal(), si la cadena tiene múltiples comas o puntos de miles sin separador decimal (ej. "1,234,567"), count_comma es 2, ninguna rama condicional remueve las comas y Decimal() falla devolviendo Decimal(0).'
  },
  {
    id: 'DEF-05',
    title: 'Falso positivo de detección XSS en strip_html_tags() y desbordamiento en constructPathString()',
    severity: 'Medio',
    priority: 'Baja (P3)',
    status: 'Abierto',
    responsible: 'Juan Torres',
    file: 'src/backend/InvenTree/InvenTree/helpers.py#L157-L171, L941-L961',
    relatedCases: 'CP-MAN-10',
    description: 'strip_html_tags() des-escapa entidades (&amp; -> &) después de nh3.clean() y compara len(cleaned) != len(value), lanzando ValidationError ante texto legítimo con entidades. Asimismo, constructPathString() con max_chars=4 calcula n=0 y duplica la cadena con pathstring[-0:].'
  },
  {
    id: 'DEF-06',
    title: 'Error tipográfico en mensaje de diagnóstico INVE-E17 y docstring erróneo en order/validators.py',
    severity: 'Bajo',
    priority: 'Baja (P4)',
    status: 'Cerrado / Documentado',
    responsible: 'Manuela Sánchez',
    file: 'src/backend/InvenTree/InvenTree/validators.py#L118, order/validators.py#L82',
    relatedCases: 'CP-MAN-12',
    description: 'En invalid_site_url_hint() aparece el carácter espurio "\\ni\'{hostname}\'" en el mensaje INVE-E17, y en validate_transfer_order_reference() el docstring menciona ReturnOrder en lugar de TransferOrder.'
  }
];

const csvHeader = 'ID,Titulo,Severidad,Prioridad,Estado,Responsable,Archivo_Linea,Casos_Asociados,Descripcion\n';
const csvRows = defects
  .map((d) =>
    [d.id, d.title, d.severity, d.priority, d.status, d.responsible, d.file, d.relatedCases, d.description]
      .map((val) => `"${String(val).replace(/"/g, '""')}"`)
      .join(',')
  )
  .join('\n');

fs.writeFileSync(path.join(REPORTS_DIR, 'defect_report_matrix.csv'), csvHeader + csvRows + '\n', 'utf8');
console.log(`Casos manuales procesados: ${manualTestCases.length} (${passedManual} aprobados, ${failedManual} fallidos). Defectos exportados: ${defects.length}.`);

