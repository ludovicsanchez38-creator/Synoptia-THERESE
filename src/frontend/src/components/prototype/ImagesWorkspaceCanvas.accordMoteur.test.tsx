/**
 * Studio Images et accord enregistré dans le moteur (correctifs 0.83, parcours e2e 08).
 *
 * Depuis le lot confidentialité, le moteur refuse une génération sans accord
 * « images » enregistré pour ce fournisseur (`exiger_accord`), et le client
 * vide la file des accords avant toute écriture métier (`apiFetch`). Le
 * parcours 08 refusait ce `POST /api/consents` comme une écriture interdite :
 * la génération ne partait jamais. Le parcours bouchonne désormais cet appel ;
 * ce test prouve, avec les vrais modules d'accord et le vrai client HTTP (seul
 * `fetch` est doublé), que l'application envoie le bon accord, avant la
 * génération, et qu'elle ne génère rien tant que le moteur ne l'a pas acquitté.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { flushConsentDecisions } from '../../lib/consentSync';
import { CLOUD_CONSENT_KEY } from '../../lib/consent';
import { ImagesWorkspaceCanvas } from './ImagesWorkspaceCanvas';

interface Appel { methode: string; chemin: string; corps: Record<string, unknown> | null }

const IMAGE = {
  id: 'image-generee', provider: 'gpt-image-2', file_name: 'visuel.png', file_size: 1200,
  mime_type: 'image/png', created_at: '2026-10-30T10:00:00Z', prompt: 'Portrait éditorial de Thérèse',
  download_url: '/api/images/download/image-generee',
};

type Refus = { status: number; corps: unknown } | 'reseau' | null;
let appels: Appel[] = [];
let refusAccord: Refus = null;
let refusGeneration: Refus = null;
const PROFIL_CHANGE = 'Le profil a changé. Reviens au profil concerné avant de réessayer.';
const RESTAURATION = 'Les accords n’ont pas pu être rétablis après la restauration. Aucun envoi cloud n’est autorisé. Relance la restauration de ta sauvegarde pour reprendre cette étape.';

function refuser(refus: Refus): Response | null {
  if (refus === 'reseau') throw new TypeError('Failed to fetch');
  return refus ? reponse(refus.corps, refus.status) : null;
}

function reponse(corps: unknown, status = 200): Response {
  return new Response(JSON.stringify(corps), { status, headers: { 'Content-Type': 'application/json' } });
}

function moteur(): void {
  vi.mocked(globalThis.fetch).mockImplementation(async (entree, init) => {
    const url = new URL(String(entree));
    const methode = (init?.method ?? 'GET').toUpperCase();
    appels.push({ methode, chemin: url.pathname, corps: init?.body ? JSON.parse(String(init.body)) : null });
    if (url.pathname === '/api/images/status') {
      return reponse({ openai_available: true, gemini_available: false, fal_available: false, active_provider: 'gpt-image-2' });
    }
    if (url.pathname === '/api/images/list') return reponse({ images: [], total: 0 });
    if (url.pathname === '/api/consents' && methode === 'POST') {
      return refuser(refusAccord) ?? reponse({ grants: [], history: [] });
    }
    if (url.pathname === '/api/images/generate' && methode === 'POST') return refuser(refusGeneration) ?? reponse(IMAGE);
    return reponse({ detail: 'Introuvable' }, 404);
  });
}

function ecritures(): string[] {
  return appels.filter(a => a.methode !== 'GET').map(a => `${a.methode} ${a.chemin}`);
}

async function preparer(): Promise<void> {
  render(<ImagesWorkspaceCanvas onClose={vi.fn()} />);
  await waitFor(() => expect(screen.getByRole('radio', { name: /GPT Image 2/ })).toBeChecked());
  fireEvent.change(screen.getByLabelText('Description du visuel'), { target: { value: 'Portrait éditorial de Thérèse' } });
  fireEvent.click(screen.getByRole('button', { name: 'Préparer la génération' }));
}

describe('Studio Images : l’accord part au moteur avant la génération', () => {
  beforeEach(async () => {
    await flushConsentDecisions().catch(() => {});
    installLocalStorageStub();
    localStorage.setItem('therese:data-profile', '/profils/test');
    appels = [];
    refusAccord = null;
    refusGeneration = null;
    vi.mocked(globalThis.fetch).mockReset();
    moteur();
  });

  it('premier usage : un seul accord « images » complet, puis la génération', async () => {
    await preparer();
    expect(screen.getByText(/tu consens à transmettre ces données à GPT Image 2/)).toBeInTheDocument();
    expect(ecritures()).toEqual([]);

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' })); });

    await waitFor(() => expect(screen.getByTestId('selected-generated-image')).toHaveTextContent('Portrait éditorial de Thérèse'));
    expect(ecritures()).toEqual(['POST /api/consents', 'POST /api/images/generate']);
    expect(appels.find(a => a.chemin === '/api/consents')!.corps).toEqual({
      event_id: expect.stringMatching(/^[a-zA-Z0-9-]+$/),
      purpose: 'images',
      provider: 'gpt-image-2',
      granted: true,
      text_version: '3',
      data_categories: ['description du visuel', 'format', 'qualité'],
      occurred_at: expect.stringMatching(/Z$/),
      data_profile: '/profils/test',
    });
    expect(appels.find(a => a.chemin === '/api/images/generate')!.corps).toMatchObject({
      prompt: 'Portrait éditorial de Thérèse', provider: 'gpt-image-2',
    });
  });

  it('accord refusé par le moteur : son message, rien n’est généré, et « Réessayer » repart avec la même décision', async () => {
    refusAccord = { status: 409, corps: { detail: PROFIL_CHANGE } };
    await preparer();

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' })); });

    expect(await screen.findByText('Génération impossible')).toBeInTheDocument();
    expect(screen.getByText(PROFIL_CHANGE)).toBeInTheDocument();
    expect(screen.queryByText('Impossible de contacter le serveur')).not.toBeInTheDocument();
    expect(ecritures()).toEqual(['POST /api/consents']);

    refusAccord = null;
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' })); });

    await waitFor(() => expect(screen.getByTestId('selected-generated-image')).toHaveTextContent('Portrait éditorial de Thérèse'));
    expect(ecritures()).toEqual(['POST /api/consents', 'POST /api/consents', 'POST /api/images/generate']);
    const [premier, second] = appels.filter(a => a.chemin === '/api/consents');
    expect(second.corps!.event_id).toBe(premier.corps!.event_id);
  });

  it.each([
    ['accord refusé pendant une restauration (400)', { accord: { status: 400, corps: { detail: RESTAURATION, message: RESTAURATION } } }, RESTAURATION, ['POST /api/consents']],
    ['moteur injoignable pendant l’accord', { accord: 'reseau' as const }, 'Impossible de contacter le serveur', ['POST /api/consents']],
    ['génération refusée par le fournisseur (500)', { generation: { status: 500, corps: { detail: 'Le fournisseur a refusé la demande.' } } }, 'Le fournisseur a refusé la demande.', ['POST /api/consents', 'POST /api/images/generate']],
    ['moteur injoignable pendant la génération', { generation: 'reseau' as const }, 'Impossible de contacter le serveur', ['POST /api/consents', 'POST /api/images/generate']],
  ])('%s : le bon message, puis « Réessayer » aboutit', async (_nom, refus: { accord?: Refus; generation?: Refus }, message, ecrit) => {
    refusAccord = refus.accord ?? null;
    refusGeneration = refus.generation ?? null;
    await preparer();

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' })); });

    expect(await screen.findByText('Génération impossible')).toBeInTheDocument();
    expect(screen.getByText(message)).toBeInTheDocument();
    expect(ecritures()).toEqual(ecrit);

    refusAccord = null;
    refusGeneration = null;
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' })); });
    await waitFor(() => expect(screen.getByTestId('selected-generated-image')).toHaveTextContent('Portrait éditorial de Thérèse'));
    expect(screen.queryByText('Génération impossible')).not.toBeInTheDocument();
  });

  it('accord déjà enregistré : la génération part seule, sans nouvelle décision', async () => {
    localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify({ version: '2', grants: { 'images:gpt-image-2': {
      purpose: 'images', provider: 'gpt-image-2', timestamp: '2026-10-01T00:00:00Z',
      dataCategories: ['description du visuel', 'format', 'qualité'], textVersion: '3' } } }));
    await preparer();
    expect(screen.queryByText(/tu consens à transmettre/)).not.toBeInTheDocument();

    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' })); });

    await waitFor(() => expect(screen.getByTestId('selected-generated-image')).toBeInTheDocument());
    expect(ecritures()).toEqual(['POST /api/images/generate']);
  });

  it('« Annuler » ne transmet ni accord ni génération', async () => {
    await preparer();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

    expect(screen.getByRole('button', { name: 'Préparer la génération' })).toBeInTheDocument();
    expect(ecritures()).toEqual([]);
  });
});
