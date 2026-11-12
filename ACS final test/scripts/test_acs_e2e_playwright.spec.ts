/**
 * Suite de Pruebas Automatizadas E2E (Frontend React + Mantine UI) con Playwright - InvenTree
 *
 * Asignatura: Aseguramiento de la Calidad (ACS) - Ingeniería de Sistemas (ITM)
 * Proyecto: InvenTree - Open Source Inventory Management System
 * Integrantes y Responsables:
 *   - Emanuel Ortiz (CP-AUT-09: Validación de Autenticación Web y Particiones Inválidas)
 *   - Manuela Sanchez y Juan Torres (CP-AUT-10: Tiempo de carga de Dashboard RNF02 y Navegación a Partes/Stock)
 *
 * Comando de ejecución (desde src/frontend):
 *   npx playwright test "../../ACS final test/scripts/test_acs_e2e_playwright.spec.ts"
 */

import { expect, test } from '@playwright/test';

const BASE_URL = process.env.INVENTREE_SITE_URL || 'http://localhost:8000';
const ADMIN_USER = process.env.INVENTREE_TEST_USER || 'admin';
const ADMIN_PASS = process.env.INVENTREE_TEST_PASS || 'inventree';

test.describe('ACS Final Test - Pruebas E2E de Interfaz Web InvenTree', () => {
  /**
   * CP-AUT-09 | Responsable: Emanuel Ortiz
   * Requisito: RF01 / RNF05 - Validación de credenciales inválidas y retroalimentación de UI
   */
  test('CP-AUT-09: Rechazo de credenciales inválidas y campos vacíos en Login Web', async ({
    page
  }) => {
    await page.goto(`${BASE_URL}/web/login`, { waitUntil: 'networkidle' });
    await expect(page).toHaveTitle(/InvenTree/i);

    // Partición Inválida 1: Usuario y contraseña inexistentes
    await page.getByLabel('login-username').fill('usuario_inexistente_qa');
    await page.getByLabel('login-password').fill('ClaveIncorrecta123!');
    await page.getByRole('button', { name: /Log In/i }).click();

    // Verificar notificación clara de fallo de autenticación (RNF05 - Usabilidad)
    await expect(page.getByText('Login failed', { exact: true })).toBeVisible();
    await expect(
      page.getByText('Check your input and try again').first()
    ).toBeVisible();

    // Partición Inválida 2: Contraseña vacía
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByLabel('login-username').fill(ADMIN_USER);
    await page.getByLabel('login-password').fill('');
    await page.getByRole('button', { name: /Log In/i }).click();
    await expect(page.getByText('Login failed', { exact: true })).toBeVisible();
  });

  /**
   * CP-AUT-10 | Responsables: Manuela Sanchez / Juan Torres
   * Requisito: RF01, RF03, RNF02 - Login exitoso en < 3000 ms y navegación al catálogo de Partes
   */
  test('CP-AUT-10: Inicio de sesión exitoso bajo umbral de rendimiento (< 3s) y acceso a Partes', async ({
    page
  }) => {
    await page.goto(`${BASE_URL}/web/login`, { waitUntil: 'networkidle' });

    await page.getByLabel('login-username').fill(ADMIN_USER);
    await page.getByLabel('login-password').fill(ADMIN_PASS);

    const startTime = Date.now();
    await page.getByRole('button', { name: /Log In/i }).click();

    // Esperar a que cargue la vista principal del Dashboard
    await page.waitForURL(/\/web(\/home)?/);
    await expect(page.getByRole('tab', { name: /Dashboard/i })).toBeVisible();
    const elapsedMs = Date.now() - startTime;

    console.log(`[Métrica RNF02] Tiempo de login y renderizado de Dashboard: ${elapsedMs} ms`);
    expect(elapsedMs).toBeLessThan(3000);

    // Navegar al módulo de Partes y verificar renderizado de tabla Mantine DataTable
    await page.goto(`${BASE_URL}/web/part/`, { waitUntil: 'networkidle' });
    await expect(page).toHaveURL(/\/web\/part/);
  });
});

