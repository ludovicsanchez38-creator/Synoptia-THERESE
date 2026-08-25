/**
 * B0 (0.48) — le registre canonique des cartes du tiroir.
 *
 * Le manifeste référence des cartes par id (`binding: {registre: 'tiroir',
 * carte}`) ; ce test garantit que toute carte référencée existe, et que
 * chacune des 30 cartes du Centre a une destination résoluble — vue connue,
 * action du registre, scénario connu ou destination spécialisée assumée.
 */
import { describe, expect, it } from 'vitest';

import { APP_ACTIONS } from '../actionRegistry';
import { APP_VIEWS } from '../../stores/navigationStore';
import { CARTES, carteIds } from './cartes';
import { POINTS_ENTREE } from './manifeste';

const SCENARIOS_CONNUS = ['today', 'memory', 'email', 'meeting', 'invoice', 'board', 'atelier'];
const KINDS_SPECIALISES = [
  'prompt', 'calculator', 'deliverables', 'images', 'follow-ups', 'voice',
];

describe('Le registre canonique des cartes', () => {
  it('toute carte référencée par le manifeste existe', () => {
    const referencees = POINTS_ENTREE
      .filter((p) => p.binding.registre === 'tiroir')
      .map((p) => (p.binding as { registre: 'tiroir'; carte: string }).carte);

    expect(referencees.length).toBeGreaterThanOrEqual(6);
    const inconnues = referencees.filter((c) => !carteIds.includes(c));
    expect(inconnues).toEqual([]);
  });

  it('chaque carte du tiroir a une destination résoluble', () => {
    const actionIds = APP_ACTIONS.map((a) => a.id);
    const injustifiables: string[] = [];

    for (const carte of CARTES) {
      const scenarioOk = carte.scenario !== undefined
        && SCENARIOS_CONNUS.includes(carte.scenario);
      const d = carte.destination;
      const destinationOk = d !== undefined && (
        (d.kind === 'view' && (APP_VIEWS as readonly string[]).includes(d.view))
        || (d.kind === 'action' && actionIds.includes(d.action))
        || KINDS_SPECIALISES.includes(d.kind)
        || (d.kind === 'pending' && d.reason.length > 0)
      );
      if (!scenarioOk && !destinationOk) {
        injustifiables.push(carte.id);
      }
    }
    expect(injustifiables).toEqual([]);
  });

  it('aucun id de carte en double', () => {
    expect(new Set(carteIds).size).toBe(carteIds.length);
  });
});
