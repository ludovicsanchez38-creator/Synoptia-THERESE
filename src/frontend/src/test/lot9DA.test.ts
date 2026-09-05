/**
 * Lot 9 du cycle 3 (05/09/2026) : gardes de source pour dix défauts DA/UI
 * confirmés par RP09 et RP10. Chaque garde nomme son bug et rougit sur HEAD.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const SRC = path.join(__dirname, '..');
const lire = (rel: string) => readFileSync(path.join(SRC, rel), 'utf-8');

describe('lot 9 - DA et UI', () => {
  it('B-358 : plus aucun bg-white plein dans un interrupteur', () => {
    for (const f of ['components/settings/PrivacyTab.tsx', 'components/settings/VoiceLocalSection.tsx']) {
      expect(lire(f), f).not.toMatch(/\bbg-white\b(?!\/)/);
    }
  });

  it('B-371 : aucune action peinte en encre sur une encre sémantique', () => {
    const fautives = lire('components/prototype/FollowUpsWorkspaceCanvas.tsx')
      .split('\n')
      .filter((l) => /\bbg-text\b(?!-)/.test(l) && /\btext-(error|success|accent|warning)-ink\b/.test(l));
    expect(fautives).toEqual([]);
  });

  it("B-365 : l'heure courante de l'agenda est en text-instant, pas en text-error", () => {
    const src = lire('components/calendar/CalendarView.tsx');
    expect(src).not.toMatch(/text-xs font-medium text-error ml-2/);
    expect(src).toMatch(/text-xs font-medium text-instant ml-2/);
  });

  it('B-367 : le guide Gmail ne porte plus d\'emoji', () => {
    const src = lire('components/email/wizard/GuideStep.tsx');
    expect(src).not.toMatch(/[\u{1F300}-\u{1FAFF}✓✗]/u);
  });

  it('B-363 : les couleurs d\'attention agenda et tâches sont celles du domaine', () => {
    const src = lire('components/prototype/TodayDashboardCard.tsx');
    expect(src).toMatch(/event: 'bg-domaine-agenda-tint text-domaine-agenda'/);
    expect(src).toMatch(/task: 'bg-domaine-taches-tint text-domaine-taches'/);
  });

  it('B-373 : un fieldset en display:contents ne porte pas disabled:opacity', () => {
    expect(lire('components/prototype/InvoiceConversationCard.tsx')).not.toMatch(/contents disabled:opacity-70/);
  });

  it('B-370 : « Boîte de réception » prend son accent circonflexe', () => {
    const src = lire('components/email/EmailPanel.tsx');
    expect(src).not.toContain("'Boite de réception'");
    expect(src).toContain('Boîte de réception');
  });

  it('B-328 : la carte devis formate ses montants par montantAvecDevise', () => {
    const src = lire('components/prototype/InvoiceConversationCard.tsx');
    expect(src).toContain('montantAvecDevise');
    expect(src).not.toMatch(/Intl\.NumberFormat\('fr-FR', \{ style: 'currency'/);
  });

  it('B-354 : le panneau CRM passe par le client API, plus par fetch relatif', () => {
    const src = lire('components/settings/CRMSyncPanel.tsx');
    expect(src).not.toMatch(/fetch\('\/api\/crm\/google-sheets\/list'/);
    expect(src).toContain('listGoogleSheets');
    expect(lire('services/api/crm.ts')).toContain('export async function listGoogleSheets');
  });

  it('B-388 : la liste transmet le type courant au formulaire', () => {
    expect(lire('components/invoices/InvoicesPanel.tsx')).toMatch(/defaultDocumentType=\{filters\.document_type === 'devis' \? 'devis' : 'facture'\}/);
  });
});
