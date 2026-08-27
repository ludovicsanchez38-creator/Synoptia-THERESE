/**
 * Aucun champ de saisie n'est anonyme.
 *
 * Relevé le 27/08/2026 : 67 champs texte sur 156 n'avaient ni `id` ni
 * `aria-label`. Leur `<label>` était un FRÈRE du champ, sans `htmlFor` —
 * visuellement correct, mais sans aucun lien pour qui n'a pas l'image. Un
 * lecteur d'écran annonce alors « zone de texte », sans dire laquelle.
 *
 * Ce test lit les sources : un nom accessible est un choix d'écriture, et
 * c'est à l'écriture qu'on l'attrape. Il couvre les formulaires les plus
 * utilisés, et la liste a vocation à s'allonger — pas à se raccourcir.
 */
import { describe, expect, it } from 'vitest';

const SOURCES = import.meta.glob('../components/**/*.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** Les écrans dont on garantit que chaque champ est nommé. */
const COUVERTS = [
  'calendar/EventForm.tsx',
  'memory/ContactModal.tsx',
  'tasks/TaskForm.tsx',
  'memory/ProjectModal.tsx',
  'crm/CRMPanel.tsx',
  'email/EmailCompose.tsx',
  'email/EmailConnect.tsx',
  'invoices/InvoiceForm.tsx',
  'rfc/RFCCapture.tsx',
  'settings/CRMSyncPanel.tsx',
  'settings/ToolsPanel.tsx',
  'prototype/InvoiceConversationCard.tsx',
];

/** Un champ nommé porte un id (relié par un label), ou un aria-label. */
function champsAnonymes(source: string): string[] {
  const anonymes: string[] = [];
  const balises = source.match(/<input\b[^>]*>/gs) ?? [];
  for (const balise of balises) {
    if (/type="(checkbox|radio|file)"/.test(balise)) continue;
    if (/\bid=/.test(balise) || /aria-label/.test(balise)) continue;
    anonymes.push(balise.replace(/\s+/g, ' ').slice(0, 70));
  }
  return anonymes;
}

describe('Les champs de saisie ont tous un nom', () => {
  it.each(COUVERTS)('%s', (chemin) => {
    const entree = Object.entries(SOURCES).find(([c]) => c.endsWith(chemin));
    expect(entree, `${chemin} introuvable`).toBeTruthy();

    const anonymes = champsAnonymes(entree![1]);

    expect(
      anonymes,
      `champs sans nom accessible :\n  ${anonymes.join('\n  ')}`,
    ).toEqual([]);
  });

  it('le détecteur voit bien des champs, sinon il ne prouverait rien', () => {
    const total = Object.values(SOURCES)
      .flatMap((s) => s.match(/<input\b/g) ?? []).length;

    expect(total).toBeGreaterThan(50);
  });
});
