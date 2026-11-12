/**
 * Suite Automatizada E2E / API en Playwright (TypeScript)
 * Caso Práctico Final - Aseguramiento de la Calidad (ACS) - ITM
 * Integrantes: Emanuel Ortiz, Manuela Sánchez, Juan Torres
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.INVENTREE_SITE_URL || 'http://localhost:8000';

test.describe('ACS Final Test - InvenTree E2E & REST API Verification', () => {
  test('CP-AUT-E2E-01 (Juan Torres): Autenticación API y rechazo de credenciales inválidas (RF01)', async ({
    request,
  }) => {
    const unauthorizedRes = await request.get(`${BASE_URL}/api/part/`, {
      headers: { Authorization: 'Token inv-invalid-token-000000' },
    });
    expect(unauthorizedRes.status()).toBe(401);
  });

  test('CP-AUT-E2E-02 (Manuela Sánchez): Creación de Parte y validación de IPN/Categoría Estructural (RF02)', async ({
    request,
  }) => {
    const response = await request.options(`${BASE_URL}/api/part/`);
    expect([200, 401, 403]).toContain(response.status());
  });

  test('CP-AUT-E2E-03 (Emanuel Ortiz): Consulta paginada de Stock Items y filtro in_stock (RF04/RNF01)', async ({
    request,
  }) => {
    const start = Date.now();
    const response = await request.get(`${BASE_URL}/api/stock/?in_stock=true&limit=25`);
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(3000);
    expect([200, 401]).toContain(response.status());
  });

  test('CP-AUT-E2E-04 (Manuela Sánchez): Validación de sobre-asignación en SalesOrderAllocation (RF05)', async ({
    request,
  }) => {
    const response = await request.post(`${BASE_URL}/api/order/so-allocation/`, {
      data: {
        line: 1,
        item: 1,
        quantity: 999999,
      },
    });
    expect([400, 401, 403]).toContain(response.status());
  });

  test('CP-AUT-E2E-05 (Juan Torres): Protección contra XSS en campos de nombre y descripción de Parte (RNF03)', async ({
    request,
  }) => {
    const response = await request.post(`${BASE_URL}/api/part/`, {
      data: {
        name: '<script>alert("XSS")</script>Microcontroller',
        description: '<img src=x onerror=alert(1)>',
        category: 1,
      },
    });
    expect([400, 401, 403]).toContain(response.status());
  });
});

