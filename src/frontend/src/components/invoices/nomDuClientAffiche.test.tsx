/**
 * B4 — le nom du client doit être À L'ÉCRAN, pas seulement dans le JSON.
 *
 * Campagne dix personas, finding F5 de l'artisan : « On voit DEV-2026-001,
 * badge Devis, Brouillon, dates, montant. Pas le client. Je retiens Moreau. »
 *
 * Premier jet : j'ai ajouté `contact_name` à l'API et au brief… et aucun écran
 * ne le lisait. Verdict de la relecture : « Un champ JSON que l'UI n'affiche
 * pas, c'est POST qui jetait l'adresse : même geste. » Le finding était intact.
 *
 * Ces tests portent donc sur ce qui s'affiche.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { buildTodayAttentionItems } from '../prototype/prototypeReadModels';

const RACINE = join(__dirname, '..', '..');
const source = (chemin: string) =>
  readFileSync(join(RACINE, chemin), 'utf-8')
    .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/\/.*$/gm, '');

describe('B4 — l’écran nomme le client', () => {
  it('le brief du jour titre avec le client, pas la référence', () => {
    const items = buildTodayAttentionItems({
      date: '2026-08-28',
      events: [],
      urgent_tasks: [],
      due_follow_ups: [],
      stale_prospects: [],
      summary: {},
      overdue_invoices: [
        {
          id: 'inv-1',
          invoice_number: 'FACT-2026-001',
          contact_id: 'c1',
          contact_name: 'Sophie Garcia',
          total_ttc: 198,
          currency: 'EUR',
          due_date: '2026-07-15',
          status: 'overdue',
        },
      ],
    } as never);

    const facture = items.find((i) => i.kind === 'invoice');
    expect(facture).toBeDefined();
    expect(facture!.title).toContain('Garcia');
  });

  it('retombe sur la référence quand le client est inconnu', () => {
    const items = buildTodayAttentionItems({
      date: '2026-08-28',
      events: [],
      urgent_tasks: [],
      due_follow_ups: [],
      stale_prospects: [],
      summary: {},
      overdue_invoices: [
        {
          id: 'inv-2',
          invoice_number: 'FACT-2026-002',
          contact_id: 'c2',
          contact_name: null,
          total_ttc: 100,
          currency: 'EUR',
          due_date: null,
          status: 'overdue',
        },
      ],
    } as never);

    const facture = items.find((i) => i.kind === 'invoice');
    expect(facture!.title).toContain('FACT-2026-002');
  });

  it('le type DashboardInvoice porte le nom', () => {
    expect(source('services/api/dashboard.ts')).toMatch(/contact_name/);
  });

  it('la liste Devis et factures affiche le client', () => {
    // Sans cela, l'écran que l'artisan ouvre reste identique au finding.
    expect(source('components/invoices/InvoicesPanel.tsx')).toMatch(/contact_name/);
  });

  it('le type Invoice du frontend porte le nom', () => {
    expect(source('services/api/invoices.ts')).toMatch(/contact_name/);
  });
});
