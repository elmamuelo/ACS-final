# Guía Práctica de Sugerencias para Pruebas Manuales, Ejecución Automatizada y Captura de Evidencias

**Asignatura:** Aseguramiento de la Calidad (ACS) – Ingeniería de Sistemas (ITM)  
**Sistema bajo prueba (SUT):** InvenTree – Open Source Inventory Management System  
**Equipo de Pruebas:**
1. **Emanuel Ortiz** (Pruebas de Autenticación, Seguridad de Acceso, Partes y Valores Límite de URL/Stock)
2. **Manuela Sanchez** (Pruebas de Categorías, Reglas de Eliminación de Partes, Partes Virtuales, Ubicaciones Estructurales y Serialización)
3. **Juan Torres** (Pruebas de Listas de Materiales BOM, Movimientos de Stock, Órdenes de Compra y Pruebas de Rendimiento)

---

## 1. ¿Dónde ejecutar las pruebas manuales rápidamente para tomar las capturas?

Tienes **dos opciones** para ejecutar las pruebas manuales y tomar las capturas de pantalla para el informe en Word:

1. **Opción A – Servidor Demo Oficial de InvenTree (Inmediata, sin instalar nada):**
   - **URL:** `https://demo.inventree.org/`
   - **Usuario Administrador / Ingeniero:** `admin` / `inventree` (o `allaccess` / `nolimits`, o `reader` / `readonly` para probar permisos restringidos).
   - *Ventaja:* Ya tiene categorías, partes, ubicaciones y órdenes precargadas; ideal para tomar las capturas de pantalla de los 12 casos manuales en pocos minutos.

2. **Opción B – Entorno Local (Docker o Servidor de Desarrollo Django + Vite):**
   - **URL Local:** `http://localhost:8000/web/login`
   - Para ejecutar la suite automatizada en consola desde el entorno virtual del backend:
     ```bash
     pytest "ACS final test/scripts/test_acs_backend_models.py" -v
     pytest "ACS final test/scripts/test_acs_api_integration.py" -v
     pytest "ACS final test/scripts/test_acs_performance.py" -v -s
     ```

---

## 2. Sugerencias Paso a Paso para los 12 Casos de Prueba Manuales (y qué capturar)

### Bloque 1 – Responsable: **Emanuel Ortiz** (`CP-MAN-01` a `CP-MAN-04`)

#### **CP-MAN-01: Inicio de sesión válido e inválido en la Interfaz Web (Partición de Equivalencia)**
- **Dónde ir:** Pantalla de Login (`/web/login`).
- **Paso 1 (Caso Inválido):** Ingresa usuario `usuario_invalido` y contraseña `clave_erronea`. Haz clic en **Log In**.
  - **Captura sugerida 1A:** Captura el mensaje emergente rojo **"Login failed - Check your input and try again"**.
- **Paso 2 (Caso Válido):** Ingresa credenciales válidas (`admin` / `inventree`). Haz clic en **Log In**.
  - **Captura sugerida 1B:** Captura el **Dashboard principal (`/web/home`)** con la sesión iniciada.

#### **CP-MAN-02: Creación de Parte con datos válidos vs. nombre vacío (Partición de Equivalencia)**
- **Dónde ir:** Menú lateral -> **Parts** (`/web/part/`) -> Botón **Create Part** (icono `+`).
- **Paso 1 (Caso Inválido):** Deja el campo **Name** vacío (`""`), escribe en **Description** `"Prueba sin nombre"` y presiona **Submit**.
  - **Captura sugerida 2A:** Captura el formulario mostrando el borde rojo en el campo **Name** con el mensaje `"This field is required"` / `"Este campo es obligatorio"`.
- **Paso 2 (Caso Válido):** Ingresa **Name:** `Microcontrolador ESP32-WROOM`, **IPN:** `MCU-ESP32-01`, **Description:** `Módulo Wi-Fi + Bluetooth Dual Core`, selecciona una categoría y presiona **Submit**.
  - **Captura sugerida 2B:** Captura la vista de detalle de la parte recién creada.

#### **CP-MAN-03: Validación de Valores Límite en Cantidad Inicial de Stock (`-1`, `0`, `1`)**
- **Dónde ir:** Dentro de cualquier Parte activa (no virtual) -> Pestaña **Stock** -> Botón **New Stock Item** (o al crear una parte con stock inicial).
- **Paso 1 (Frontera Inválida `-1`):** En el campo **Quantity**, escribe `-1` e intenta guardar (**Submit**).
  - **Captura sugerida 3A:** Captura el error de validación bajo el campo **Quantity** indicando que el valor debe ser mayor o igual a cero (`"Ensure this value is greater than or equal to 0"` / `"Quantity must be greater than zero"`).
- **Paso 2 (Fronteras Válidas `0` y `1`):** Cambia **Quantity** a `1` (o `100`), selecciona una ubicación válida (ej. `Warehouse` / `Bodega Central`) y guarda.
  - **Captura sugerida 3B:** Captura el ítem de stock creado en la tabla con estado **OK**.

#### **CP-MAN-04: Validación de Esquema y Longitud Límite en Enlace Externo (`StockItem.link`)**
- **Dónde ir:** Abre un **Stock Item** -> Menú **Actions / Edit Stock Item**.
- **Paso 1 (Esquema Inválido):** En el campo **External Link**, ingresa `httpx://url-invalida.com` o `texto_sin_esquema` y presiona **Submit**.
  - **Captura sugerida 4A:** Captura el mensaje de error `"Enter a valid URL"`.
- **Paso 2 (Esquema Válido):** Ingresa `https://inventree.org/datasheet.pdf` y guarda.

---

### Bloque 2 – Responsable: **Manuela Sanchez** (`CP-MAN-05` a `CP-MAN-08`)

#### **CP-MAN-05: Tabla de Decisión para Eliminación de Parte Activa vs. Parte Inactiva**
- **Dónde ir:** Vista de detalle de una Parte de prueba (`/web/part/<id>`).
- **Paso 1 (Parte Activa `active=True`):** Con el interruptor **Active** encendido, abre el menú **Actions (tres puntos / icono de acciones)** -> intenta seleccionar **Delete Part** (o intenta eliminar vía modal).
  - **Captura sugerida 5A:** Captura cómo el sistema bloquea la acción o muestra el error `"Cannot delete this part as it is still active"`.
- **Paso 2 (Parte Inactiva `active=False`):** Edita la parte (**Edit Part**), desmarca la casilla **Active**, guarda los cambios, y ahora selecciona **Actions -> Delete Part**.
  - **Captura sugerida 5B:** Captura la confirmación de eliminación exitosa.

#### **CP-MAN-06: Restricción de Almacenamiento en Ubicación Estructural (`structural = True`)**
- **Dónde ir:** Menú **Stock** -> **Stock Locations** (`/web/stock/location/`).
- **Paso 1:** Crea o selecciona una ubicación que tenga marcada la casilla **Structural** (`Structural = True`, ej. `"Bloque Norte Estructural"`).
- **Paso 2:** Intenta crear o transferir un **Stock Item** asignándolo a esa ubicación estructural.
  - **Captura sugerida 6:** Captura el mensaje de validación `"Stock items cannot be located into structural stock locations!"` (o la restricción en el selector).

#### **CP-MAN-07: Restricción de Creación de Stock en Parte Virtual (`virtual = True`)**
- **Dónde ir:** Menú **Parts** -> Crea o selecciona una parte con el atributo **Virtual** activado (`Virtual = True`, ej. `"Licencia Software CAD"`).
- **Paso 1:** Revisa la sección de Stock o intenta crear un `StockItem` asociado a esa parte virtual (desde formulario o API `/api/stock/`).
  - **Captura sugerida 7:** Captura la restricción donde se impide crear stock físico para una parte virtual (`"Stock item cannot be created for virtual parts"`).

#### **CP-MAN-08: Control de Números de Serie Únicos y Cantidad Unitaria (`quantity = 1`)**
- **Dónde ir:** Selecciona una parte con atributo **Trackable** activado (`Trackable = True`).
- **Paso 1 (Creación válida con serial):** Crea un **New Stock Item** con **Quantity:** `1` y **Serial Numbers:** `SN-100`. Guarda.
- **Paso 2 (Intento de serial duplicado o cantidad incongruente):** Intenta crear otro **New Stock Item** para la misma parte con **Quantity:** `1` y el mismo **Serial Numbers:** `SN-100` (o **Quantity:** `3` con un solo serial `SN-101`).
  - **Captura sugerida 8:** Captura el error de validación `"Stock item with this serial number already exists: SN-100"` o `"Number of unique serial numbers (1) must match quantity (3)"`.

---

### Bloque 3 – Responsable: **Juan Torres** (`CP-MAN-09` a `CP-MAN-12`)

#### **CP-MAN-09: Prevención de Referencia Circular/Autorreferencial en Lista de Materiales (BOM)**
- **Dónde ir:** Selecciona una parte tipo **Assembly** (`Assembly = True`) -> Pestaña **Bill of Materials (BOM)** -> Botón **Add BOM Item**.
- **Paso 1:** En el campo **Sub Part**, intenta buscar o seleccionar la **misma parte padre** (o vía API `/api/bom/`) con **Quantity:** `2`.
  - **Captura sugerida 9:** Captura el rechazo de validación `"Part '...' cannot be used in BOM for '...' (recursive)"`.

#### **CP-MAN-10: Operaciones de Conteo, Adición (`Add Stock`) y Retiro (`Remove Stock`) con Límites**
- **Dónde ir:** Abre un **Stock Item** que tenga `Quantity = 100` -> Botones de ajuste rápido de stock (**Add Stock** / **Remove Stock**).
- **Paso 1:** Usa **Add Stock** para sumar `25` unidades con nota `"Ingreso lote QA"`. Verifica que el saldo pase a `125`.
- **Paso 2:** Usa **Remove Stock** para retirar `40` unidades. Verifica que el saldo pase a `85` y revisa la pestaña **Stock Tracking / History**.
  - **Captura sugerida 10:** Captura la pestaña **Stock Tracking** donde se evidencian las entradas de historial (`Added stock`, `Removed stock`) con fecha, usuario y cantidad.

#### **CP-MAN-11: Transferencia Parcial de Stock entre Ubicaciones (`Split & Transfer`)**
- **Dónde ir:** En el mismo **Stock Item** (con `85` unidades en `Ubicación A`), haz clic en **Transfer Stock**.
- **Paso 1:** Ingresa **Quantity:** `20` (menor que 85), selecciona como destino `Ubicación B` y confirma.
  - **Captura sugerida 11:** Captura la tabla de Stock mostrando cómo el lote se dividió: `65` unidades permanecen en `Ubicación A` y un nuevo ítem hijo de `20` unidades aparece en `Ubicación B`.

#### **CP-MAN-12: Flujo de Orden de Compra (`PurchaseOrder`) y Restricción de Acceso por Rol (`RBAC`)**
- **Dónde ir:** Menú **Purchasing -> Purchase Orders** (`/web/purchasing/purchase-order/`).
- **Paso 1:** Con el usuario administrador/ingeniero, crea una Orden de Compra hacia un proveedor (`Supplier`), verifica que inicie en estado **Pending**, agrega una línea de pedido (**Add Line Item**) y emítela (**Issue Order** -> pasa a estado **Placed / Issued**).
  - **Captura sugerida 12A:** Captura el detalle de la Orden de Compra en estado **Placed** con su línea de pedido.
- **Paso 2:** Inicia sesión con un usuario de solo lectura (ej. `reader` / `readonly` en la demo) y verifica que los botones de creación/edición/eliminación no estén habilitados.
  - **Captura sugerida 12B:** Captura la vista con usuario de solo lectura sin botones de edición.

---

## 3. Lista de Chequeo de Capturas para Pegar en el Informe Word

En el documento Word (`Informe_Caso_Practico_Final_ACS_InvenTree.docx`) encontrarás recuadros resaltados con el texto `[ESPACIO PARA EVIDENCIA / CAPTURA DE PANTALLA #...]`. Aquí tienes el resumen de qué pegar en cada uno:

1. **Sección 3 (Contexto del Proyecto):** Diagrama de arquitectura (ya incluimos un esquema estructurado en tablas dentro del Word, puedes dejarlo así o pegar una imagen de arquitectura).
2. **Sección 7.1 (Evidencias de Pruebas Funcionales Manuales):** Capturas de los casos manuales (`CP-MAN-01` a `CP-MAN-12`).
3. **Sección 7.2 / Sección 8 (Evidencias de Pruebas Automatizadas):** Captura de la terminal ejecutando `pytest` sobre `test_acs_backend_models.py`, `test_acs_api_integration.py` y Playwright.
4. **Sección 7.3 (Evidencia de Prueba de Rendimiento):** Captura de la consola ejecutando `test_acs_performance.py` con la tabla de latencias en milisegundos (Media, Mediana, $P_{95}$, Máximo).
5. **Sección 8.6 (Evidencia de Integración CI/CD):** Captura de la pestaña **Actions** del repositorio de GitHub (`qc_checks.yaml` / `frontend.yaml`).
6. **Sección 9 (Gestión de Defectos):** Captura de un Issue en GitHub Issues o del formulario donde se evidencia el defecto reportado.
7. **Sección 10 (Pruebas de Seguridad OWASP Top 10):** Captura de respuesta HTTP `401 Unauthorized` / `403 Forbidden` en navegador/Postman o pantalla de bloqueo de login / configuración de permisos RBAC.

