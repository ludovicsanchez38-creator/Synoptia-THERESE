import { readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { Page } from '@playwright/test';

/**
 * Backend E2E dédié (revue 0.40).
 *
 * Les E2E ne doivent JAMAIS toucher l'instance THÉRÈSE réelle : pendant la
 * revue 0.40, la suite a créé deux contacts dans la base de production
 * (port 17293). Le port est donc dédié, refusé s'il vaut 17293, et le backend
 * correspondant est lancé par playwright.config.ts sur un dossier de données
 * jetable (tests/e2e/run-e2e-backend.sh).
 */
export const E2E_BACKEND_PORT = Number(process.env.THERESE_E2E_PORT ?? 17393);

if (E2E_BACKEND_PORT === 17293) {
  throw new Error(
    'E2E interdits sur le port 17293 (instance THÉRÈSE réelle) : choisis un autre THERESE_E2E_PORT.',
  );
}

export const BACKEND_URL = `http://127.0.0.1:${E2E_BACKEND_PORT}`;

/** Le secret vient du fichier de l'instance jetable, sous le compte du test. */
export async function lireJetonPriveBackend(): Promise<string> {
  const token = (await readFile(
    join(tmpdir(), `therese-e2e-${E2E_BACKEND_PORT}`, '.session_token'), 'utf8',
  )).trim();
  if (!token) throw new Error('Jeton privé du backend E2E absent.');
  return token;
}

/** Remplace le canal IPC absent du navigateur par une preuve du secret privé. */
export async function authentifierAmorcageNavigateur(page: Page): Promise<void> {
  await page.route(`${BACKEND_URL}/api/auth/token`, async (route) => {
    await route.continue({
      headers: { ...route.request().headers(), 'X-Therese-Token': await lireJetonPriveBackend() },
    });
  });
}
