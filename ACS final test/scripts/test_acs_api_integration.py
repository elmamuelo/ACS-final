"""Suite de Pruebas Automatizadas de Integración API REST y Seguridad RBAC - InvenTree.

Asignatura: Aseguramiento de la Calidad (ACS) - Ingeniería de Sistemas (ITM)
Proyecto: InvenTree - Open Source Inventory Management System
Integrantes y Responsables:
    - Emanuel Ortiz (CP-AUT-06: Control de Acceso y Autenticación API - RNF04 / RF01)
    - Manuela Sanchez (CP-AUT-07: Creación y Validación de Partes vía REST API - RF03)
    - Juan Torres (CP-AUT-08: Ajustes de Stock y Transferencia vía REST API - RF08)

Comando de ejecución:
    pytest "ACS final test/scripts/test_acs_api_integration.py" -v
"""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part, PartCategory
from stock.models import StockItem, StockLocation


class ACSFinalAPIIntegrationTests(InvenTreeAPITestCase):
    """Pruebas de integración sobre la API RESTful de InvenTree."""

    roles = [
        'part.view',
        'part.add',
        'part.change',
        'part_category.view',
        'part_category.add',
        'stock.view',
        'stock.add',
        'stock.change',
        'stock_location.view',
        'stock_location.add',
    ]

    @classmethod
    def setUpTestData(cls):
        """Inicialización de datos para pruebas de integración API."""
        super().setUpTestData()

        cls.category = PartCategory.objects.create(
            name='Sensores Industriales API',
            description='Categoría creada para pruebas de integración API',
        )
        cls.loc_origen = StockLocation.objects.create(
            name='Almacen Principal A1',
            description='Ubicación origen para transferencia API',
        )
        cls.loc_destino = StockLocation.objects.create(
            name='Estacion Ensamble B2',
            description='Ubicación destino para transferencia API',
        )
        cls.part_sample = Part.objects.create(
            name='Modulo Transceptor CAN-BUS',
            description='Transceptor industrial MCP2551',
            category=cls.category,
            IPN='CAN-MCP2551-01',
            active=True,
        )

    # =========================================================================
    # CP-AUT-06 | Responsable: Emanuel Ortiz
    # Requisito: RF01 / RNF04 - Autenticación obligatoria y Control de Acceso (RBAC)
    # =========================================================================
    def test_cp_aut_06_api_authentication_and_rbac_security(self):
        """CP-AUT-06: Verificar rechazo HTTP 401/403 ante peticiones no autenticadas o sin rol.

        Técnica: Partición de Equivalencia (Sesión anónima vs. Usuario sin permisos vs. Usuario con rol).
        """
        part_list_url = reverse('api-part-list')

        # 1. Cliente anónimo sin credenciales -> Debe rechazar con 401 Unauthorized o 403 Forbidden
        anonymous_client = APIClient()
        anon_response = anonymous_client.get(part_list_url)
        self.assertIn(
            anon_response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

        # 2. Cliente autenticado con permisos asignados -> Debe responder 200 OK
        auth_response = self.client.get(part_list_url)
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)

        # 3. Remoción de permisos de escritura -> Intento de POST debe retornar 403 Forbidden
        self.clearRoles()
        self.assignRole('part.view')
        forbidden_post = self.client.post(
            part_list_url,
            data={
                'name': 'Parte No Autorizada',
                'description': 'Intento sin rol part.add',
                'category': self.category.pk,
            },
            format='json',
        )
        self.assertEqual(forbidden_post.status_code, status.HTTP_403_FORBIDDEN)

        # Restaurar roles para las demás pruebas
        for role in self.roles:
            self.assignRole(role)

    # =========================================================================
    # CP-AUT-07 | Responsable: Manuela Sanchez
    # Requisito: RF03 - Creación de Parte vía API REST (/api/part/) y validación de campos
    # =========================================================================
    def test_cp_aut_07_api_create_part_validation(self):
        """CP-AUT-07: Validar creación exitosa (201 Created) y rechazo por datos faltantes (400 Bad Request).

        Técnica: Partición de Equivalencia en payloads JSON de la API REST.
        """
        part_list_url = reverse('api-part-list')

        # Caso 1: Payload válido -> 201 Created
        valid_payload = {
            'name': 'Regulador Voltaje LM2596',
            'description': 'Convertidor DC-DC Step-Down 3A',
            'IPN': 'REG-LM2596-3A',
            'category': self.category.pk,
            'minimum_stock': 15,
            'active': True,
        }
        response_ok = self.client.post(part_list_url, data=valid_payload, format='json')
        self.assertEqual(response_ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_ok.data['name'], 'Regulador Voltaje LM2596')
        self.assertEqual(response_ok.data['IPN'], 'REG-LM2596-3A')

        # Caso 2: Payload inválido (nombre vacío '') -> 400 Bad Request
        invalid_payload = {
            'name': '',
            'description': 'Parte sin nombre obligatorio',
            'category': self.category.pk,
        }
        response_bad = self.client.post(
            part_list_url, data=invalid_payload, format='json'
        )
        self.assertEqual(response_bad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response_bad.data)

    # =========================================================================
    # CP-AUT-08 | Responsable: Juan Torres
    # Requisito: RF08 - Creación y Transferencia de Stock vía API REST (/api/stock/transfer/)
    # =========================================================================
    def test_cp_aut_08_api_stock_creation_and_transfer(self):
        """CP-AUT-08: Validar creación de lote de Stock y transferencia parcial entre ubicaciones vía API.

        Técnica: Valores Límite y Transición de Estados en movimientos de almacén.
        """
        stock_list_url = reverse('api-stock-list')
        transfer_url = reverse('api-stock-transfer')

        # 1. Crear StockItem con 50 unidades en Almacen Principal A1
        create_res = self.client.post(
            stock_list_url,
            data={
                'part': self.part_sample.pk,
                'location': self.loc_origen.pk,
                'quantity': 50,
            },
            format='json',
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        stock_pk = create_res.data['pk']

        # 2. Intentar transferir cantidad superior al saldo disponible (51 > 50) -> 400 Bad Request
        over_transfer_res = self.client.post(
            transfer_url,
            data={
                'items': [
                    {
                        'pk': stock_pk,
                        'quantity': 51,
                    }
                ],
                'location': self.loc_destino.pk,
                'notes': 'Intento de transferencia excediendo límite disponible',
            },
            format='json',
        )
        self.assertEqual(over_transfer_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Transferir exactamente 20 unidades a Estacion Ensamble B2 -> 200 OK / 201 Created
        valid_transfer_res = self.client.post(
            transfer_url,
            data={
                'items': [
                    {
                        'pk': stock_pk,
                        'quantity': 20,
                    }
                ],
                'location': self.loc_destino.pk,
                'notes': 'Transferencia parcial validada por QA',
            },
            format='json',
        )
        self.assertIn(
            valid_transfer_res.status_code,
            [status.HTTP_200_OK, status.HTTP_201_CREATED],
        )

        # Verificar que el ítem original quedó con 30 unidades y se creó el nuevo ítem con 20 en destino
        item_origen = StockItem.objects.get(pk=stock_pk)
        self.assertEqual(item_origen.quantity, Decimal('30'))

        item_destino = StockItem.objects.filter(
            part=self.part_sample, location=self.loc_destino
        ).first()
        self.assertIsNotNone(item_destino)
        self.assertEqual(item_destino.quantity, Decimal('20'))

