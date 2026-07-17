/**
 * API Endpoints
 *
 * Tests API : tous les endpoints principaux avec token auth
 *
 * User Stories : US-040, US-300+, US-500+
 */

import { test, expect } from '@playwright/test';

import { BACKEND_URL } from './helpers/backend';

let authToken: string;

test.beforeAll(async ({ request }) => {
  // Recuperer le token d'authentification
  const tokenResp = await request.get(`${BACKEND_URL}/api/auth/token`);
  expect(tokenResp.status()).toBe(200);
  const body = await tokenResp.json();
  authToken = body.token || '';
});

function headers() {
  return authToken ? { 'X-Therese-Token': authToken } : {};
}

test.describe('API Endpoints - Health & Status', () => {

  test('US-040.HP : GET /health retourne status ok', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/health`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.status).toBeTruthy();
  });

  test('US-040.HP : GET /health/services retourne les services', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/health/services`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toBeTruthy();
  });
});

test.describe('API Endpoints - Config', () => {

  test('US-040.HP : GET /api/config retourne la configuration', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/config`, {
      headers: headers(),
    });

    if (!authToken) {
      expect(resp.status()).toBe(401);
      return;
    }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toBeTruthy();
  });
});

test.describe('API Endpoints - Memory (Contacts & Projets)', () => {

  test('US-500.HP : GET /api/memory/contacts retourne une liste', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/memory/contacts`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test('US-501.HP : POST /api/memory/contacts cree un contact', async ({ request }) => {
    const resp = await request.post(`${BACKEND_URL}/api/memory/contacts`, {
      headers: { ...headers(), 'Content-Type': 'application/json' },
      data: {
        first_name: 'E2E',
        last_name: 'Test',
        email: 'e2e-test@example.com',
        company: 'Test Corp',
      },
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.first_name).toBe('E2E');
    expect(body.last_name).toBe('Test');
    expect(body).toHaveProperty('id');
  });

  test('US-502.HP : GET /api/memory/projects retourne une liste', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/memory/projects`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
  });
});

test.describe('API Endpoints - CRM', () => {

  test('US-300.HP : GET /api/crm/activities retourne une liste', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/crm/activities`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test('US-301.HP : GET /api/crm/pipeline/stats retourne les stats pipeline', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/crm/pipeline/stats`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toBeTruthy();
  });

  test('US-301.HP : POST /api/crm/contacts cree un contact CRM', async ({ request }) => {
    const resp = await request.post(`${BACKEND_URL}/api/crm/contacts`, {
      headers: { ...headers(), 'Content-Type': 'application/json' },
      data: {
        first_name: 'CRM',
        last_name: 'E2E',
        email: 'crm-e2e@example.com',
        company: 'CRM Test Inc',
        tags: ['test', 'e2e'],
      },
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    // 200 ou 201
    expect([200, 201]).toContain(resp.status());
    const body = await resp.json();
    expect(body).toHaveProperty('id');
  });

  test('US-300.HP : GET /api/crm/deliverables retourne une liste', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/crm/deliverables`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
  });
});

test.describe('API Endpoints - Email Setup', () => {

  test('US-110.HP : GET /api/email/setup/status retourne le statut', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/email/setup/status`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toBeTruthy();
  });
});

test.describe('API Endpoints - Data (Export/Backup)', () => {

  test('US-040.HP : GET /api/data/backups retourne la liste des backups', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/data/backups`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body) || typeof body === 'object').toBe(true);
  });

  test('US-040.HP : GET /api/data/logs retourne les logs', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/data/logs`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
  });
});

test.describe('API Endpoints - Perf', () => {

  test('US-040.HP : GET /api/perf/status retourne le status systeme', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/perf/status`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toBeTruthy();
  });

  test('US-040.HP : GET /api/perf/metrics retourne les metriques', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/perf/metrics`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
  });
});

test.describe('API Endpoints - Commands', () => {

  test('US-040.HP : GET /api/commands/user retourne les commandes utilisateur', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/commands/user`, {
      headers: headers(),
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
  });
});

test.describe('API Endpoints - Validation des reponses', () => {

  test('US-040.HP : les reponses JSON ont le bon Content-Type', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/health`);
    const contentType = resp.headers()['content-type'];
    expect(contentType).toContain('application/json');
  });

  test('US-040.HP : un endpoint inexistant retourne 404', async ({ request }) => {
    const resp = await request.get(`${BACKEND_URL}/api/this-endpoint-does-not-exist`, {
      headers: headers(),
    });
    // Avec le token, un endpoint inexistant retourne 404 (ou 401 sans token)
    expect([404, 401, 405]).toContain(resp.status());
  });

  test('US-040.HP : POST avec body vide sur endpoint qui attend du JSON retourne 4xx', async ({ request }) => {
    const resp = await request.post(`${BACKEND_URL}/api/crm/contacts`, {
      headers: { ...headers(), 'Content-Type': 'application/json' },
      data: {},
    });

    if (!authToken) { expect(resp.status()).toBe(401); return; }

    // Devrait retourner 422 (validation error) ou 400
    expect([400, 422]).toContain(resp.status());
  });
});
