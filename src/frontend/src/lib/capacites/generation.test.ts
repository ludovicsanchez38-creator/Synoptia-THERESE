/**
 * Le contrôle de génération : la moitié frontend.
 *
 * L'enjeu du test n'est pas le SHA-256, c'est la CANONICITÉ : si la
 * sérialisation dépendait de l'ordre des clés, deux manifestes identiques
 * produiraient deux empreintes différentes selon le parseur, et le contrôle
 * crierait à la divergence en permanence — un contrôle qui crie tout le temps
 * finit débranché.
 */
import { describe, expect, it, vi, afterEach } from 'vitest';

import {
  controlerGenerationAuDemarrage,
  empreinteLocale,
  serialisationCanonique,
  verifierGeneration,
} from './generation';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('La sérialisation est canonique', () => {
  it('ignore l’ordre des clés', () => {
    expect(serialisationCanonique({ b: 1, a: [{ d: 2, c: 3 }] })).toBe(
      serialisationCanonique({ a: [{ c: 3, d: 2 }], b: 1 }),
    );
  });

  it('distingue deux contenus différents', () => {
    expect(serialisationCanonique({ a: 1 })).not.toBe(
      serialisationCanonique({ a: 2 }),
    );
  });

  it('préserve l’ordre des tableaux, qui est significatif', () => {
    // L'ordre des `entrees` d'une capacité est un contenu, pas un artefact.
    expect(serialisationCanonique([1, 2])).not.toBe(serialisationCanonique([2, 1]));
  });
});

describe('Le contrôle signale sans jamais bloquer', () => {
  it('déclare une divergence quand les empreintes diffèrent', async () => {
    const avertir = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ empreinte: 'autre-generation' }),
    } as unknown as Response);

    const verdict = await verifierGeneration('http://localhost:17293', fetcher);

    expect(verdict.coherent).toBe(false);
    expect(avertir).toHaveBeenCalledOnce();
  });

  it('reste cohérent quand les deux côtés portent le même manifeste', async () => {
    const locale = await empreinteLocale();
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ empreinte: locale }),
    } as unknown as Response);

    const verdict = await verifierGeneration('http://localhost:17293', fetcher);

    expect(verdict.coherent).toBe(true);
  });

  it('un backend injoignable ne produit ni erreur ni fausse alerte', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('refusé'));

    const verdict = await verifierGeneration('http://localhost:17293', fetcher);

    expect(verdict.coherent).toBe(true);
    expect(verdict.distante).toBe('inconnue');
  });
});

describe('Un sidecar sans manifeste n’est pas une divergence de packaging', () => {
  it('signale la bonne cause, pas la mauvaise', async () => {
    // « absent » = le backend n'a pas PU lire son manifeste (fail-open).
    // L'annoncer comme un écart de générations enverrait le diagnostic dans
    // la mauvaise direction : on chercherait un problème de build qui
    // n'existe pas.
    const avertir = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ empreinte: 'absent' }),
    } as unknown as Response);

    const verdict = await verifierGeneration('http://localhost:17293', fetcher);

    expect(verdict.coherent).toBe(false);
    expect(avertir).toHaveBeenCalledOnce();
    const message = String(avertir.mock.calls[0][0]);
    expect(message).toContain('pas pu lire');
    expect(message).not.toContain('packagés à des moments différents');
  });
});

describe('Le contrôle attend un jeton vérifiable avant de conclure', () => {
  /**
   * Seconde passe de revue : sur un démarrage lent, l'auth échouait en
   * silence, le contrôle prenait un 401 « cohérent », et ne recommençait
   * jamais. Le contrat : réessayer borné, puis dire honnêtement que le
   * contrôle n'a pas eu lieu — jamais conclure « cohérent » sans preuve.
   */
  it('ne vérifie rien et le dit quand le jeton ne vient jamais', async () => {
    const avertir = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const verifier = vi.fn();

    const verdict = await controlerGenerationAuDemarrage({
      initApiBase: vi.fn().mockResolvedValue(undefined),
      initializeAuth: vi.fn().mockResolvedValue(undefined),
      getSessionToken: () => null,
      apiBase: () => 'http://localhost:17293',
      verifier,
      tentatives: 3,
      attendreMs: () => Promise.resolve(),
    });

    expect(verdict).toBeNull();
    expect(verifier).not.toHaveBeenCalled();
    expect(String(avertir.mock.calls.at(-1)?.[0])).toContain('non exécuté');
  });

  it('vérifie dès que le jeton arrive, même tardivement', async () => {
    let jeton: string | null = null;
    const initializeAuth = vi.fn().mockImplementation(async () => {
      if (initializeAuth.mock.calls.length >= 3) jeton = 'jeton-tardif';
    });
    const verifier = vi.fn().mockResolvedValue({
      coherent: true, locale: 'a', distante: 'a',
    });

    const verdict = await controlerGenerationAuDemarrage({
      initApiBase: vi.fn().mockResolvedValue(undefined),
      initializeAuth,
      getSessionToken: () => jeton,
      apiBase: () => 'http://localhost:17293',
      verifier,
      tentatives: 5,
      attendreMs: () => Promise.resolve(),
    });

    expect(verifier).toHaveBeenCalledExactlyOnceWith('http://localhost:17293');
    expect(verdict?.coherent).toBe(true);
    expect(initializeAuth).toHaveBeenCalledTimes(3);
  });
});
