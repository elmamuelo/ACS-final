"""Script de Pruebas de Rendimiento y Tiempo de Respuesta (Benchmark API) - InvenTree.

Asignatura: Aseguramiento de la Calidad (ACS) - Ingeniería de Sistemas (ITM)
Proyecto: InvenTree - Open Source Inventory Management System
Responsable Principal: Juan Torres (con apoyo de Emanuel Ortiz y Manuela Sanchez)
Requisito Asociado: RNF01 (Tiempo de respuesta de endpoints críticos < 500 ms promedio y < 2000 ms P95)

Descripción:
    Este script ejecuta pruebas de carga secuencial y medición estadística de latencia
    (Media, Mediana, Mínimo, Máximo, Percentil 95) sobre los endpoints críticos de
    InvenTree (/api/part/, /api/stock/, /api/stock/location/, /api/search/).
    Puede ejecutarse tanto como test de Django/pytest (usando APIClient) como contra un
    servidor activo mediante HTTP (urllib/requests).
"""

import json
import os
import statistics
import time
import urllib.request
from decimal import Decimal

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part, PartCategory
from stock.models import StockItem, StockLocation


class ACSFinalPerformanceTests(InvenTreeAPITestCase):
    """CP-PERF-01: Pruebas de rendimiento y tiempos de respuesta sobre API REST."""

    roles = [
        'part.view',
        'part.add',
        'part_category.view',
        'stock.view',
        'stock.add',
        'stock_location.view',
    ]

    @classmethod
    def setUpTestData(cls):
        """Poblar lote de datos de prueba para evaluar tiempos de respuesta con carga realista."""
        super().setUpTestData()

        cls.category = PartCategory.objects.create(
            name='Categoria Benchmark Rendimiento',
            description='Categoría para pruebas de carga RNF01',
        )
        cls.location = StockLocation.objects.create(
            name='Almacen Benchmark Central',
            description='Ubicación para pruebas de carga RNF01',
        )

        # Crear 50 partes y 50 ítems de stock para medir consulta y serialización
        for idx in range(1, 51):
            part = Part.objects.create(
                name=f'Componente Rendimiento #{idx:03d}',
                description=f'Parte generada para prueba de carga iteración {idx}',
                category=cls.category,
                IPN=f'PERF-IPN-{idx:04d}',
                active=True,
            )
            StockItem.objects.create(
                part=part,
                location=cls.location,
                quantity=Decimal(idx * 5),
            )

    def _measure_endpoint(self, url: str, method: str = 'GET', payload: dict | None = None, iterations: int = 30) -> dict:
        """Ejecuta N peticiones midiendo latencia en milisegundos y calcula métricas estadísticas."""
        latencies_ms = []

        for _ in range(iterations):
            t0 = time.perf_counter()
            if method == 'GET':
                response = self.client.get(url)
            else:
                response = self.client.post(url, data=payload or {}, format='json')
            t1 = time.perf_counter()

            self.assertEqual(response.status_code, 200)
            latencies_ms.append((t1 - t0) * 1000.0)

        sorted_lat = sorted(latencies_ms)
        p95_index = max(0, int(len(sorted_lat) * 0.95) - 1)

        metrics = {
            'endpoint': url,
            'method': method,
            'iterations': iterations,
            'min_ms': round(min(latencies_ms), 2),
            'mean_ms': round(statistics.mean(latencies_ms), 2),
            'median_ms': round(statistics.median(latencies_ms), 2),
            'p95_ms': round(sorted_lat[p95_index], 2),
            'max_ms': round(max(latencies_ms), 2),
        }
        return metrics

    def test_cp_perf_01_api_response_time_sla(self):
        """CP-PERF-01: Validar que los endpoints críticos cumplan RNF01 (Media < 500 ms, P95 < 2000 ms)."""
        endpoints = [
            ('/api/part/?limit=25', 'GET', None),
            ('/api/stock/?limit=25', 'GET', None),
            ('/api/stock/location/?limit=25', 'GET', None),
            (
                '/api/search/',
                'POST',
                {
                    'search': 'PERF-IPN',
                    'limit': 25,
                    'part': {'active': True},
                    'stockitem': {'in_stock': True},
                },
            ),
        ]

        print('\n' + '=' * 85)
        print('REPORTE DE PRUEBA DE RENDIMIENTO (CP-PERF-01 - RNF01) - INVENTREE API')
        print('=' * 85)
        print(f"{'Endpoint':<30} | {'Método':<6} | {'Media (ms)':<10} | {'Mediana':<8} | {'P95 (ms)':<9} | {'Máx (ms)':<8}")
        print('-' * 85)

        for url, method, payload in endpoints:
            stats = self._measure_endpoint(url, method=method, payload=payload, iterations=30)
            print(
                f"{stats['endpoint']:<30} | {stats['method']:<6} | "
                f"{stats['mean_ms']:<10.2f} | {stats['median_ms']:<8.2f} | "
                f"{stats['p95_ms']:<9.2f} | {stats['max_ms']:<8.2f}"
            )
            # Validación del acuerdo de nivel de servicio (SLA definido en RNF01)
            self.assertLess(
                stats['mean_ms'],
                500.0,
                f"El tiempo medio de {url} ({stats['mean_ms']} ms) superó el umbral de 500 ms",
            )
            self.assertLess(
                stats['p95_ms'],
                2000.0,
                f"El percentil 95 de {url} ({stats['p95_ms']} ms) superó el umbral de 2000 ms",
            )

        print('=' * 85 + '\n')

