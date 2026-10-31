/**
 * Un accord que le moteur refuse d'enregistrer n'est pas une panne réseau
 * (correctifs 0.83, Studio Images).
 *
 * `apiFetch` vide la file des accords avant toute écriture métier. Ce vidage se
 * faisait dans le `try` de `request()`, qui convertit toute exception en
 * « Impossible de contacter le serveur » : un profil changé, une restauration
 * en attente ou une décision invalide s'affichaient comme une coupure réseau.
 * Le message du moteur passe désormais tel quel, sans le statut HTTP de
 * `/api/consents`, qu'aucun appelant ne doit lire comme celui de sa route.
 *
 * Tous les chemins d'erreur de `request()` et d'`apiFetch` sont rejoués avec
 * les vrais modules d'accord ; seul `fetch` est doublé.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { flushConsentDecisions, queueConsentDecision } from '../../lib/consentSync';
import { messageDErreurDuFlux } from '../../lib/messageDErreurDuFlux';
import { apiFetch, ApiError, request } from './core';

type Reponse = { status: number; corps: unknown } | Error | 'suspendu';
let reponses: Record<string, Reponse> = {};
let appels: string[] = [];

function json(corps: unknown, status: number): Response {
  return new Response(JSON.stringify(corps), { status, headers: { 'Content-Type': 'application/json' } });
}

function moteur(): void {
  vi.mocked(globalThis.fetch).mockImplementation(async (entree, init) => {
    const url = new URL(String(entree));
    const cle = `${(init?.method ?? 'GET').toUpperCase()} ${url.pathname}`;
    appels.push(cle);
    const reponse = reponses[cle] ?? { status: 200, corps: { ok: true } };
    if (reponse === 'suspendu') {
      // Comme le vrai fetch : un signal déjà abandonné rejette tout de suite.
      return new Promise((_resolve, rejeter) => {
        const abandonner = () => rejeter(init?.signal?.reason ?? new DOMException('Abandon', 'AbortError'));
        if (init?.signal?.aborted) abandonner();
        else init?.signal?.addEventListener('abort', abandonner);
      });
    }
    if (reponse instanceof Error) throw reponse;
    return json(reponse.corps, reponse.status);
  });
}

function accordEnAttente(): void {
  // Une décision locale à transmettre : c'est elle que l'écriture suivante attend.
  vi.mocked(globalThis.fetch).mockImplementationOnce(async () => {
    throw new TypeError('Failed to fetch');
  });
  queueConsentDecision('images', 'gpt-image-2', true, ['description du visuel']);
}

async function poserUnAccordEnAttente(): Promise<void> {
  accordEnAttente();
  await flushConsentDecisions().catch(() => {});
  moteur();
  appels = [];
}

const GENERER = { method: 'POST', body: JSON.stringify({ prompt: 'Portrait' }) };

describe('request() : un accord refusé par le moteur garde son message', () => {
  beforeEach(async () => {
    vi.mocked(globalThis.fetch).mockReset();
    vi.mocked(globalThis.fetch).mockResolvedValue(json({ grants: [] }, 200));
    await flushConsentDecisions().catch(() => {});
    installLocalStorageStub();
    localStorage.setItem('therese:data-profile', '/profils/test');
    reponses = {};
    appels = [];
    moteur();
  });

  it('profil changé (409) : le message du moteur, sans statut, et rien n’est généré', async () => {
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = { status: 409, corps: { detail: 'Le profil a changé. Reviens au profil concerné avant de réessayer.' } };

    const erreur = await request('/api/images/generate', GENERER).catch(e => e);

    expect(erreur).toMatchObject({ name: 'AccordNonEnregistre', message: 'Le profil a changé. Reviens au profil concerné avant de réessayer.' });
    expect(erreur).not.toBeInstanceOf(ApiError);
    expect((erreur as { status?: number }).status).toBeUndefined();
    expect(appels).toEqual(['POST /api/consents']);
  });

  it('restauration en attente (400 ErreurPourEcran) : le message du moteur', async () => {
    const texte = 'Les accords n’ont pas pu être rétablis après la restauration. Aucun envoi cloud n’est autorisé. Relance la restauration de ta sauvegarde pour reprendre cette étape.';
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = { status: 400, corps: { detail: texte, message: texte } };

    await expect(request('/api/images/generate', GENERER)).rejects.toMatchObject({ name: 'AccordNonEnregistre', message: texte });
    expect(appels).toEqual(['POST /api/consents']);
  });

  it('décision invalide (422) : le champ et la règle, pas une panne réseau', async () => {
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = { status: 422, corps: { code: 'VALIDATION_ERROR', message: 'Données invalides dans la requête', details: [] } };

    await expect(request('/api/images/generate', GENERER)).rejects.toMatchObject({ name: 'AccordNonEnregistre', message: 'Données invalides dans la requête' });
  });

  it('accords d’un profil non identifié : le message local, pas une panne réseau', async () => {
    localStorage.setItem('therese-cloud-consent-pending', JSON.stringify([{ event_id: 'ancien', purpose: 'llm', provider: 'openai',
      granted: false, text_version: '3', data_categories: [], occurred_at: '2026-10-29T00:00:00Z' }]));

    await expect(request('/api/images/generate', GENERER)).rejects.toMatchObject({
      name: 'AccordNonEnregistre', message: expect.stringContaining('profil non identifié') });
    expect(appels).toEqual([]);
  });

  it('moteur injoignable pendant l’accord : reste une panne réseau', async () => {
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = new TypeError('Failed to fetch');

    await expect(request('/api/images/generate', GENERER)).rejects.toMatchObject({
      status: 0, statusText: 'NetworkError', message: 'Impossible de contacter le serveur' });
    expect(appels).toEqual(['POST /api/consents']);
  });

  it('accord acquitté : l’écriture métier part ensuite, une seule fois', async () => {
    await poserUnAccordEnAttente();

    await expect(request('/api/images/generate', GENERER)).resolves.toEqual({ ok: true });
    expect(appels).toEqual(['POST /api/consents', 'POST /api/images/generate']);
  });

  it('les erreurs de la route elle-même ne changent pas', async () => {
    reponses['POST /api/images/generate'] = { status: 500, corps: { detail: 'Le fournisseur a refusé la demande.', code: 'PROVIDER_ERROR' } };
    await expect(request('/api/images/generate', GENERER)).rejects.toMatchObject({
      status: 500, message: 'Le fournisseur a refusé la demande.', code: 'PROVIDER_ERROR' });

    reponses['POST /api/images/generate'] = new TypeError('Failed to fetch');
    await expect(request('/api/images/generate', GENERER)).rejects.toMatchObject({ status: 0, message: 'Impossible de contacter le serveur' });

    reponses['POST /api/images/generate'] = 'suspendu';
    await expect(request('/api/images/generate', { ...GENERER, timeoutMs: 20 })).rejects.toMatchObject({ name: 'TimeoutError' });

    const abandon = new AbortController();
    const enCours = request('/api/images/generate', { ...GENERER, signal: abandon.signal });
    abandon.abort(new DOMException('Annulé', 'AbortError'));
    await expect(enCours).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('une lecture n’attend pas la file des accords', async () => {
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = { status: 409, corps: { detail: 'Le profil a changé.' } };

    await expect(request('/api/images/status')).resolves.toEqual({ ok: true });
    expect(appels).toEqual(['GET /api/images/status']);
  });
});

describe('apiFetch() appelé directement (flux du chat, Board, agents)', () => {
  beforeEach(async () => {
    vi.mocked(globalThis.fetch).mockReset();
    vi.mocked(globalThis.fetch).mockResolvedValue(json({ grants: [] }, 200));
    await flushConsentDecisions().catch(() => {});
    installLocalStorageStub();
    localStorage.setItem('therese:data-profile', '/profils/test');
    reponses = {};
    appels = [];
    moteur();
  });

  it('un refus du moteur porte son message jusqu’à la bulle', async () => {
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = { status: 409, corps: { detail: 'Le profil a changé.' } };

    const erreur = await apiFetch('http://127.0.0.1:17293/api/chat/send', { method: 'POST' }).catch(e => e);

    expect(erreur).toMatchObject({ name: 'AccordNonEnregistre', message: 'Le profil a changé.' });
    expect(messageDErreurDuFlux(erreur)).toBe('Le profil a changé.');
  });

  it('une coupure pendant l’accord reste une coupure (« Réponse interrompue »)', async () => {
    await poserUnAccordEnAttente();
    reponses['POST /api/consents'] = new TypeError('Failed to fetch');

    const erreur = await apiFetch('http://127.0.0.1:17293/api/chat/send', { method: 'POST' }).catch(e => e);

    expect(messageDErreurDuFlux(erreur)).toMatch(/^Réponse interrompue/);
  });
});
