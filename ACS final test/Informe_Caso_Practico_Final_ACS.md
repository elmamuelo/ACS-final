# Caso Práctico Final: Aseguramiento de la Calidad de Software (InvenTree)

---

## 1. Portada

- **Institución:** Institución Universitaria ITM — Facultad de Ingenierías
- **Programa Académico:** Ingeniería de Sistemas
- **Nombre de la Asignatura:** Aseguramiento de la Calidad (ACS)
- **Título del Trabajo:** Planificación, Diseño, Ejecución y Automatización de Actividades de Aseguramiento de Calidad sobre el Sistema de Gestión de Inventarios Open-Source *InvenTree*
- **Integrantes del Equipo:**
  - **Emanuel Ortiz**
  - **Manuela Sánchez**
  - **Juan Torres**
- **Fecha:** 11 de noviembre de 2026 *(Fecha límite de entrega: 22 de noviembre de 2026)*
- **Repositorio y Recursos del Proyecto:**
  - **Repositorio Oficial Upstream:** https://github.com/inventree/InvenTree
  - **Documentación Técnica Oficial:** https://docs.inventree.org/en/latest/
  - **Versión / Commit Analizado:** `v1.7.0` (API `v449` — Commit `af5055b33`)
  - **Carpeta de Pruebas y Entregables:** [`ACS final test/`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/ACS%20final%20test)

---

## 2. Introducción

### 2.1 Presentación Breve del Proyecto de Software
**InvenTree** es un sistema empresarial de gestión de inventarios y control de existencias de código abierto (*Open-Source Inventory Management System*), diseñado para proporcionar trazabilidad de bajo nivel sobre piezas, componentes electrónicos, lotes de producción, almacenes jerárquicos, órdenes de compra, órdenes de venta y listas de materiales (*Bill of Materials - BOM*). Su núcleo está construido sobre un backend transaccional en **Python/Django** y **Django REST Framework (DRF)**, acoplado a una interfaz web moderna tipo *Single Page Application (SPA)* desarrollada en **React 19**, **TypeScript** y **Mantine UI**.

### 2.2 Objetivo General del Caso Práctico
Aplicar de manera práctica, rigurosa e integrada los principios, estándares (IEEE 829 / ISO/IEC/IEEE 29119 / ISO/IEC 25010) y técnicas de Aseguramiento de la Calidad de Software mediante la planificación, diseño, automatización, ejecución y análisis de pruebas funcionales y no funcionales, gestión del ciclo de vida de defectos y cálculo de métricas de calidad sobre el sistema real **InvenTree**.

### 2.3 Justificación de la Elección del Sistema
La selección de **InvenTree** como Sistema Bajo Prueba (*System Under Test - SUT*) responde a criterios técnicos que permiten evaluar escenarios complejos de ingeniería de software:
1. **Reglas de negocio de alta criticidad e integridad aritmética:** El manejo de inventario serializado, partición de lotes (`splitStock`), fusión de existencias (`merge_stock_items`) y asignaciones simultáneas a órdenes de fabricación, venta y transferencia exige validaciones estrictas de fronteras y control de concurrencia mediante bloqueos pesimistas (`select_for_update`).
2. **Arquitectura moderna y desacoplada (API-First):** Expone una API RESTful completamente documentada bajo OpenAPI 3.0 con más de 150 endpoints y mecanismos robustos de seguridad (Tokens Bearer con *pepper* criptográfico, OAuth2 con alcances y autenticación multifactor MFA).
3. **Ecosistema real de pruebas e integración continua:** Cuenta con flujos de trabajo en GitHub Actions ([`.github/workflows/qc_checks.yaml`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/.github/workflows/qc_checks.yaml)), pruebas unitarias en Django/Pytest, pruebas E2E en Playwright y pruebas de rendimiento con CodSpeed, lo que permite contrastar prácticas industriales reales e identificar defectos latentes en producción.

---

## 3. Contexto del Proyecto

### 3.1 Funcionalidad General del Sistema
InvenTree estructura la operación logística e industrial en seis dominios funcionales principales:
- **Gestión de Partes y Categorías (`part`):** Organización jerárquica en árbol MPTT (`PartCategory`), control de números de parte internos (`IPN`), revisiones, variantes, plantillas de parámetros técnicos y validación de Listas de Materiales (`BomItem`) con detección de recursividad.
- **Control de Inventario y Ubicaciones (`stock`):** Administración de lotes físicos (`StockItem`), ubicaciones jerárquicas y tipos de almacén (`StockLocation`, `StockLocationType`), serialización individual, conteo físico (*stocktake*), fechas de caducidad (*expiry/stale*), instalación/desinstalación en sub-ensambles y trazabilidad histórica (`StockItemTracking` / `audit`).
- **Gestión de Compañías y Proveedores (`company`):** Registro de proveedores, fabricantes y clientes (`Company`), partes de proveedor (`SupplierPart`), partes de fabricante (`ManufacturerPart`) y escalas de precios por volumen (`SupplierPriceBreak`).
- **Gestión de Órdenes (`order`):** Flujos transaccionales para Órdenes de Compra (`PurchaseOrder`), Órdenes de Venta (`SalesOrder`), Asignaciones de Stock (`SalesOrderAllocation`), Embarques (`SalesOrderShipment`), Órdenes de Devolución (`ReturnOrder`) y Órdenes de Transferencia (`TransferOrder`).
- **Manufactura y Construcción (`build`):** Órdenes de fabricación (`Build`), consumo de componentes de inventario y generación de productos terminados.
- **Seguridad, Usuarios y Plugins (`users`, `plugin`, `common`):** Control de acceso basado en roles y conjuntos de reglas (`RuleSetEnum`), tokens de API revocables/expirables (`ApiToken`), autenticación MFA y motor extensible de plugins.

### 3.2 Problema que Resuelve
En entornos de manufactura electrónica, ensamblaje industrial y distribución técnica, las hojas de cálculo o sistemas ERP genéricos carecen de trazabilidad a nivel de componente individual (número de serie, lote de proveedor, genealogía padre-hijo tras divisiones o fusiones de stock y validación de listas de materiales multinivel). **InvenTree** resuelve la pérdida de trazabilidad, la sobre-asignación de existencias entre órdenes concurrentes y la desincronización entre el inventario físico en bodega y las órdenes de producción/venta.

### 3.3 Tipo de Arquitectura Utilizada
InvenTree implementa una arquitectura **Cliente-Servidor Desacoplada (API-First) con Backend Monolítico Modular y Procesamiento Asíncrono Basado en Eventos**:
- **Capa de Presentación (Cliente SPA / Móvil):** Aplicación React compilada con Vite que consume exclusivamente el API REST mediante JSON/HTTPS, complementada por una aplicación móvil oficial y un cliente SDK en Python.
- **Capa de Aplicación y Dominio (Servidor Web / API):** Monolito modular en Django/DRF servido mediante Gunicorn/Uvicorn detrás de un proxy inverso (Caddy/Nginx), dividido en aplicaciones de dominio desacopladas (`part`, `stock`, `order`, `build`, `company`, `users`, `report`, `plugin`).
- **Capa de Procesamiento Asíncrono (Workers):** Clúster `django-q2` que ejecuta tareas pesadas en segundo plano (despacho masivo de embarques, recálculo de costos BOM, notificaciones, generación de reportes PDF WeasyPrint).
- **Capa de Persistencia y Caché:** Base de datos relacional (PostgreSQL, MySQL/MariaDB o SQLite3) con árboles `django-mptt` y servidor Redis para caché distribuida y cola de mensajes.

```mermaid
flowchart TB
    subgraph Clientes["Capa de Presentación (Clientes)"]
        SPA["Frontend Web SPA<br/>(React 19 + TypeScript + Mantine UI)"]
        SDK["Cliente Python / CLI / Integraciones"]
        MOB["App Móvil (Android / iOS)"]
    end

    subgraph Backend["Servidor de Aplicación InvenTree (Django + DRF)"]
        AUTH["Middleware & Seguridad<br/>(ApiToken, OAuth2, Allauth MFA, RBAC RuleSet)"]
        API["Capa API RESTful (OpenAPI v449)<br/>Serializers + Filters + Validators"]
        subgraph Dominio["Módulos de Dominio (Monolito Modular)"]
            PART["part<br/>(Part, PartCategory, BomItem)"]
            STOCK["stock<br/>(StockItem, StockLocation)"]
            ORDER["order<br/>(PO, SO, Allocation, Shipment)"]
            BUILD["build & company<br/>(Build, Company, SupplierPart)"]
            HELP["InvenTree Core<br/>(helpers, validators, conversion)"]
        end
        WORKER["Worker Asíncrono (Django-Q2)<br/>Embarques, Auditoría, Notificaciones"]
    end

    subgraph Datos["Capa de Datos e Infraestructura"]
        DB[("Base de Datos Relacional<br/>PostgreSQL / MySQL / SQLite3")]
        REDIS[("Redis<br/>Caché & Broker de Cola")]
        MEDIA[("Almacenamiento Estático/Media<br/>Adjuntos, Códigos QR, Reportes")]
    end

    SPA -->|HTTPS JSON| AUTH
    SDK -->|Token Bearer| AUTH
    MOB -->|HTTPS JSON| AUTH
    AUTH --> API
    API --> PART & STOCK & ORDER & BUILD & HELP
    PART & STOCK & ORDER & BUILD --> DB
    ORDER & STOCK -.->|Encola Tareas| REDIS
    REDIS -.-> WORKER
    WORKER --> DB & MEDIA
```

### 3.4 Tecnologías Utilizadas

| Capa / Categoría | Tecnologías y Librerías Específicas en el Repositorio |
| :--- | :--- |
| **Frontend** | React `19.2.7`, TypeScript `6.x`, Vite `7.0.0`, Mantine UI `@mantine/core 9.7.1`, Mantine DataTable `9.2.2`, TanStack React Query `5.101.0`, Zustand `5.0.14`, React Router DOM `6.30.4`, Axios `1.17.0`, DOMPurify `3.4.8`, Lingui `5.9.2` (i18n). |
| **Backend** | Python `3.12+`, Django, Django REST Framework (DRF), `django-allauth` (MFA/SSO), `django-oauth-toolkit`, `django-q2` (cola de tareas), `django-mptt` (árboles jerárquicos), `pint` (conversión de unidades físicas), `py-moneyed` / `django-money`, `nh3` (sanitización HTML en Rust), `Pillow`, `structlog`. |
| **Base de Datos** | PostgreSQL, MySQL, MariaDB, SQLite3 (entorno de pruebas CI y desarrollo local), Redis (caché y broker). |
| **Frameworks de Pruebas y Calidad** | `pytest` / Django `TestCase`, `@playwright/test 1.62.1` (E2E UI/API), Node.js Test Runner (`node:test`), `coverage.py` / Codecov, `ruff` (linter/formatter), `ty` (verificador estático de tipos), `oasdiff` (validación de contratos OpenAPI). |
| **Infraestructura y DevOps** | Docker / Docker Compose, GitHub Actions (11 flujos de trabajo en [`.github/workflows/`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/.github/workflows)), Gunicorn, Invoke (`tasks.py`), Netlify (previsualización UI). |

### 3.5 Alcance Funcional Cubierto por las Pruebas
El alcance de prueba de este caso práctico cubre los componentes críticos del núcleo transaccional y de seguridad de InvenTree:
1. **Módulo de Utilidades y Validadores Transversales ([`InvenTree/helpers.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/helpers.py) y [`InvenTree/validators.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/validators.py)):** Extracción y generación masiva de números de serie (`extract_serial_numbers`), extracción y acotamiento de enteros (`extract_int`), limpieza decimal (`clean_decimal`), prevención de inyección de fórmulas en exportaciones (`escape_export_value`), enmascaramiento de tokens (`sanitize_token`), limpieza de etiquetas HTML (`strip_html_tags`) y validación de unidades físicas/divisas/URLs.
2. **Módulo de Partes y Listas de Materiales ([`part/models.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/part/models.py)):** Categorías estructurales (`PartCategory.clean`), bloqueo de partes (`Part.locked`), validación de revisiones (`validate_revision`) y prevención de ciclos recursivos en listas de materiales (`check_add_to_bom`).
3. **Módulo de Inventario y Lotes ([`stock/models.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/stock/models.py)):** Reglas de integridad de stock (`StockItem.clean`), serialización de lotes (`serializeStock`), desinstalación en ubicaciones (`uninstall_into_location`) y fusión transaccional de lotes (`merge_stock_items`).
4. **Módulo de Órdenes de Venta ([`order/models.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/order/models.py)):** Control de asignaciones de stock y prevención de sobre-asignación (`SalesOrderAllocation.clean`) y validación de cierre de embarques (`SalesOrderShipment.check_can_complete`).
5. **Módulo de Seguridad, Autenticación y Permisos ([`users/authentication.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/users/authentication.py) y [`users/ruleset.py`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/users/ruleset.py)):** Validación de tokens de API (`validate_api_token`), restricción de Basic Auth con MFA activo (`InvenTreeBasicAuthentication`) y matriz RBAC (`RuleSetEnum`).

---

## 4. Requerimientos y Criterios de Calidad

### 4.1 Requisitos Funcionales Relevantes
- **RF01 – Autenticación Segura y Políticas MFA:** El sistema deberá autenticar peticiones mediante tokens de API (`ApiToken`) o credenciales básicas, rechazando tokens inactivos, revocados o expirados, y bloqueando la autenticación por contraseña simple (`BasicAuth`) cuando el usuario tenga MFA habilitado o el sistema exija MFA globalmente (`LOGIN_ENFORCE_MFA`).
- **RF02 – Integridad de Partes, Categorías Estructurales y BOM:** El sistema deberá impedir que se asignen partes a categorías estructurales o que una categoría con partes pase a ser estructural; deberá impedir la edición/eliminación de partes bloqueadas (`locked=True`) y deberá bloquear cualquier referencia circular directa o indirecta en la Lista de Materiales (`BomItem`).
- **RF03 – Generación y Extracción Acotada de Números de Serie:** El sistema deberá permitir extraer y expandir secuencias de números de serie individuales, por rangos (`A-B`) o incrementales (`inicio+cantidad`), exigiendo unicidad, longitud máxima de 100 caracteres y un límite estricto máximo de **1,000 números de serie por operación**.
- **RF04 – Validación de Creación y Movimiento de Lotes de Stock:** El sistema deberá prohibir la creación de lotes de stock (`StockItem`) para partes virtuales (`virtual=True`), exigir cantidades enteras para partes rastreables (`trackable=True`), fijar `quantity = 1` en ítems serializados y bloquear el traslado o desinstalación hacia ubicaciones estructurales (`structural=True`).
- **RF05 – Control de Asignación de Stock en Órdenes de Venta y Embarques:** El sistema deberá validar que la suma de asignaciones activas (`BuildItem` + `SalesOrderAllocation` + `TransferOrderAllocation`) nunca supere la cantidad física disponible del `StockItem` (*over-allocation*), y que un embarque (`SalesOrderShipment`) no pueda completarse sin ítems asignados ni sin verificación previa cuando `SALESORDER_SHIPMENT_REQUIRES_CHECK` esté activo.
- **RF06 – Fusión Transaccional de Lotes de Inventario (`merge_stock_items`):** Cuando dos o más lotes compatibles no serializados se fusionen en un lote principal, el sistema deberá sumar sus cantidades, promediar ponderadamente el precio de compra y **transferir íntegras todas las asignaciones de órdenes de construcción, venta y transferencia** al lote absorbente antes de eliminar el lote secundario.
- **RF07 – Sanitización contra Inyección de Fórmulas (CSV) y Etiquetas HTML (XSS):** El sistema deberá anteponer una comilla simple (`'`) a cualquier cadena exportada que comience con caracteres ejecutables de hoja de cálculo (`=`, `+`, `-`, `@`, `\t`, `\r`) preservando números con signo legítimos, y deberá limpiar o rechazar etiquetas HTML en campos de texto sin afectar texto comercial válido.
- **RF08 – Enmascaramiento Seguro de Tokens Secretos:** El sistema deberá ocultar la sección central de los tokens de API mediante asteriscos (`sanitize_token`), garantizando que en ningún caso —incluyendo valores límite de los parámetros `front` y `back`— se filtre el valor completo del token.
- **RF09 – Conversión y Normalización de Datos Numéricos y Unidades Físicas:** El sistema deberá extraer enteros acotados por `INT_CLIP_MAX` respetando la bandera `allow_negative`, normalizar cadenas decimales con separadores de miles/decimales (`clean_decimal`) y validar unidades físicas contra el registro del Sistema Internacional (`validate_physical_units`).
- **RF10 – Control de Acceso Basado en Roles (RBAC):** El sistema deberá controlar los permisos `view`, `add`, `change` y `delete` sobre los 12 dominios definidos en `RuleSetEnum`.

### 4.2 Requisitos No Funcionales Relevantes
- **RNF01 – Rendimiento y Tiempo de Respuesta API:** Los endpoints principales del API REST (`/api/part/`, `/api/stock/`, `/api/order/so/`, `/api/search/`, `/api/user/token/`) deberán responder en **menos de 3 segundos (3,000 ms)** bajo carga concurrente de 20 peticiones simultáneas, con una meta óptima interna de percentil 95 (`p95`) inferior a **200 ms** en consultas indexadas y una tasa de error HTTP del **0%**.
- **RNF02 – Fiabilidad y Atomicidad Transaccional:** Todas las operaciones mutables sobre inventario (`serializeStock`, `merge_stock_items`, `allocateToCustomer`, `complete_allocations`) deberán ejecutarse dentro de bloques `transaction.atomic()` utilizando bloqueos de fila `select_for_update()` en orden determinista de clave primaria para evitar condiciones de carrera y *deadlocks*.
- **RNF03 – Seguridad de la Información (OWASP Top 10):** El sistema deberá proteger las credenciales de sesión y tokens de API mediante hash criptográfico con *pepper* (`SECRET_KEY`), mitigar ataques XSS y CSV Formula Injection, y cumplir los controles descritos en el modelo de amenazas oficial ([`threat_model.md`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/docs/docs/concepts/threat_model.md)).
- **RNF04 – Usabilidad y Claridad Diagnóstica:** Todos los errores de validación de negocio y configuración deberán retornar mensajes descriptivos, internacionalizables (`gettext_lazy`) y con códigos de diagnóstico estandarizados (ej. `INVE-E17`, `INVE-W20`) sin errores tipográficos ni ambigüedades.
- **RNF05 – Mantenibilidad y Automatización en CI/CD:** Los scripts de prueba deberán ser modulares, repetibles, independientes del estado previo y capaces de exportar reportes estructurados (JSON y JUnit XML) ejecutables en menos de **5 segundos** dentro de un pipeline CI/CD.

### 4.3 Criterios de Aceptación

| ID Requisito | Criterio de Aceptación Verificable (Dado / Cuando / Entonces) |
| :--- | :--- |
| **RF01 / RNF03** | **Dado** un usuario con MFA activo o un token revocado/expirado, **cuando** intenta autenticarse vía Basic Auth o `ApiTokenAuthentication`, **entonces** el sistema rechaza el acceso con `AuthenticationFailed` (`HTTP 401`) y mensaje `INVE-W20` o razón específica del token. |
| **RF02** | **Dada** una parte con `locked=True` o una relación BOM circular (`A -> A` o mismo `tree_id`), **cuando** se invoca `delete()`, `check_parameter_save()` o `check_add_to_bom()`, **entonces** se lanza `ValidationError` abortando la operación. |
| **RF03** | **Dada** una solicitud de extracción de números de serie en `extract_serial_numbers()`, **cuando** `expected_quantity <= 1000` y los seriales son únicos y `<= 100` caracteres, **entonces** retorna la lista expandida; **cuando** `expected_quantity >= 1001`, **entonces** lanza `ValidationError("Cannot serialize more than 1000 items at once")`. |
| **RF04 / RF05** | **Dado** un `StockItem` con `quantity = 100` y `80` unidades ya reservadas entre órdenes de construcción, venta y transferencia, **cuando** se crea una `SalesOrderAllocation` por `20` unidades, **entonces** se aprueba; **cuando** se solicita por `21` unidades, **entonces** falla con `"Stock item is over-allocated"`. |
| **RF06 / RNF02** | **Dados** dos lotes `StockItem` compatibles donde el lote secundario posee asignaciones `SalesOrderAllocation` y `TransferOrderAllocation`, **cuando** se ejecuta `merge_stock_items()`, **entonces** el lote principal conserva el 100% de las asignaciones activas sin pérdida de registros por cascada. |
| **RF07 / RF08** | **Dado** un valor exportado que inicia con `=`, `+`, `-`, `@` no numérico, **cuando** pasa por `escape_export_value()`, **entonces** se prefija con `'`; y **dado** un token pasado a `sanitize_token(token, front, back)` con cualquier `back >= 0`, **entonces** jamás expone el token completo en texto plano. |
| **RNF01** | **Dada** una carga concurrente de 20 hilos y 540 peticiones sobre los 5 endpoints críticos del API, **cuando** finaliza el benchmark, **entonces** el 100% de los endpoints registra un tiempo de respuesta `< 3,000 ms` y `0%` de respuestas fallidas (`HTTP 5xx/4xx`). |

### 4.4 Atributos de Calidad Analizados (Modelo ISO/IEC 25010)
1. **Funcionalidad (Adecuación y Exactitud Funcional):** Se evalúa la exactitud de los algoritmos de validación de inventario, cálculo de cantidades disponibles (`unallocated_quantity`), expansión de rangos de números de serie y reglas de transición de órdenes.
2. **Usabilidad (Reconocibilidad de Adecuación y Protección contra Errores de Usuario):** Se analiza la precisión de los mensajes de error por campo en `ValidationError`, las advertencias de configuración (`invalid_site_url_hint`) y las guardas que impiden acciones destructivas accidentales (borrado de partes activas/bloqueadas o ítems serializados).
3. **Fiabilidad (Madurez, Tolerancia a Fallos y Recuperabilidad):** Se inspecciona el aislamiento transaccional (`@transaction.atomic`), el ordenamiento de bloqueos en base de datos (`sorted(..., key=lambda item: item.pk)` con `select_for_update()`) y la integridad referencial en operaciones compuestas como la fusión y división de stock.
4. **Rendimiento (Comportamiento Temporal y Capacidad):** Se mide la latencia promedio, mediana (`p50`), percentiles `p90`, `p95`, `p99` y rendimiento en peticiones por segundo (`RPS`) sobre los endpoints de consulta y búsqueda global, identificando cuellos de botella de agregación.
5. **Seguridad (Confidencialidad, Integridad, No Repudio y Autenticidad):** Se evalúa la protección de tokens (`ApiToken`), imposición de MFA, resistencia contra inyección CSV y XSS (`nh3`), funciones hash en códigos de barras y trazabilidad inmutable de eventos en el log de auditoría (`audit`).
6. **Mantenibilidad (Modularidad, Analizabilidad y Capacidad de ser Probado):** Se analiza el desacoplamiento por dominios de Django, el uso de mixins reutilizables (`InvenTreeAuditMixin`, `PluginValidationMixin`) y la facilidad para ejecutar suites automatizadas deterministas.

---

## 5. Plan de Pruebas (Estructurado bajo Lineamientos IEEE 829 / ISO/IEC/IEEE 29119-3)

### 5.1 Identificador y Objetivos de Prueba
- **Identificador del Plan:** `TP-INVENTREE-ACS-2026-V1`
- **Objetivos de Prueba:**
  1. Verificar el cumplimiento de los requisitos funcionales (`RF01` a `RF10`) y no funcionales (`RNF01` a `RNF05`) en el código fuente real de InvenTree `v1.7.0`.
  2. Diseñar y ejecutar al menos **10 casos de prueba manuales** (se diseñaron y ejecutaron **12 casos**) y al menos **5 casos de prueba automatizados** (se implementaron y ejecutaron **8 casos en la suite principal + 5 especificaciones E2E Playwright y 7 pruebas Pytest**), aplicando técnicas formales de caja negra y caja blanca.
  3. Detectar, documentar, clasificar y gestionar defectos reales presentes en el repositorio mediante evidencia reproducible a nivel de línea de código.
  4. Evaluar el comportamiento temporal del API bajo concurrencia y analizar la postura de seguridad del sistema frente a OWASP Top 10.

### 5.2 Alcance del Plan de Pruebas
- **Dentro del Alcance (*In-Scope*):**
  - Pruebas unitarias, de integración y de sistema sobre los módulos `InvenTree.helpers`, `InvenTree.validators`, `part`, `stock`, `order` y `users`.
  - Pruebas de rendimiento y carga concurrente sobre los endpoints REST `/api/part/`, `/api/stock/`, `/api/order/so/`, `/api/search/` y `/api/user/token/`.
  - Evaluación de seguridad basada en OWASP Top 10 (2021) y revisión contra el modelo de amenazas del proyecto.
- **Fuera del Alcance (*Out-of-Scope*):**
  - Ejecución de servidores externos de análisis SonarQube y escaneo activo con OWASP ZAP *(excluidos explícitamente de acuerdo con los lineamientos del encargo)*.
  - Pruebas sobre la aplicación móvil nativa en Flutter (Play Store / App Store) y plugins de terceros fuera del repositorio central.

### 5.3 Tipos y Niveles de Prueba
1. **Pruebas Unitarias:** Verificación aislada de funciones puras y validadores (`extract_int`, `extract_serial_numbers`, `clean_decimal`, `escape_export_value`, `sanitize_token`, `strip_html_tags`, `validate_physical_units`, `invalid_site_url_hint`).
2. **Pruebas de Integración:** Verificación de la interacción entre modelos relacionales y reglas de dominio acopladas (`Part` ↔ `BomItem`, `StockItem` ↔ `SalesOrderAllocation` ↔ `TransferOrderAllocation` durante `merge_stock_items()`, y `ApiToken` ↔ `User` ↔ `MFA`).
3. **Pruebas de Sistema (API & Rendimiento):** Evaluación integral de los endpoints RESTful bajo carga concurrente y validación de contratos de entrada/salida.
4. **Pruebas de Aceptación:** Contraste directo de los resultados obtenidos contra los criterios de aceptación definidos en la Sección 4.3 para validar las reglas críticas del negocio logístico.

### 5.4 Estrategias Utilizadas y Justificación
- **Estrategia Funcional (Caja Negra y Caja Blanca):** Combina el diseño basado en especificaciones (requisitos y docstrings) con la inspección estructural del código fuente de Django para verificar todas las ramas condicionales y manejadores de excepciones.
- **Estrategia No Funcional (Rendimiento, Concurrencia y Seguridad):** Evalúa tiempos de respuesta por percentiles (`p50`, `p90`, `p95`, `p99`), estabilidad sin errores bajo ráfagas de 20 conexiones concurrentes y resistencia ante entradas maliciosas (payloads XSS, fórmulas CSV y manipulación de parámetros).
- **Estrategia Exploratoria Basada en Riesgos:** Focalizada en operaciones destructivas o de alta complejidad algorítmica (fusión de lotes con claves foráneas en cascada y operadores de slicing negativo en Python), lo que permitió descubrir defectos críticos no cubiertos por la suite original del proyecto.
- **Estrategia de Automatización Determinista:** Implementación de scripts autocontenidos en la carpeta [`ACS final test/`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/ACS%20final%20test) que se ejecutan en milisegundos, generan logs verificables y exportan reportes estándar JSON y JUnit XML.

### 5.5 Técnicas de Diseño Aplicadas y Justificación Técnica
1. **Partición de Equivalencia (EP):** Divide el dominio de entrada en clases válidas e inválidas (ej. formatos de rangos de serie `SN001-SN005` vs. duplicados; fórmulas CSV que inician con `=`, `+`, `-`, `@` vs. números negativos reales `-222` o científicos `-12e6`; unidades SI válidas en Pint vs. unidades inexistentes). Reduce la explosión combinatoria garantizando máxima cobertura semántica.
2. **Análisis de Valores Límite (BVA):** Evalúa el comportamiento en los bordes exactos de las restricciones del sistema, donde se concentra la mayor densidad de defectos:
   - Cantidad de números de serie a generar: fronteras `0` (inválido), `1` (mínimo válido), `1000` (máximo válido) y `1001` (inválido).
   - Asignación disponible de stock (`stock = 100`, `ocupado = 80`): fronteras `0` (inválido), `20` (máximo disponible exacto) y `21` (sobre-asignación).
   - Enmascaramiento de tokens en `sanitize_token(token, front=8, back=0)`: frontera `back = 0`, la cual reveló el defecto crítico de seguridad **DEF-02** (`token_value[-0:]`).
   - Acotamiento de enteros en `extract_int(ref, clip=100, allow_negative=False)`: frontera inferior `< -clip` (`-500`), la cual reveló el defecto **DEF-03**.
3. **Tablas de Decisión:** Modelan reglas de negocio multicondicionales donde el resultado depende de la combinación booleana de varias entradas (ej. `BASIC_AUTH_ENABLED` × `is_mfa_enabled(user)` × `mfa_enforced()`; o `shipment_date` × `allocations.count()` × `SALESORDER_SHIPMENT_REQUIRES_CHECK` × `is_checked()`).
4. **Transición de Estados:** Valida los cambios de estado permitidos y prohibidos en objetos del ciclo de vida del inventario (ej. `Part` activa $\rightarrow$ inactiva $\rightarrow$ bloqueada `locked=True` $\rightarrow$ intento de edición/eliminación; o `StockItem` en bodega $\rightarrow$ asignado $\rightarrow$ fusionado / embarcado).

### 5.6 Recursos

#### 5.6.1 Recursos Humanos y Distribución de Responsabilidades
Las actividades del Plan de Pruebas se distribuyeron equitativamente entre los tres integrantes del equipo:

| Integrante | Rol en el Equipo de QA | Módulos y Tareas Asignadas | Casos Manuales | Casos Automatizados |
| :--- | :--- | :--- | :--- | :--- |
| **Emanuel Ortiz** | **Líder de QA, Automatización Backend y Pruebas de Rendimiento** | Liderazgo del plan IEEE 829, pruebas del módulo `stock` (`StockItem`, serialización, `merge_stock_items`), utilidades numéricas (`extract_int`, `clean_decimal`), ejecución del benchmark de carga (`RNF01`) y análisis de métricas KPI. | `CP-MAN-05`<br/>`CP-MAN-06`<br/>`CP-MAN-07`<br/>`CP-MAN-09` | `CP-AUT-01`<br/>`CP-AUT-04`<br/>`CP-AUT-07`<br/>+ Benchmark `PERF-01..05` |
| **Manuela Sánchez** | **Analista QA Funcional, Diseño de Casos (EP/BVA) y Gestión de Defectos** | Levantamiento de requerimientos y criterios de aceptación, pruebas de los módulos `part` (`Part`, `PartCategory`, `BomItem`) y `order` (`SalesOrderAllocation`, `SalesOrderShipment`), aplicación de tablas de decisión y administración de la matriz de defectos (`DEF-01` a `DEF-06`). | `CP-MAN-02`<br/>`CP-MAN-03`<br/>`CP-MAN-04`<br/>`CP-MAN-08` | `CP-AUT-02`<br/>`CP-AUT-03`<br/>+ Suite Pytest/Playwright |
| **Juan Torres** | **Ingeniero de Automatización E2E/API, Integración CI/CD y Seguridad** | Pruebas del módulo `users` (`authentication.py`, `ApiToken`, MFA y `RuleSetEnum`), sanitización de seguridad (`escape_export_value`, `sanitize_token`, `strip_html_tags`), evaluación OWASP Top 10, integración con pipeline CI/CD y consolidación de anexos. | `CP-MAN-01`<br/>`CP-MAN-10`<br/>`CP-MAN-11`<br/>`CP-MAN-12` | `CP-AUT-05`<br/>`CP-AUT-06`<br/>`CP-AUT-08`<br/>+ Checks OWASP |

#### 5.6.2 Herramientas Utilizadas
- **Ejecución y Automatización:** Node.js Test & Verification Engine (`v24.19.0`), Pytest (`test_inventree_pytest.py`), Playwright TypeScript (`pui_acs_inventree.spec.ts`).
- **Rendimiento y Carga:** Motor asíncrono de carga concurrente con medición de alta resolución `node:perf_hooks` (`performance_load_test.mjs`).
- **Control de Versiones y CI/CD:** Git (`2.x`), GitHub Actions ([`.github/workflows/qc_checks.yaml`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/.github/workflows/qc_checks.yaml)).
- **Gestión de Defectos y Reportes:** GitHub Issues / Matriz CSV estructurada (`defect_report_matrix.csv`), reportes JSON y JUnit XML (`junit_report.xml`).

#### 5.6.3 Ambiente de Pruebas
- **Sistema Operativo:** Windows 10/11 Pro x64 (`win32`).
- **Entorno de Ejecución:** Node.js `v24.19.0`, npm `11.17.0`, Python `3.12` (configuración objetivo en `pyproject.toml`).
- **Base de Datos de Prueba:** Motor relacional en memoria / SQLite3 con dataset sintético representativo (1,200 partes, 3,000 lotes de stock, 600 órdenes de venta, 40 ubicaciones).

### 5.7 Cronograma de Actividades

| Fase | Actividad del Plan de Pruebas | Responsable(s) | Fecha Inicio | Fecha Fin | Estado |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **Fase 1** | Selección del sistema InvenTree, clonación del repositorio y análisis arquitectónico | Emanuel Ortiz, Manuela Sánchez, Juan Torres | 2026-11-01 | 2026-11-03 | Completado |
| **Fase 2** | Definición de Requisitos (`RF01–RF10`, `RNF01–RNF05`), Criterios de Aceptación e ISO 25010 | Manuela Sánchez | 2026-11-04 | 2026-11-06 | Completado |
| **Fase 3** | Estructuración del Plan de Pruebas IEEE/ISO y diseño de matrices EP, BVA y Tablas de Decisión | Emanuel Ortiz, Manuela Sánchez | 2026-11-07 | 2026-11-09 | Completado |
| **Fase 4** | Diseño y ejecución de Casos Manuales (`CP-MAN-05, 06, 07, 09`) sobre módulo `stock` y `helpers` | Emanuel Ortiz | 2026-11-10 | 2026-11-12 | Completado |
| **Fase 4** | Diseño y ejecución de Casos Manuales (`CP-MAN-02, 03, 04, 08`) sobre módulos `part` y `order` | Manuela Sánchez | 2026-11-10 | 2026-11-12 | Completado |
| **Fase 4** | Diseño y ejecución de Casos Manuales (`CP-MAN-01, 10, 11, 12`) sobre `users` y `validators` | Juan Torres | 2026-11-10 | 2026-11-12 | Completado |
| **Fase 5** | Desarrollo y ejecución de la Suite Automatizada (`CP-AUT-01` a `CP-AUT-08`) en `ACS final test/` | Emanuel Ortiz, Manuela Sánchez, Juan Torres | 2026-11-13 | 2026-11-15 | Completado |
| **Fase 6** | Ejecución de Pruebas de Rendimiento y Carga Concurrente (`PERF-01` a `PERF-05`) | Emanuel Ortiz | 2026-11-16 | 2026-11-17 | Completado |
| **Fase 7** | Evaluación de Seguridad OWASP Top 10 y análisis de integración CI/CD | Juan Torres | 2026-11-17 | 2026-11-18 | Completado |
| **Fase 8** | Registro, clasificación y análisis de ciclo de vida de defectos (`DEF-01` a `DEF-06`) | Manuela Sánchez, Emanuel Ortiz | 2026-11-19 | 2026-11-20 | Completado |
| **Fase 9** | Cálculo de KPIs de calidad, reflexión crítica y consolidación del informe final | Emanuel Ortiz, Manuela Sánchez, Juan Torres | 2026-11-21 | 2026-11-22 | Completado |

---

## 6. Diseño de Casos de Prueba

### 6.1 Aplicación de Técnicas Obligatorias de Diseño

#### A. Matriz de Partición de Equivalencia (EP) y Valores Límite (BVA)
| Función / Modelo Bajo Prueba | Parámetro / Campo | Partición Inválida Inferior (BVA) | Partición Válida (EP + Fronteras BVA) | Partición Inválida Superior / Especial (BVA) | Caso Asociado |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `extract_serial_numbers()` | `expected_quantity` | `0`, `-1`, `"abc"` (No numérico) | Mínimo=`1`, Nominal=`5`, **Máximo=`1000`** | **`1001`** (`> 1000` lanza `ValidationError`) | `CP-MAN-05`<br/>`CP-AUT-01` |
| `extract_serial_numbers()` | `serial` (longitud y unicidad) | `""` (Cadena vacía) | `1` a **`100` caracteres**, únicos (`SN001-SN005`) | **`101` caracteres** (`> 100`), o serial repetido (`SN1, SN1`) | `CP-AUT-01` |
| `SalesOrderAllocation.clean()` | `quantity` (con stock=`100`, reservado=`80`) | **`0`**, `-5` (`<= 0`) | Mínimo=`1`, Nominal=`10`, **Máximo disponible=`20`** | **`21`** (`80 + 21 = 101 > 100` $\rightarrow$ *over-allocated*) | `CP-AUT-03` |
| `sanitize_token()` | `back` (con `front=8`, `len=40`) | N/A | Nominal `back=12`, Frontera `back=1` | **Frontera `back=0`** (Evalúa `token[-0:]` $\rightarrow$ **DEF-02**) | `CP-AUT-06` |
| `extract_int()` | `reference` (con `clip=100`, `allow_negative=False`) | **`"-500"`** (`< -clip` $\rightarrow$ **DEF-03**), `"-101"` | `"-100"` a `"-1"` (convierte a positivo), `"0"` a **`"100"`** | **`"101"`**, `"9999"` (recorta a `+100`) | `CP-AUT-07` |
| `escape_export_value()` | `value` (cadena exportada a CSV/Excel) | N/A | Texto normal (`"Resistor"`), Números con signo (`"-222"`, `"+1.5"`, `"-12e6"`) | Fórmulas ejecutables: `"=1+1"`, `"=CMD()"`, `"@SUM()"`, `"+HYPERLINK()"` | `CP-AUT-05` |

#### B. Tabla de Decisión: Autenticación y Validación de Embarques
| Regla # | Condición 1: `BASIC_AUTH_ENABLED` | Condición 2: `is_mfa_enabled(user)` | Condición 3: `mfa_enforced()` | Acción Esperada en `InvenTreeBasicAuthentication` | Caso Asociado |
| :---: | :---: | :---: | :---: | :--- | :---: |
| **R1** | `False` | Cualquiera | Cualquiera | Retorna `None` (No autentica por Basic Auth) | `CP-AUT-08` |
| **R2** | `True` | `False` | `False` | **Permite** autenticación con usuario y contraseña | `CP-MAN-01` |
| **R3** | `True` | `True` | `False` | **Bloquea** con `AuthenticationFailed("INVE-W20: Password authentication not allowed due to MFA")` | `CP-MAN-01` |
| **R4** | `True` | `False` | `True` | **Bloquea** con `AuthenticationFailed("INVE-W20: Password authentication not allowed due to MFA")` | `CP-MAN-01` |

---

### 6.2 Casos de Prueba Manuales (12 Casos Documentados)

#### Caso Manual 01 (`CP-MAN-01`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-01` |
| **Nombre del caso** | Rechazo de autenticación HTTP Basic Auth cuando el usuario tiene MFA habilitado |
| **Responsable** | **Juan Torres** |
| **Objetivo** | Verificar que [`InvenTreeBasicAuthentication.authenticate_credentials`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/users/authentication.py#L51-L60) impida el inicio de sesión con solo contraseña si el usuario posee MFA activo. |
| **Requisito asociado** | `RF01`, `RNF03` (Técnica: **Tabla de Decisión**) |
| **Precondiciones** | Configuración `BASIC_AUTH_ENABLED = True`; usuario `jtorres` activo con dispositivo TOTP MFA registrado (`is_mfa_enabled(user) == True`). |
| **Datos de entrada** | Cabecera `Authorization: Basic anRvcnJlczpTZWN1cmVQYXNzMTIzIQ==` en petición `GET /api/part/`. |
| **Pasos de ejecución** | 1. Habilitar TOTP MFA en la cuenta `jtorres`.<br/>2. Enviar petición `GET /api/part/` con cabecera Basic Auth.<br/>3. Evaluar el retorno de `password_auth_allowed(user)` en `users/authentication.py:L24-L28`. |
| **Resultado esperado** | Se rechaza la petición con `HTTP 401 Unauthorized` y detalle `"INVE-W20: Password authentication not allowed due to MFA"`. |
| **Resultado obtenido** | `password_auth_allowed(user)` retorna `False` en la línea 27 y la línea 56 lanza `AuthenticationFailed('INVE-W20: Password authentication not allowed due to MFA')`. |
| **Estado** | **Aprobado** |

#### Caso Manual 02 (`CP-MAN-02`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-02` |
| **Nombre del caso** | Protección de inmutabilidad en Parte bloqueada (`Part.locked = True`) ante edición de parámetros y borrado |
| **Responsable** | **Manuela Sánchez** |
| **Objetivo** | Comprobar que una parte bloqueada no permita modificar/eliminar sus parámetros técnicos ni ser eliminada de la base de datos. |
| **Requisito asociado** | `RF02` (Técnica: **Transición de Estados**) |
| **Precondiciones** | Ajuste global `PART_ENABLE_LOCKING = True`; instancia `Part(pk=104, name="PCB Controlador V2", locked=True, active=False)`. |
| **Datos de entrada** | Operación 1: `part.check_parameter_save(param)` | Operación 2: `part.delete()`. |
| **Pasos de ejecución** | 1. Instanciar la parte `pk=104` en estado `locked=True`.<br/>2. Invocar `check_parameter_save()` ([`part/models.py#L592-L596`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/part/models.py#L592-L596)).<br/>3. Invocar `delete()` ([`part/models.py#L597-L607`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/part/models.py#L597-L607)). |
| **Resultado esperado** | Ambas operaciones lanzan `ValidationError`: `"Cannot modify parameters of a locked part"` y `"Cannot delete this part as it is locked"`. |
| **Resultado obtenido** | Ambas validaciones interceptan `self.locked and get_global_setting('PART_ENABLE_LOCKING')` y lanzan `ValidationError` impidiendo cualquier cambio. |
| **Estado** | **Aprobado** |

#### Caso Manual 03 (`CP-MAN-03`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-03` |
| **Nombre del caso** | Prevención de referencias circulares directas y por árbol de variantes en Lista de Materiales (`BOM`) |
| **Responsable** | **Manuela Sánchez** |
| **Objetivo** | Validar que [`Part.check_add_to_bom()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/part/models.py#L682-L742) rechace agregar una parte como componente de sí misma o de otra parte perteneciente al mismo árbol de variantes (`tree_id`). |
| **Requisito asociado** | `RF02` (Técnica: **Partición de Equivalencia**) |
| **Precondiciones** | `Part A` (`pk=10, tree_id=5, assembly=True`) y `Part B` (`pk=11, variant_of=10, tree_id=5`). |
| **Datos de entrada** | Intento 1: `parent=Part(10), sub_part=Part(10)` | Intento 2: `parent=Part(10), sub_part=Part(11)`. |
| **Pasos de ejecución** | 1. Ejecutar `Part(10).check_add_to_bom(Part(10), raise_error=True)`.<br/>2. Ejecutar `Part(11).check_add_to_bom(Part(10), raise_error=True)`. |
| **Resultado esperado** | Se lanza `ValidationError` en ambos intentos con el mensaje `"Part '...' cannot be used in BOM for '...' (recursive)"`. |
| **Resultado obtenido** | La línea 695 detecta `self.pk == parent.pk` y la línea 709 detecta igualdad de `tree_id`, lanzando `ValidationError` en ambos casos. |
| **Estado** | **Aprobado** |

#### Caso Manual 04 (`CP-MAN-04`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-04` |
| **Nombre del caso** | Restricción de conversión a categoría estructural cuando existen partes asignadas |
| **Responsable** | **Manuela Sánchez** |
| **Objetivo** | Verificar que [`PartCategory.clean()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/part/models.py#L174-L186) impida activar el atributo `structural=True` en una categoría que ya contiene partes directas. |
| **Requisito asociado** | `RF02` (Técnica: **Tabla de Decisión**) |
| **Precondiciones** | Categoría `"Sensores Industriales"` (`pk=4, structural=False`) con `partcount(False, False) == 3`. |
| **Datos de entrada** | `PATCH /api/part/category/4/` con payload `{"structural": true}`. |
| **Pasos de ejecución** | 1. Confirmar que la categoría `pk=4` tiene 3 partes asociadas directamente.<br/>2. Asignar `category.structural = True` e invocar `category.clean()`. |
| **Resultado esperado** | Se rechaza la modificación con `ValidationError("You cannot make this part category structural because some parts are already assigned to it!")`. |
| **Resultado obtenido** | La guarda en `part/models.py:L179` evalúa `self.pk and self.structural and self.partcount(False, False) > 0` como verdadera y lanza `ValidationError`. |
| **Estado** | **Aprobado** |

#### Caso Manual 05 (`CP-MAN-05`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-05` |
| **Nombre del caso** | Serialización de lotes de Stock en valores límite (`quantity = 0, 1, 1000, 1001`) |
| **Responsable** | **Emanuel Ortiz** |
| **Objetivo** | Validar las fronteras inferior y superior en [`StockItem.serializeStock()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/stock/models.py#L2491-L2601) y [`extract_serial_numbers()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/helpers.py#L617-L650). |
| **Requisito asociado** | `RF03` (Técnica: **Análisis de Valores Límite - BVA**) |
| **Precondiciones** | Parte con `trackable=True`; lote `StockItem` con `quantity=1500` unidades sin serializar. |
| **Datos de entrada** | Frontera 1: `qty=0` | Frontera 2: `qty=1, serial="SN0001"` | Frontera 3: `qty=1000, serial="1+"` | Frontera 4: `qty=1001, serial="1+"`. |
| **Pasos de ejecución** | 1. Ejecutar con `qty=0`.<br/>2. Ejecutar con `qty=1` y `qty=1000`.<br/>3. Ejecutar con `qty=1001`. |
| **Resultado esperado** | `qty=0` falla con `"Quantity must be greater than zero"`; `qty=1` y `qty=1000` tienen éxito; `qty=1001` falla con `"Cannot serialize more than 1000 items at once"`. |
| **Resultado obtenido** | Las cuatro fronteras responden exactamente conforme a las validaciones de `stock/models.py:L2528` y `helpers.py:L647`. |
| **Estado** | **Aprobado** |

#### Caso Manual 06 (`CP-MAN-06`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-06` |
| **Nombre del caso** | Bloqueo de desinstalación de `StockItem` hacia una ubicación de almacén estructural |
| **Responsable** | **Emanuel Ortiz** |
| **Objetivo** | Comprobar que [`StockItem.uninstall_into_location()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/stock/models.py#L1997-L2036) rechace mover un componente desinstalado hacia un `StockLocation` con `structural=True`. |
| **Requisito asociado** | `RF04` (Técnica: **Partición de Equivalencia**) |
| **Precondiciones** | `StockItem(pk=88, belongs_to=StockItem(50))` instalado en ensamble; ubicación destino `StockLocation(pk=12, structural=True)`. |
| **Datos de entrada** | `location = StockLocation(pk=12, structural=True)`, `notes = "Desmonte por mantenimiento"`. |
| **Pasos de ejecución** | 1. Tomar el ítem instalado `pk=88`.<br/>2. Llamar a `uninstall_into_location(location=StockLocation(12), user=admin, notes="...")`. |
| **Resultado esperado** | Lanza `ValidationError({'location': 'Cannot assign stock to structural location'})` sin modificar `belongs_to`. |
| **Resultado obtenido** | La línea 2009 de `stock/models.py` detecta `location and location.structural` y lanza `ValidationError`, manteniendo intacta la relación del ítem. |
| **Estado** | **Aprobado** |

#### Caso Manual 07 (`CP-MAN-07`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-07` |
| **Nombre del caso** | Fusión de lotes de Stock (`merge_stock_items`) con asignaciones activas de Órdenes de Venta y Transferencia |
| **Responsable** | **Emanuel Ortiz** |
| **Objetivo** | Verificar que al fusionar dos lotes compatibles mediante [`StockItem.merge_stock_items()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/stock/models.py#L2781-L2875), las asignaciones de órdenes de venta (`SalesOrderAllocation`) y transferencia (`TransferOrderAllocation`) del lote absorbido se preserven y reasignen al lote principal. |
| **Requisito asociado** | `RF06`, `RNF02` (Técnica: **Transición de Estados / Integración**) |
| **Precondiciones** | `StockItem A (pk=201, qty=50)` y `StockItem B (pk=202, qty=30)` de la misma parte no serializada. `StockItem B` tiene asociada `SalesOrderAllocation(pk=501, item_id=202, qty=10)` y `TransferOrderAllocation(pk=601, item_id=202, qty=5)`. |
| **Datos de entrada** | `item_a.merge_stock_items([item_b], user=admin)`. |
| **Pasos de ejecución** | 1. Confirmar que `item_a.can_merge(item_b)` retorna `True` (ninguno tiene `sales_order` directo, sino registros de asignación).<br/>2. Ejecutar `item_a.merge_stock_items([item_b])`.<br/>3. Inspeccionar las líneas 2864–2874 de `stock/models.py` y el estado de `SalesOrderAllocation(501)` y `TransferOrderAllocation(601)` tras `other.delete()`. |
| **Resultado esperado** | `StockItem A` actualiza su cantidad a `80` y tanto `SalesOrderAllocation(501)` como `TransferOrderAllocation(601)` actualizan su llave foránea `item` a `201`. |
| **Resultado obtenido** | **FALLO CRÍTICO (`DEF-01`):** En `stock/models.py:L2866` se ejecuta `allocation.stock_item = self`, pero en `SalesOrderAllocation` ([`order/models.py#L3336`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/order/models.py#L3336)) el campo ForeignKey se llama **`item`** (no `stock_item`). Al ejecutarse `other.delete()` en la línea 2874 con `on_delete=models.CASCADE`, todas las asignaciones `SalesOrderAllocation` y `TransferOrderAllocation` del lote fusionado **se eliminan silenciosamente por cascada**. |
| **Estado** | **Fallido** *(Defecto `DEF-01` reportado)* |

#### Caso Manual 08 (`CP-MAN-08`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-08` |
| **Nombre del caso** | Validación de requisitos previos para completar embarque de Orden de Venta (`SalesOrderShipment.check_can_complete`) |
| **Responsable** | **Manuela Sánchez** |
| **Objetivo** | Comprobar que [`SalesOrderShipment.check_can_complete()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/order/models.py#L2950-L2978) bloquee el despacho cuando el embarque ya fue enviado, no tiene asignaciones o no ha sido verificado (`is_checked() == False`). |
| **Requisito asociado** | `RF05` (Técnica: **Tabla de Decisión**) |
| **Precondiciones** | Ajuste global `SALESORDER_SHIPMENT_REQUIRES_CHECK = True`; embarque `SO-SHIP-09` con 2 ítems asignados y `checked_by = None`. |
| **Datos de entrada** | Invocación de `shipment.check_can_complete(raise_error=True)`. |
| **Pasos de ejecución** | 1. Invocar `check_can_complete()` sobre embarque sin ítems (`allocations.count() == 0`).<br/>2. Asignar 2 ítems dejando `checked_by = None` e invocar `check_can_complete()`.<br/>3. Marcar `checked_by = user` e invocar nuevamente. |
| **Resultado esperado** | Paso 1 falla con `"Shipment has no allocated stock items"`; Paso 2 falla con `"Shipment must be checked before it can be completed"`; Paso 3 retorna `True`. |
| **Resultado obtenido** | Las tres condiciones de la tabla de decisión en `order/models.py:L2957-L2978` responden exactamente según lo esperado. |
| **Estado** | **Aprobado** |

#### Caso Manual 09 (`CP-MAN-09`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-09` |
| **Nombre del caso** | Normalización de cadenas decimales con múltiples separadores de miles (`clean_decimal`) |
| **Responsable** | **Emanuel Ortiz** |
| **Objetivo** | Verificar que [`InvenTree.helpers.clean_decimal()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/helpers.py#L901-L938) convierta correctamente cadenas numéricas con formato internacional y múltiples separadores de miles. |
| **Requisito asociado** | `RF09` (Técnica: **Partición de Equivalencia**) |
| **Precondiciones** | Función `clean_decimal(number)` disponible en `InvenTree/helpers.py`. |
| **Datos de entrada** | Entrada A: `"1.250,50"` | Entrada B: `"1,250.50"` | Entrada C: `"1,234,567"` (dos comas separadoras de miles, sin decimales). |
| **Pasos de ejecución** | 1. Ejecutar `clean_decimal("1.250,50")` y `clean_decimal("1,250.50")`.<br/>2. Ejecutar `clean_decimal("1,234,567")` y trazar las líneas 911–932 de `helpers.py`. |
| **Resultado esperado** | Entradas A y B retornan `Decimal("1250.5")`; Entrada C retorna `Decimal("1234567")`. |
| **Resultado obtenido** | **FALLO (`DEF-04`):** Las Entradas A y B retornan `Decimal("1250.5")`, pero en la Entrada C (`"1,234,567"`) `count_comma` es `2` y `count_point` es `0`. Como el código solo evalúa `if count_comma == 1:` y `elif count_point == 1:`, no se eliminan las comas, `Decimal("1,234,567")` lanza `InvalidOperation` y la línea 932 **retorna silenciosamente `Decimal(0)`**. |
| **Estado** | **Fallido** *(Defecto `DEF-04` reportado)* |

#### Caso Manual 10 (`CP-MAN-10`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-10` |
| **Nombre del caso** | Sanitización de etiquetas HTML y manejo de entidades comerciales en [`strip_html_tags()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/helpers.py#L941-L961) |
| **Responsable** | **Juan Torres** |
| **Objetivo** | Comprobar que `strip_html_tags(value, raise_error=True)` bloquee etiquetas HTML maliciosas sin rechazar texto legítimo que contenga entidades escapadas como `&amp;`. |
| **Requisito asociado** | `RF07`, `RNF03` (Técnica: **Partición de Equivalencia + Valores Límite**) |
| **Precondiciones** | Librería `nh3` activa en `InvenTree.helpers.strip_html_tags`. |
| **Datos de entrada** | Entrada 1: `"<script>alert(1)</script>Resistor"` | Entrada 2: `"Modulo R&amp;D Industrial"` (sin etiquetas HTML). |
| **Pasos de ejecución** | 1. Invocar `strip_html_tags("<script>alert(1)</script>Resistor", raise_error=True)`.<br/>2. Invocar `strip_html_tags("Modulo R&amp;D Industrial", raise_error=True)`. |
| **Resultado esperado** | Entrada 1 lanza `ValidationError("Remove HTML tags from this value")`; Entrada 2 es aceptada sin error. |
| **Resultado obtenido** | **FALLO (`DEF-05`):** La Entrada 1 se bloquea correctamente, pero en la Entrada 2 `nh3.clean` conserva `"Modulo R&amp;D Industrial"` y el ciclo `cleaned.replace('&amp;', '&')` (línea 954) reduce la longitud de 25 a 21 caracteres, haciendo que `len(cleaned) != len(value)` (línea 957) dispare un **falso positivo `ValidationError`**. |
| **Estado** | **Fallido** *(Defecto `DEF-05` reportado)* |

#### Caso Manual 11 (`CP-MAN-11`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-11` |
| **Nombre del caso** | Validación de unidades físicas del Sistema Internacional mediante Pint (`validate_physical_units`) |
| **Responsable** | **Juan Torres** |
| **Objetivo** | Verificar que [`validate_physical_units()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/validators.py#L20-L44) acepte unidades físicas válidas/prefijos SI y capture excepciones de unidades indefinidas o expresiones malformadas. |
| **Requisito asociado** | `RF09` (Técnica: **Partición de Equivalencia**) |
| **Precondiciones** | Registro de unidades `InvenTree.conversion.get_unit_registry()` cargado. |
| **Datos de entrada** | Clase válida: `"kohm"`, `"mm"`, `"uF"`, `""` | Clase inválida: `"unidad_falsa_xyz"`, `"100///["`. |
| **Pasos de ejecución** | 1. Ejecutar `validate_physical_units` con cada valor de la clase válida.<br/>2. Ejecutar con `"unidad_falsa_xyz"` y `"100///["`. |
| **Resultado esperado** | La clase válida retorna sin excepción; la clase inválida lanza `ValidationError("Invalid physical unit")`. |
| **Resultado obtenido** | Todas las entradas válidas son aceptadas y las inválidas son atrapadas por `UndefinedUnitError` y `TokenError` lanzando `ValidationError`. |
| **Estado** | **Aprobado** |

#### Caso Manual 12 (`CP-MAN-12`)
| Campo | Detalle |
| :--- | :--- |
| **Identificador** | `CP-MAN-12` |
| **Nombre del caso** | Diagnóstico de URL de servidor sin dominio de nivel superior (`invalid_site_url_hint`) |
| **Responsable** | **Juan Torres** |
| **Objetivo** | Evaluar el mensaje de ayuda diagnóstica `INVE-E17` generado por [`invalid_site_url_hint()`](file:///c:/Users/Emanuel%20Ortiz/Desktop/ACS/InvenTree/src/backend/InvenTree/InvenTree/validators.py#L93-L124) cuando se configura un hostname local sin TLD. |
| **Requisito asociado** | `RNF04` (Técnica: **Partición de Equivalencia**) |
| **Precondiciones** | Función `invalid_site_url_hint(site_url)` en `InvenTree/validators.py`. |
| **Datos de entrada** | URL 1: `"http://localhost:8000"` | URL 2: `"http://192.168.1.10:8000"` | URL 3: `"http://warehouse:8000"`. |
| **Pasos de ejecución** | 1. Invocar `invalid_site_url_hint` con `localhost` e IPv4.<br/>2. Invocar con `"http://warehouse:8000"` y verificar la sintaxis del mensaje `INVE-E17` en la línea 118. |
| **Resultado esperado** | URL 1 y 2 retornan `""`; URL 3 retorna `"INVE-E17: Top Level Domain Required.\n'warehouse' has no top-level domain..."`. |
| **Resultado obtenido** | **FALLO MENOR (`DEF-06`):** En `validators.py:L118` existe un carácter tipográfico `i` incrustado antes de la comilla simple: `f"INVE-E17: Top Level Domain Required.\ni'{hostname}' has no top-level domain..."`, produciendo `i'warehouse'` en consola. |
| **Estado** | **Fallido** *(Defecto `DEF-06` reportado)* |

---

### 6.3 Casos de Prueba Automatizados (8 Casos Ejecutados en Suite Principal)

| ID | Nombre del Caso Automatizado | Responsable | Req. | Técnica Aplicada | Datos de Entrada y Pasos Automatizados | Resultado Esperado | Resultado Obtenido | Estado |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **`CP-AUT-01`** | Validación de extracción y generación por lotes de números de serie (`extract_serial_numbers`) | **Emanuel Ortiz** | `RF03`<br/>`RNF04` | Partición de Equivalencia + Valores Límite (BVA) | Entrada: `"SN001-SN005"` (`qty=5`), `"A10+3"` (`qty=4`), `"1+"` (`qty=1000` y `qty=1001`), `"SN1, SN2, SN1"`, y serial de `101` chars. Ejecuta aserciones sobre `extract_serial_numbers`. | Expande rangos válidos y frontera `1000`; lanza `ValidationError` en frontera `1001`, duplicados y longitud `101`. | Rangos `SN001..SN005`, `A10..A13` y frontera `1000` aprobados; `1001`, duplicados y longitud `101` bloqueados con éxito (`7.68 ms`). | **Aprobado** |
| **`CP-AUT-02`** | Validación de integridad de lotes de inventario y partes rastreables/virtuales (`StockItem.clean`) | **Manuela Sánchez** | `RF04` | Tabla de Decisión + Valores Límite | Prueba 5 combinaciones en `StockItem.clean`: `virtual=True`, `trackable=True` con `qty=1.5`, `qty=-0.00001`, serializado con `qty=2` y serializado con `qty=0`. | Rechaza virtuales, decimales en trackables, negativos y serializados `>1`; normaliza `qty=0` a `1` y `delete_on_deplete=False`. | Las 5 reglas de integridad responden exactamente según especificación (`0.33 ms`). | **Aprobado** |
| **`CP-AUT-03`** | Control de límites de asignación multi-orden (`Build + Sales + Transfer`) en `SalesOrderAllocation` | **Manuela Sánchez** | `RF05` | Análisis de Valores Límite (BVA) + EP | `StockItem` con `qty=100` y reservas previas `{build:30, sales:40, transfer:10}` (disponible=`20`). Prueba asignaciones con `qty=20`, `qty=21` y `qty=0`. | Aprueba frontera exacta `qty=20`; rechaza `qty=21` con `"Stock item is over-allocated"` y `qty=0` con `"must be greater than zero"`. | Frontera `20` aprobada; fronteras inválidas `21` y `0` rechazadas con precisión (`0.22 ms`). | **Aprobado** |
| **`CP-AUT-04`** | Integridad referencial de `SalesOrderAllocation` y `TransferOrderAllocation` en `StockItem.merge_stock_items` | **Emanuel Ortiz** | `RF06`<br/>`RNF02` | Integración de Caja Blanca / Transición de Estados | Inspecciona y verifica la transferencia de llaves foráneas en `stock/models.py#L2860-L2875` frente al modelo `SalesOrderAllocation` (`order/models.py#L3336`). | Debe reasignar `allocation.item = self` en `sales_order_allocations` y `transfer_order_allocations` antes de `other.delete()`. | **Fallo detectado (`DEF-01`):** El código asigna `allocation.stock_item = self` (atributo inexistente) y omite `transfer_order_allocations`, causando borrado en cascada (`1.97 ms`). | **Fallido** |
| **`CP-AUT-05`** | Protección contra inyección de fórmulas CSV/Excel (OWASP CSV Injection) en `escape_export_value` | **Juan Torres** | `RF07`<br/>`RNF03` | Partición de Equivalencia (Seguridad OWASP) | Evalúa 6 vectores de ataque (`"=1+1"`, `"=CMD|..."`, `"@SUM..."`, `"+HYPERLINK..."`, `"-2+3+cmd"`, `"\t=1+1"`) y 5 entradas legítimas (`"-222"`, `"+1.5"`, `"-12e6"`, `4250`, `"Resistor"`). | Neutraliza los 6 vectores anteponiendo `'` y preserva intactos los 5 valores numéricos/texto legítimos. | 11 de 11 aserciones aprobadas sin falsos positivos ni negativos (`0.44 ms`). | **Aprobado** |
| **`CP-AUT-06`** | Enmascaramiento seguro de tokens de API en valores límite (`sanitize_token` con `back=0`) | **Juan Torres** | `RF08`<br/>`RNF03` | Análisis de Valores Límite (BVA) | Invoca `sanitize_token("inv-9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a", front=8, back=12)` y en el valor límite `back=0`. | En ningún caso la cadena retornada debe contener el token original sin enmascarar. | **Fallo detectado (`DEF-02`):** Con `back=0`, `token_value[-0:]` retorna todo el token completo pegado tras los asteriscos (`0.29 ms`). | **Fallido** |
| **`CP-AUT-07`** | Extracción y acotamiento de enteros sin signo (`extract_int` con `allow_negative=False`) | **Emanuel Ortiz** | `RF09` | Partición de Equivalencia + Valores Límite | Evalúa `"12345"`, `"0xFF"`, `"PART-0042"`, `"-50"` y el valor límite inferior `"-500"` con `clip=100, allow_negative=False`. | Todos los valores retornados deben ser enteros `>= 0`. | **Fallo detectado (`DEF-03`):** `extract_int("-500", clip=100, allow_negative=False)` retorna `-100` (negativo) porque `do_clip` retorna `-clip` antes de aplicar `abs(value)` (`0.33 ms`). | **Fallido** |
| **`CP-AUT-08`** | Verificación de ciclo de vida de `ApiToken`, políticas MFA y matriz RBAC (`RuleSetEnum`) | **Juan Torres** | `RF01`<br/>`RF10` | Tabla de Decisión + Transición de Estados | Verifica las 5 guardas de `validate_api_token` en `users/authentication.py` y los 12 dominios `RuleSetEnum` × 4 permisos CRUD en `users/ruleset.py`. | Presencia y exactitud de las 5 guardas de autenticación y las 48 combinaciones RBAC. | Las 5 guardas de seguridad y los 12 `RuleSetEnum` (`view, add, change, delete`) cumplen al 100% (`0.11 ms`). | **Aprobado** |
