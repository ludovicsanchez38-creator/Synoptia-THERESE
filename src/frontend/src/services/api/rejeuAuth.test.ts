/**
 * Campagne dix personas : après une relance du moteur, l'application est morte
 * sans le dire.
 *
 * Tauri relance le sidecar (jusqu'à 3 fois, `lib.rs:375`). Chaque démarrage
 * génère un NOUVEAU token de session. Le frontend, lui, chargeait le sien une
 * seule fois et ne traitait aucun 401 : tout retournait 401 pendant que le
 * bandeau annonçait que le moteur était reparti. L'écrivaine a fini sa session
 * ainsi et a cessé d'essayer.
 *
 * Deux corrections de la relecture de design, décisives :
 *
 *  - Mon marqueur initial était un en-tête de réponse. Il n'aurait JAMAIS
 *    fonctionné : `expose_headers` ne contient que `Content-Disposition`, donc
 *    `headers.get()` rend `null` dans la webview. Les tests Node l'auraient
 *    laissé passer. On lit `code: "UNAUTHORIZED"` dans le corps, qui n'existe
 *    qu'au middleware d'auth (`main.py:712`) — les autres 401 (Gmail, Groq,
 *    Sheets) sont des `{"detail": ...}`.
 *  - Je voulais exclure le streaming. Faux : le 401 du middleware arrive AVANT
 *    l'entrée dans la route, donc aucune génération n'a démarré et le message
 *    utilisateur n'est pas encore persisté (`chat.py:1160`). Et la branche sans
 *    délai — `timeoutMs == null` — est précisément celle du chat.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiFetch, initializeAuth, _reinitialiserAuthPourTests } from './core';

const TOKEN_APRES = 'jeton-apres-relance';

function reponse401DuMiddleware() {
  return new Response(
    JSON.stringify({ code: 'UNAUTHORIZED', message: 'Token de session invalide ou manquant' }),
    { status: 401, headers: { 'Content-Type': 'application/json' } },
  );
}

function reponse401Metier() {
  // Gmail, Groq, Sheets : `{"detail": ...}`, pas notre middleware.
  return new Response(JSON.stringify({ detail: 'Invalid credentials' }), {
    status: 401,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('Rejeu du jeton après une relance du moteur', () => {
  beforeEach(async () => {
    _reinitialiserAuthPourTests();
    vi.restoreAllMocks();
  });

  it('rejoue une fois quand le middleware refuse le jeton, et réussit', async () => {
    let appels = 0;
    globalThis.fetch = vi.fn(async (url: RequestInfo | URL) => {
      const cible = String(url);
      if (cible.includes('/api/auth/token')) {
        return new Response(JSON.stringify({ token: TOKEN_APRES }), { status: 200 });
      }
      appels += 1;
      if (appels === 1) return reponse401DuMiddleware();
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    }) as never;

    await initializeAuth();
    const reponse = await apiFetch('http://127.0.0.1:17293/api/dashboard/today');

    expect(reponse.status).toBe(200);
    expect(appels).toBe(2);
  });

  it('rejoue aussi sur la branche SANS délai — celle du chat en flux', async () => {
    let appels = 0;
    globalThis.fetch = vi.fn(async (url: RequestInfo | URL) => {
      const cible = String(url);
      if (cible.includes('/api/auth/token')) {
        return new Response(JSON.stringify({ token: TOKEN_APRES }), { status: 200 });
      }
      appels += 1;
      if (appels === 1) return reponse401DuMiddleware();
      return new Response('data: {}', { status: 200 });
    }) as never;

    await initializeAuth();
    // timeoutMs: null = le chemin de `streamMessage`, du Board, des agents.
    const reponse = await apiFetch('http://127.0.0.1:17293/api/chat/send', { timeoutMs: null });

    expect(reponse.status).toBe(200);
    expect(appels).toBe(2);
  });

  it('ne rejoue PAS un 401 métier (Gmail, Groq, Sheets)', async () => {
    let appels = 0;
    globalThis.fetch = vi.fn(async (url: RequestInfo | URL) => {
      if (String(url).includes('/api/auth/token')) {
        return new Response(JSON.stringify({ token: TOKEN_APRES }), { status: 200 });
      }
      appels += 1;
      return reponse401Metier();
    }) as never;

    await initializeAuth();
    const reponse = await apiFetch('http://127.0.0.1:17293/api/email/messages');

    expect(reponse.status).toBe(401);
    expect(appels).toBe(1);
  });

  it('ne rejoue qu’une seule fois : un second refus remonte', async () => {
    // Le plafond n'est pas décoratif : si le rejeu se rappelait lui-même
    // (`apiFetch` au lieu de `envoyer`), le serveur répondant toujours 401,
    // la récursion serait infinie. Sans borne, le test ne rougirait pas — il
    // BLOQUERAIT, et un test qui bloque est un mauvais signal. On le fait
    // échouer proprement. (Trouvé par la preuve par sabotage.)
    const PLAFOND = 5;
    let appels = 0;
    globalThis.fetch = vi.fn(async (url: RequestInfo | URL) => {
      if (String(url).includes('/api/auth/token')) {
        return new Response(JSON.stringify({ token: TOKEN_APRES }), { status: 200 });
      }
      appels += 1;
      if (appels > PLAFOND) {
        throw new Error(`Boucle de rejeu : plus de ${PLAFOND} tentatives`);
      }
      return reponse401DuMiddleware();
    }) as never;

    await initializeAuth();
    const reponse = await apiFetch('http://127.0.0.1:17293/api/dashboard/today');

    expect(reponse.status).toBe(401);
    expect(appels).toBe(2); // l'appel initial + un seul rejeu
  });

  it('recharge le jeton avec un fetch brut, sans repasser par apiFetch', async () => {
    // Sinon le rafraîchissement déclencherait lui-même un rejeu : récursion.
    //
    // L'assertion est faite APRÈS coup, hors du mock : `rechargerLeJeton`
    // enveloppe son appel dans un try/catch, qui avalerait silencieusement une
    // assertion jetée depuis le mock — le test passerait quoi qu'il arrive.
    // (Trouvé par la preuve par sabotage : remplacer le fetch brut par apiFetch
    // ne faisait pas rougir ce test.)
    const jetonsVusSurLeRafraichissement: (string | null)[] = [];
    let appelsDashboard = 0;
    globalThis.fetch = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const cible = String(url);
      if (cible.includes('/api/auth/token')) {
        jetonsVusSurLeRafraichissement.push(new Headers(init?.headers).get('X-Therese-Token'));
        return new Response(JSON.stringify({ token: TOKEN_APRES }), { status: 200 });
      }
      appelsDashboard += 1;
      return appelsDashboard === 1
        ? reponse401DuMiddleware()
        : new Response('{}', { status: 200 });
    }) as never;

    await initializeAuth();
    jetonsVusSurLeRafraichissement.length = 0; // on ne juge que le rafraîchissement du rejeu
    await apiFetch('http://127.0.0.1:17293/api/dashboard/today');

    expect(jetonsVusSurLeRafraichissement.length).toBe(1);
    // Le rafraîchissement ne doit PAS porter l'ancien jeton périmé : s'il le
    // portait, c'est qu'il est passé par apiFetch.
    expect(jetonsVusSurLeRafraichissement[0]).toBeNull();
  });
});
