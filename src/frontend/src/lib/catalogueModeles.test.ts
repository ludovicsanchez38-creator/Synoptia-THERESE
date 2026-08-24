/**
 * Le catalogue vient du backend, la décoration reste locale.
 *
 * L'enjeu : quatre copies frontend divergeaient (l'onboarding proposait
 * encore gpt-5.3-codex, retiré partout ailleurs). La liste doit venir de la
 * route, et un échec réseau doit rendre null - jamais une liste vide qui
 * viderait le sélecteur.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

import { _viderLeCache, chargerCatalogue, decorer } from './catalogueModeles';

afterEach(() => {
  _viderLeCache();
  vi.restoreAllMocks();
});

describe('La liste vient du backend', () => {
  it('sert les modèles de la route, décorés', async () => {
    const fetcher = vi.fn().mockResolvedValue({ models: ['glm-5.3', 'glm-x-inconnu'] });

    const modeles = await chargerCatalogue('glm', fetcher);

    expect(modeles?.map((m) => m.id)).toEqual(['glm-5.3', 'glm-x-inconnu']);
    expect(modeles?.[0].name).toBe('GLM 5.3');
    // Un id sans décoration s'affiche tel quel : un nouveau modèle publié
    // par le backend apparaît sans MAJ frontend, il n'est jamais masqué.
    expect(modeles?.[1].name).toBe('glm-x-inconnu');
  });

  it('ne rappelle pas la route deux fois pour le même fournisseur', async () => {
    const fetcher = vi.fn().mockResolvedValue({ models: ['kimi-k3'] });

    await chargerCatalogue('kimi', fetcher);
    await chargerCatalogue('kimi', fetcher);

    expect(fetcher).toHaveBeenCalledOnce();
  });

  it('rend null sur échec : l’appelant garde sa liste de repli', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('backend muet'));

    expect(await chargerCatalogue('qwen', fetcher)).toBeNull();
  });

  it('rend null sur liste vide : un sélecteur vide n’est pas un catalogue', async () => {
    const fetcher = vi.fn().mockResolvedValue({ models: [] });

    expect(await chargerCatalogue('minimax', fetcher)).toBeNull();
  });
});

describe('La décoration', () => {
  it('préserve la casse des identifiants (MiniMax y tient)', () => {
    expect(decorer(['MiniMax-M3'])[0]).toEqual({
      id: 'MiniMax-M3', name: 'MiniMax M3', badge: 'Recommandé',
    });
  });
});
