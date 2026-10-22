import { expect, it } from 'vitest';
import { consequencesDeLaSuppression } from './consequencesDeLaSuppression';
import type { EnsembleDuProjet } from '../services/api/memory';
const vide = { total: 0, elements: [] };
const ensemble: EnsembleDuProjet = { conversations: vide, documents: vide,
  taches: { ...vide, ouvertes: 0, en_retard: 0 }, contacts: { ...vide, ranges: 0 },
  livrables: { total: 0 }, fichiers: { total: 0, deposes: 0, indexes_sur_place: 0 },
  dossier_synchronise: { rattache: false }, rendez_vous: { total: 0 }, sous_dossiers: { total: 0 },
  planning: { total: 0, ressources: 0, calculs: 0 }, indisponibles: [],
  memory_cards: { total: 2 }, activities: { total: 3 } };
it('annonce les fiches, le journal et les notes avant la suppression du dossier', () => {
  expect(consequencesDeLaSuppression(ensemble)?.join(' ')).toContain('2 fiches mémoire');
  expect(consequencesDeLaSuppression(ensemble)?.join(' ')).toContain('3 traces du journal ou notes de rendez-vous');
  expect(consequencesDeLaSuppression({ ...ensemble, activities: null })).toBeNull();
});
