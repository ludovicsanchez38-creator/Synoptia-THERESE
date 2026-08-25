/**
 * 0.47 - Annuler une délibération passe par le chemin canonique.
 *
 * Un abort() local coupait le transport et rien d'autre : le backend
 * continuait de consulter les conseillers (constat du plan 0.42, jamais
 * corrigé jusqu'ici). Le contrat : demander l'arrêt au traitement durable
 * (generation_id reçu en premier événement SSE), PUIS fermer le transport.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/processingTasks', () => ({
  annulerTraitement: vi.fn(),
}));

import { annulerTraitement } from '../../services/api/processingTasks';
import { annulerDeliberation } from './annulerDeliberation';

describe('annulerDeliberation', () => {
  beforeEach(() => {
    vi.mocked(annulerTraitement).mockReset();
    vi.mocked(annulerTraitement).mockResolvedValue(undefined as never);
  });

  it('demande l’arrêt canonique PUIS coupe le transport', async () => {
    const ordre: string[] = [];
    vi.mocked(annulerTraitement).mockImplementation(async () => {
      ordre.push('canonique');
      return undefined as never;
    });

    await annulerDeliberation('traitement-42', () => ordre.push('abort'));

    expect(annulerTraitement).toHaveBeenCalledWith('traitement-42');
    expect(ordre).toEqual(['canonique', 'abort']);
  });

  it('coupe quand même le transport sans identifiant de traitement', async () => {
    let coupe = false;

    await annulerDeliberation(null, () => { coupe = true; });

    expect(annulerTraitement).not.toHaveBeenCalled();
    expect(coupe).toBe(true);
  });

  it('coupe quand même le transport si l’appel canonique échoue', async () => {
    vi.mocked(annulerTraitement).mockRejectedValue(new Error('backend down'));
    let coupe = false;

    await annulerDeliberation('traitement-42', () => { coupe = true; });

    expect(coupe).toBe(true);
  });
});
