/**
 * Entrée 8 du plan du 28/08 : le brief ouvre l'objet, pas le module.
 *
 * La contradiction la plus audible de l'application : « Tu peux agir ici, sans
 * chercher le bon module » s'affiche trois lignes au-dessus d'un appel qui
 * ouvre le module. Sur « Relancer Dupont », un clic mène à la boîte entière,
 * et il faut y retrouver Dupont à la main.
 *
 * L'identité existe pourtant : chaque item la calcule pour fabriquer sa clé,
 * puis la jette. On la garde désormais à part, telle quelle.
 */
import { describe, expect, it } from 'vitest';

import { buildTodayAttentionItems } from './prototypeReadModels';

const AUJOURDHUI = '2026-08-28';

function brief(partiel: Record<string, unknown> = {}) {
  return {
    date: AUJOURDHUI,
    events: [],
    urgent_tasks: [],
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
    ...partiel,
  } as never;
}

describe('Entrée 8 : chaque item du brief sait quel objet il désigne', () => {
  it('une tâche porte son identifiant, pas seulement sa clé', () => {
    const [item] = buildTodayAttentionItems(
      brief({ urgent_tasks: [{ id: 't-9', title: 'Rappeler Paul', due_date: null, priority: 'high', status: 'todo' }] }),
    );
    expect(item.cibleId).toBe('t-9');
  });

  it('une relance porte l’identifiant de son message', () => {
    const [item] = buildTodayAttentionItems(
      brief({
        due_follow_ups: [{
          id: 'f-1', due_date: AUJOURDHUI, note: null,
          email_subject: 'Devis', email_from: 'Paul',
          contact_id: 'c-1', contact_name: 'Paul Rivière',
          email_message_id: 'msg-77',
        }],
      }),
    );
    // C'est le message qu'on veut rouvrir, pas le contact ni la relance.
    expect(item.cibleId).toBe('msg-77');
  });

  it('un prospect porte son contact', () => {
    const [item] = buildTodayAttentionItems(
      brief({ stale_prospects: [{ id: 'c-42', display_name: 'Alpha SA', stage: 'prospect', last_interaction: null }] }),
    );
    expect(item.cibleId).toBe('c-42');
  });

  it('une facture et un événement aussi', () => {
    const [facture] = buildTodayAttentionItems(
      brief({ overdue_invoices: [{ id: 'inv-3', invoice_number: 'F-2026-003', client_name: 'Beta', total_ttc: 100, due_date: AUJOURDHUI }] }),
    );
    expect(facture.cibleId).toBe('inv-3');

    const [evenement] = buildTodayAttentionItems(
      brief({ events: [{ id: 'ev-5', summary: 'Point Alpha', start: `${AUJOURDHUI}T10:00:00Z`, end: `${AUJOURDHUI}T11:00:00Z`, attendees_count: 2, crm_contact_ids: [] }] }),
    );
    expect(evenement.cibleId).toBe('ev-5');
  });

  it('une relance sans message reste ouvrable, sans identifiant inventé', () => {
    const [item] = buildTodayAttentionItems(
      brief({
        due_follow_ups: [{
          id: 'f-2', due_date: AUJOURDHUI, note: null,
          email_subject: null, email_from: null,
          contact_id: 'c-1', contact_name: 'Paul',
          email_message_id: null,
        }],
      }),
    );
    expect(item.cibleId).toBeNull();
  });
});

/*
 * Le dispatcher a été RETIRÉ après relecture, et le brief rouvre les modules
 * comme avant. Sur les cinq types, un seul ouvrait réellement son objet : la
 * facture. Le rendez-vous posait une cible que le canevas ne lit pas, la
 * relance courait après un compte que son hook n'a pas encore chargé, le
 * prospect écrivait dans l'état local d'un canevas que la vue CRM n'observe
 * pas, et la tâche n'était pas traitée du tout.
 *
 * Un brief où la facture s'ouvre et le reste non est précisément ce que le
 * plan interdisait : plus déroutant que l'ancien, uniformément grossier.
 *
 * Ce qui reste ci-dessus est acquis et vrai : chaque item SAIT quel objet il
 * désigne, et le serveur transmet enfin l'identifiant du message d'une
 * relance. La reprise partira de là — avec un test qui CLIQUE et vérifie
 * l'objet affiché, pas un scan de source.
 */
