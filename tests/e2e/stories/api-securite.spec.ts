/**
 * API Securite
 *
 * Tests API : health 200, security headers, auth 401 sans token, XSS escaped
 *
 * User Stories : US-800 a US-808
 */

import { test, expect } from '@playwright/test';

import { BACKEND_URL } from './helpers/backend';

test.describe('API Securite', () => {

  test('US-800.HP : GET /health retourne 200', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`);
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('status');
  });

  test('US-801.HP : GET /health retourne 200 (pas /api/health)', async ({ request }) => {
    // L'endpoint sante est /health, pas /api/health
    const response = await request.get(`${BACKEND_URL}/health`);
    expect(response.status()).toBe(200);
  });

  test('US-802.HP : les headers de securite sont presents sur les reponses', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`);
    const headers = response.headers();

    // X-Content-Type-Options: nosniff (SEC-023)
    expect(headers['x-content-type-options']).toBe('nosniff');

    // X-Frame-Options: DENY (SEC-023)
    expect(headers['x-frame-options']).toBe('DENY');

    // X-XSS-Protection: 1; mode=block (SEC-023)
    expect(headers['x-xss-protection']).toBe('1; mode=block');
  });

  test('US-803.HP : GET /api/config sans token retourne 401', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/config`, {
      headers: {
        // Pas de X-Therese-Token
      },
    });
    expect(response.status()).toBe(401);

    const body = await response.json();
    expect(body.code).toBe('UNAUTHORIZED');
  });

  test('US-804.HP : GET /api/memory/contacts sans token retourne 401', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/memory/contacts`);
    expect(response.status()).toBe(401);
  });

  test('US-805.HP : POST /api/chat sans token retourne 401', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/chat`, {
      data: { message: 'test' },
    });
    expect(response.status()).toBe(401);
  });

  test('US-806.HP : GET /api/auth/token retourne un token (endpoint exempt)', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/auth/token`);
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('token');
  });

  test('US-807.HP : un token invalide retourne 401', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/config`, {
      headers: {
        'X-Therese-Token': 'invalid-fake-token-12345',
      },
    });
    expect(response.status()).toBe(401);

    const body = await response.json();
    expect(body.code).toBe('UNAUTHORIZED');
    expect(body.message).toContain('invalide');
  });

  test('US-808.HP : XSS dans les parametres est rejete ou echappe', async ({ request }) => {
    // Recuperer un token valide
    const tokenResp = await request.get(`${BACKEND_URL}/api/auth/token`);
    const { token } = await tokenResp.json();

    if (!token) {
      test.skip(true, 'Pas de token disponible (backend en mode dev sans token)');
      return;
    }

    // Tenter d'injecter du XSS dans une recherche
    const xssPayload = '<script>alert("xss")</script>';
    const response = await request.get(`${BACKEND_URL}/api/memory/contacts`, {
      headers: { 'X-Therese-Token': token },
      params: { search: xssPayload },
    });

    // La reponse ne doit pas contenir le script brut non echappe
    const text = await response.text();
    expect(text).not.toContain('<script>alert("xss")</script>');
  });

  test('US-802.HP : les endpoints exempts n\'exigent pas de token', async ({ request }) => {
    const exemptPaths = ['/health', '/api/auth/token'];

    for (const path of exemptPaths) {
      const response = await request.get(`${BACKEND_URL}${path}`);
      expect(response.status()).toBe(200);
    }
  });

  test('US-803.HP : les endpoints proteges exigent tous un token', async ({ request }) => {
    const protectedPaths = [
      '/api/config',
      '/api/memory/contacts',
      '/api/memory/projects',
      '/api/crm/activities',
    ];

    for (const path of protectedPaths) {
      const response = await request.get(`${BACKEND_URL}${path}`);
      expect(response.status()).toBe(401);
    }
  });
});
