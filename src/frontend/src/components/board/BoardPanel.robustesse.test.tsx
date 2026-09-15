/**
 * J0 (31/07/2026) - Le Board ne doit pas casser quand `fetch` ne rend pas de promesse.
 *
 * `checkOllama` était le SEUL appel `fetch` direct de tout le frontend (tout
 * le reste passe par `services/api`). Il enchaînait `.then()` sur le retour de
 * `fetch` sans garde : si `fetch` rendait autre chose qu'une promesse, ou
 * levait de façon synchrone, l'effet de montage jetait une TypeError NON
 * CAPTURÉE. Le `.catch()` en fin de chaîne ne protège que du rejet ASYNCHRONE.
 *
 * Depuis B-842 (cycle 9), le Board sonde Ollama par `api.getOllamaStatus()`,
 * dont le `fetch` sous-jacent est celui de `services/api` : ce test garde la
 * même exigence (le montage ne lève jamais) avec le vrai client HTTP.
 *
 * Symptôme qui a mené ici : au run complet de la suite, monter le Board depuis
 * la coque faisait échouer des tests de navigation sans rapport - le setup
 * global (`src/test/setup.ts`) remplace `fetch` par un `vi.fn()` nu, qui rend
 * `undefined`. Au-delà du bruit de test, c'est un défaut réel de robustesse :
 * un environnement où `fetch` est absent ou instrumenté fait planter le
 * montage d'une vue entière.
 */
import { render } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { BoardPanel } from './BoardPanel';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    streamDeliberation: vi.fn(),
    listBoardDecisions: vi.fn().mockResolvedValue([]),
    getBoardDecision: vi.fn(),
    deleteBoardDecision: vi.fn(),
  };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));
vi.mock('./DeliberationView', () => ({ DeliberationView: () => null }));
vi.mock('./AdvisorArcLayout', () => ({ AdvisorArcLayout: () => null }));

describe('BoardPanel - robustesse du sondage Ollama', () => {
  const erreurs: unknown[] = [];
  const capter = (evenement: ErrorEvent) => {
    erreurs.push(evenement.error ?? evenement.message);
    evenement.preventDefault();
  };

  beforeEach(() => {
    erreurs.length = 0;
    window.addEventListener('error', capter);
  });

  afterEach(() => {
    window.removeEventListener('error', capter);
  });

  it('se monte sans lever quand fetch ne rend pas de promesse', () => {
    // Exactement ce que fait le setup global de la suite.
    vi.stubGlobal('fetch', vi.fn());

    render(<BoardPanel isOpen onClose={() => {}} />);

    expect(erreurs).toEqual([]);
    vi.unstubAllGlobals();
  });

  it('se monte sans lever quand fetch échoue de façon synchrone', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => {
        throw new Error('réseau indisponible');
      })
    );

    render(<BoardPanel isOpen onClose={() => {}} />);

    expect(erreurs).toEqual([]);
    vi.unstubAllGlobals();
  });
});
