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
