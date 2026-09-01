import { describe, expect, it } from 'vitest';

import type { TodayDashboard } from '../../services/api/dashboard';
import { buildTodayAttentionItems } from './prototypeReadModels';

/**
 * 01/09/2026. Une réponse de tableau de bord privée d'une seule liste faisait
 * tomber TOUTE l'application sur son écran « Oups ! » : `data.due_follow_ups`
 * valait `undefined`, et `.filter` sur `undefined` remonte jusqu'au garde-fou
 * d'erreur de React. Trouvé parce qu'un test de bout en bout bouchonnait
 * `/api/dashboard/today` sans ce champ — un serveur d'une version antérieure,
 * une réponse tronquée ou un proxy produiraient la même chose.
 *
 * Le brief doit afficher ce qu'il a reçu, pas s'effondrer sur ce qui manque.
 */
describe('buildTodayAttentionItems face à une réponse incomplète', () => {
  const socle = {
    date: '2026-09-01',
    events: [],
    urgent_tasks: [],
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    summary: {
      events_count: 0,
      tasks_count: 0,
      follow_ups_count: 0,
      invoices_count: 0,
      prospects_count: 0,
    },
  } satisfies TodayDashboard;

  const listes = [
    'events',
    'urgent_tasks',
    'due_follow_ups',
    'overdue_invoices',
    'stale_prospects',
  ] as const;

  for (const manquante of listes) {
    it(`ne jette pas quand « ${manquante} » est absente de la réponse`, () => {
      const ampute = { ...socle };
      delete (ampute as Record<string, unknown>)[manquante];

      expect(() => buildTodayAttentionItems(ampute as TodayDashboard)).not.toThrow();
    });
  }

  it('rend quand même les éléments des listes présentes', () => {
    const partiel = {
      ...socle,
      urgent_tasks: [
        { id: 't1', title: 'Relancer', due_date: '2026-08-01', priority: 'high', status: 'todo' },
      ],
    } as unknown as TodayDashboard;
    delete (partiel as unknown as Record<string, unknown>).due_follow_ups;

    const items = buildTodayAttentionItems(partiel);
    expect(items.map((i) => i.title)).toContain('Relancer');
  });
});
