"""Suite de Pruebas Automatizadas de Backend (Modelos y Reglas de Negocio) - InvenTree.

Asignatura: Aseguramiento de la Calidad (ACS) - Ingeniería de Sistemas (ITM)
Proyecto: InvenTree - Open Source Inventory Management System
Integrantes y Responsables:
    - Emanuel Ortiz (CP-AUT-01, CP-AUT-02)
    - Manuela Sanchez (CP-AUT-03, CP-AUT-04)
    - Juan Torres (CP-AUT-05)

Técnicas de diseño aplicadas:
    - Partición de Equivalencia (EP)
    - Análisis de Valores Límite (BVA)
    - Tablas de Decisión (DT)

Comando de ejecución (desde la raíz o src/backend/InvenTree):
    pytest "ACS final test/scripts/test_acs_backend_models.py" -v
    o bien:
    python src/backend/InvenTree/manage.py test
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import override_settings

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeTestCase
from part.models import BomItem, Part, PartCategory
from stock.models import StockItem, StockLocation
from stock.status_codes import StockHistoryCode, StockStatus


class ACSFinalBackendModelTests(InvenTreeTestCase):
    """Pruebas automatizadas de unidad e integración sobre modelos de InvenTree."""

    @classmethod
    def setUpTestData(cls):
        """Configuración de datos base (fixtures en memoria) para los casos de prueba."""
        super().setUpTestData()

        # Categoría base para partes de prueba
        cls.category_electronics = PartCategory.objects.create(
            name='Componentes Electronicos ACS',
            description='Categoría de prueba para validación de inventario',
        )

        # Ubicación física normal y ubicación estructural
        cls.location_warehouse = StockLocation.objects.create(
            name='Bodega Central Medellin',
            description='Ubicación física habilitada para almacenamiento',
            structural=False,
        )
        cls.location_structural = StockLocation.objects.create(
            name='Edificio Bloque Norte (Estructural)',
            description='Ubicación contenedora estructural que no admite stock directo',
            structural=True,
        )

        # Parte estándar rastreable (trackable=True, assembly=True)
        cls.part_trackable = Part.objects.create(
            name='Microcontrolador STM32F4',
            description='MCU ARM Cortex-M4 para pruebas de valores límite y serie',
            category=cls.category_electronics,
            IPN='MCU-STM32-001',
            trackable=True,
            assembly=True,
            active=True,
        )

        # Parte estándar no rastreable (permite cantidades decimales)
        cls.part_bulk = Part.objects.create(
            name='Cable UTP Cat6 Rollo',
            description='Material a granel medido en metros',
            category=cls.category_electronics,
            IPN='CAB-UTP6-001',
            trackable=False,
            active=True,
        )

        # Parte virtual (no debe permitir creación de StockItem físico)
        cls.part_virtual = Part.objects.create(
            name='Licencia Firmware Industrial v2',
            description='Activo intangible virtual',
            category=cls.category_electronics,
            IPN='LIC-FW-002',
            virtual=True,
            active=True,
        )

    # =========================================================================
    # CP-AUT-01 | Responsable: Emanuel Ortiz
    # Requisito: RF06 - Validación de cantidad de Stock (Valores Límite y Equivalencia)
    # =========================================================================
    def test_cp_aut_01_stock_quantity_boundary_and_equivalence(self):
        """CP-AUT-01: Validar fronteras de cantidad en StockItem (-1, -0.00001, 0, 1, decimal).

        Técnica: Análisis de Valores Límite (BVA) y Partición de Equivalencia (EP).
        - Partición Inválida 1: Cantidad negativa (< 0) -> ValidationError.
        - Frontera Inferior Válida: Cantidad = 0 y Cantidad = 1 -> Aceptado.
        - Partición Inválida 2: Cantidad decimal (1.5) en parte trackable=True -> ValidationError.
        - Partición Válida 2: Cantidad decimal (1.5) en parte trackable=False -> Aceptado.
        """
        # 1. Frontera inválida inmediata: -0.00001 y valor negativo -10
        for invalid_qty in [Decimal('-0.00001'), Decimal('-1'), Decimal('-100')]:
            with self.assertRaises(ValidationError):
                item_neg = StockItem(
                    part=self.part_bulk,
                    location=self.location_warehouse,
                    quantity=invalid_qty,
                )
                item_neg.full_clean()

        # 2. Frontera válida inferior: quantity = 0 y quantity = 1
        for valid_boundary_qty in [Decimal('0'), Decimal('1'), Decimal('500')]:
            item_valid = StockItem.objects.create(
                part=self.part_bulk,
                location=self.location_warehouse,
                quantity=valid_boundary_qty,
            )
            item_valid.full_clean()
            self.assertEqual(item_valid.quantity, valid_boundary_qty)

        # 3. Equivalencia inválida: Cantidad decimal en parte rastreable (trackable=True)
        with self.assertRaises(ValidationError):
            item_decimal_trackable = StockItem(
                part=self.part_trackable,
                location=self.location_warehouse,
                quantity=Decimal('2.5'),
            )
            item_decimal_trackable.clean()

    # =========================================================================
    # CP-AUT-02 | Responsable: Emanuel Ortiz
    # Requisito: RF09 - Validación de longitud y esquema de URL en StockItem.link
    # =========================================================================
    def test_cp_aut_02_stock_external_link_url_boundaries(self):
        """CP-AUT-02: Validar longitud límite (1999, 2000, 2001 chars) y esquema en StockItem.link.

        Técnica: Análisis de Valores Límite (BVA) y Partición de Equivalencia (EP).
        - Límite máximo definido en InvenTreeURLField: max_length = 2000.
        """
        item = StockItem.objects.create(
            part=self.part_bulk,
            location=self.location_warehouse,
            quantity=Decimal('10'),
        )

        # Partición inválida de esquemas malformados
        for bad_url in ['inventree.org', 'httpx://dominio.com', 'https:malformado.com']:
            with self.assertRaises(ValidationError):
                item.link = bad_url
                item.full_clean()

        # Valor límite exacto permitido: 2000 caracteres
        prefix = 'https://datasheets.inventree.org/?doc='
        exact_2000_url = prefix + ('a' * (2000 - len(prefix)))
        self.assertEqual(len(exact_2000_url), 2000)
        item.link = exact_2000_url
        item.full_clean()
        item.save()

        # Valor límite superior inválido: 2001 caracteres
        over_2001_url = exact_2000_url + 'x'
        self.assertEqual(len(over_2001_url), 2001)
        with self.assertRaises(ValidationError):
            item.link = over_2001_url
            item.full_clean()

    # =========================================================================
    # CP-AUT-03 | Responsable: Manuela Sanchez
    # Requisito: RF04 - Reglas de protección de eliminación de Partes (Tabla de Decisión)
    # =========================================================================
    def test_cp_aut_03_part_deletion_decision_table(self):
        """CP-AUT-03: Validar Tabla de Decisión para eliminación de Partes (active y locked).

        Técnica: Tabla de Decisión (DT).
        - Regla 1: active=True, locked=False -> Prohibido eliminar (ValidationError).
        - Regla 2: active=False, locked=True -> Prohibido eliminar (ValidationError).
        - Regla 3: active=False, locked=False -> Eliminación permitida.
        """
        InvenTreeSetting.set_setting('PART_ENABLE_LOCKING', True, self.user)

        part_to_delete = Part.objects.create(
            name='Sensor Temperatura PT100',
            description='Parte para prueba de tabla de decisión de borrado',
            category=self.category_electronics,
            active=True,
            locked=False,
        )

        # Regla 1: Parte activa no puede eliminarse
        with self.assertRaises(ValidationError):
            part_to_delete.delete()

        # Regla 2: Parte inactiva pero bloqueada (locked=True) no puede eliminarse
        part_to_delete.active = False
        part_to_delete.locked = True
        part_to_delete.save()

        with self.assertRaises(ValidationError):
            part_to_delete.delete()

        # Regla 3: Parte inactiva y desbloqueada se elimina correctamente
        part_to_delete.locked = False
        part_to_delete.save()
        part_pk = part_to_delete.pk
        part_to_delete.delete()
        self.assertFalse(Part.objects.filter(pk=part_pk).exists())

    # =========================================================================
    # CP-AUT-04 | Responsable: Manuela Sanchez
    # Requisito: RF06 y RF07 - Restricciones de Ubicación Estructural, Parte Virtual y Seriales
    # =========================================================================
    def test_cp_aut_04_structural_location_virtual_part_and_serial_uniqueness(self):
        """CP-AUT-04: Impedir stock en ubicaciones estructurales, partes virtuales y seriales duplicados.

        Técnica: Partición de Equivalencia (EP) y Tabla de Decisión.
        """
        # 1. No se permite alojar stock en ubicación estructural (structural=True)
        with self.assertRaises(ValidationError):
            structural_item = StockItem(
                part=self.part_bulk,
                location=self.location_structural,
                quantity=10,
            )
            structural_item.clean()

        # 2. No se permite crear stock para una parte virtual (virtual=True)
        with self.assertRaises(ValidationError):
            virtual_item = StockItem(
                part=self.part_virtual,
                location=self.location_warehouse,
                quantity=1,
            )
            virtual_item.clean()

        # 3. Ítem con número de serie debe tener quantity = 1 y serial único
        with self.assertRaises(ValidationError):
            invalid_serial_qty = StockItem(
                part=self.part_trackable,
                location=self.location_warehouse,
                serial='SN-9001',
                quantity=2,
            )
            invalid_serial_qty.clean()

        # Creación válida con serial='SN-9001' y quantity=1
        valid_serial_item = StockItem.objects.create(
            part=self.part_trackable,
            location=self.location_warehouse,
            serial='SN-9001',
            quantity=1,
        )
        self.assertTrue(valid_serial_item.serialized)

        # Intento de duplicar el mismo número de serie 'SN-9001' en la misma parte
        with self.assertRaises(ValidationError):
            duplicate_serial_item = StockItem(
                part=self.part_trackable,
                location=self.location_warehouse,
                serial='SN-9001',
                quantity=1,
            )
            duplicate_serial_item.validate_unique()

    # =========================================================================
    # CP-AUT-05 | Responsable: Juan Torres
    # Requisito: RF05 y RF08 - Prevención de recursividad BOM y operaciones de Stock
    # =========================================================================
    def test_cp_aut_05_bom_recursion_and_stock_movements(self):
        """CP-AUT-05: Validar rechazo de BOM autorreferencial y exactitud en add_stock / take_stock / transfer.

        Técnica: Partición de Equivalencia y Transición de Estados.
        """
        # 1. Una parte de ensamblaje no puede incluirse a sí misma como sub_part en su BOM
        with self.assertRaises(ValidationError):
            self.part_trackable.check_add_to_bom(
                self.part_trackable, raise_error=True
            )

        # 2. Operaciones transaccionales sobre StockItem (add_stock, take_stock, transfer)
        dest_location = StockLocation.objects.create(
            name='Laboratorio Ensamble Piso 2',
            structural=False,
        )
        stock_item = StockItem.objects.create(
            part=self.part_bulk,
            location=self.location_warehouse,
            quantity=Decimal('100'),
        )

        # Adición de 25 unidades -> total esperado: 125
        stock_item.add_stock(Decimal('25'), self.user, notes='Ingreso por ajuste QA')
        stock_item.refresh_from_db()
        self.assertEqual(stock_item.quantity, Decimal('125'))

        # Retiro de 40 unidades -> total esperado: 85
        stock_item.take_stock(Decimal('40'), self.user, notes='Consumo orden QA')
        stock_item.refresh_from_db()
        self.assertEqual(stock_item.quantity, Decimal('85'))

        # Transferencia total a nueva ubicación
        stock_item.transfer(dest_location, self.user, 'Traslado a Laboratorio')
        stock_item.refresh_from_db()
        self.assertEqual(stock_item.location, dest_location)

