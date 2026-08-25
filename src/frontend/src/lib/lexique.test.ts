/**
 * Lot C (0.48) — un mot par chose.
 *
 * Le test porte sur les REGISTRES DE TEXTES EXPORTÉS, jamais sur un scan
 * brut du code (faux positifs sur identifiants, commentaires, types). Un
 * terme technique interdit à l'écran standard doit disparaître du libellé,
 * pas de l'id interne — les ids restent stables.
 *
 * Table du lexique : docs/RULES-DESIGN.md (source unique).
 */
import { describe, expect, it } from 'vitest';

import { APP_ACTIONS } from './actionRegistry';
import { CAPACITES } from './capacites/manifeste';
import { capabilities } from '../components/prototype/CapabilityCenter';
import { SHORTCUT_GROUPS } from '../components/chat/ShortcutsModal';
import { SLASH_COMMANDS } from '../components/chat/SlashCommandsMenu';
import { viewLabels } from '../components/prototype/PrototypeUnifiedViewCanvas';
import { TEXTES_ONBOARDING } from '../components/onboarding/textes';
import { CHIPS as CHIPS_ACTIONS } from '../components/chat/ActionChips';
import { ALL_TABS } from '../components/settings/SettingsModal';

/**
 * Interdits à l'écran standard. Comparés aux libellés des registres —
 * `\b` pour éviter les faux positifs (« Outils » n'est pas « tools »).
 */
const INTERDITS: [string, RegExp][] = [
  ['sidecar', /\bsidecar\b/i],
  ['fencing', /\bfencing\b/i],
  ['Qdrant', /\bqdrant\b/i],
  ['generation_id', /generation_id/i],
  ['tools (anglais)', /\btools?\b/],
  ['BYOK', /\bBYOK\b/],
  ['LLM', /\bLLMs?\b/],
  ['MCP', /\bMCP\b/],
  ['provider', /\bproviders?\b/i],
];

function violations(textes: [string, string][]): string[] {
  const trouvees: string[] = [];
  for (const [origine, texte] of textes) {
    for (const [nom, motif] of INTERDITS) {
      if (motif.test(texte)) {
        trouvees.push(`${origine} : « ${texte} » contient ${nom}`);
      }
    }
  }
  return trouvees;
}

describe('Aucun terme technique dans les registres de textes', () => {
  it('le Centre de capacités (titres, descriptions, features, prompts)', () => {
    const textes: [string, string][] = capabilities.flatMap((c) => [
      [`carte ${c.id} (title)`, c.title] as [string, string],
      [`carte ${c.id} (description)`, c.description] as [string, string],
      ...c.features.map(
        (f): [string, string] => [`carte ${c.id} (feature)`, f],
      ),
      [`carte ${c.id} (prompt)`, c.prompt] as [string, string],
    ]);
    expect(violations(textes)).toEqual([]);
  });

  it('le manifeste de capacités (nom, quoi)', () => {
    const textes: [string, string][] = CAPACITES.flatMap((c) => [
      [`${c.id} (nom)`, c.textes['fr-FR'].nom] as [string, string],
      [`${c.id} (quoi)`, c.textes['fr-FR'].quoi] as [string, string],
    ]);
    expect(violations(textes)).toEqual([]);
  });

  it('le registre d’actions (labels, descriptions)', () => {
    const textes: [string, string][] = APP_ACTIONS.flatMap((a) => [
      [`${a.id} (label)`, a.label] as [string, string],
      [`${a.id} (description)`, a.description] as [string, string],
    ]);
    expect(violations(textes)).toEqual([]);
  });

  it('les raccourcis clavier', () => {
    const textes: [string, string][] = SHORTCUT_GROUPS.flatMap((g) => [
      [`groupe ${g.title}`, g.title] as [string, string],
      ...g.shortcuts.map(
        (s): [string, string] => [`raccourci ${g.title}`, s.description],
      ),
    ]);
    expect(violations(textes)).toEqual([]);
  });

  it('les commandes slash', () => {
    const textes: [string, string][] = SLASH_COMMANDS.flatMap((c) => [
      [`${c.prefix} (nom)`, c.name] as [string, string],
      [`${c.prefix} (description)`, c.description] as [string, string],
    ]);
    expect(violations(textes)).toEqual([]);
  });

  it('les onglets des Réglages', () => {
    const textes: [string, string][] = ALL_TABS.map((t) => [
      `onglet ${t.id}`, t.label,
    ]);
    expect(violations(textes)).toEqual([]);
  });

  it('l’onboarding (registre extrait des chaînes inline)', () => {
    const textes: [string, string][] = [
      ['onboarding (titre LLMStep)', TEXTES_ONBOARDING.choixServiceIA.titre],
      ['onboarding (sous-titre LLMStep)', TEXTES_ONBOARDING.choixServiceIA.sousTitre],
      ...TEXTES_ONBOARDING.risques.flatMap((r): [string, string][] => [
        [`onboarding risque (titre)`, r.title],
        [`onboarding risque (description)`, r.description],
      ]),
    ];
    expect(violations(textes)).toEqual([]);
  });

  it('les affordances du chat insèrent les cibles du lexique', () => {
    // Revue 0.48 p2 (F4) : les puces et le menu / annonçaient encore
    // « ouvrir crm », « ouvrir mémoire », « ouvrir calendrier »,
    // « ouvrir facturation » - alias tolérés au parseur, jamais annoncés.
    const inserts = [
      ...CHIPS_ACTIONS.map((c) => c.insert),
      ...SLASH_COMMANDS.map((c) => c.prefix),
    ].filter((texte): texte is string => Boolean(texte));
    const anciens = [
      'ouvrir crm', 'ouvrir mémoire', 'ouvrir memoire',
      'ouvrir calendrier', 'ouvrir facturation',
    ];
    const fautifs = inserts.filter((texte) =>
      anciens.some((ancien) => texte.includes(ancien)),
    );
    expect(fautifs).toEqual([]);
    expect(inserts).toContain('{action: ouvrir pipeline}');
    expect(inserts).toContain('{action: ouvrir agenda}');
  });

  it('les libellés de vues', () => {
    const textes: [string, string][] = Object.entries(viewLabels).map(
      ([vue, label]) => [`vue ${vue}`, label],
    );
    expect(violations(textes)).toEqual([]);
  });
});

describe('Le lexique impose un mot par chose (table RULES-DESIGN.md)', () => {
  it('les vues portent leur nom d’écran', () => {
    expect(viewLabels.memory).toBe('Contacts');
    expect(viewLabels.crm).toBe('Pipeline');
    expect(viewLabels.calendar).toBe('Agenda');
    expect(viewLabels.invoices).toBe('Devis et factures');
    expect(viewLabels.files).toBe('Fichiers');
    expect(viewLabels.documents).toBe('Documents');
    expect(viewLabels.tasks).toBe('Tâches');
  });

  it('les cartes du Centre suivent le lexique', () => {
    const titres = Object.fromEntries(capabilities.map((c) => [c.id, c.title]));
    expect(titres['decision-board']).toBe('Décision');
    expect(titres['agents']).toBe('Améliorer THÉRÈSE');
    expect(titres['document-workshop']).toBe('Rédiger un document');
    expect(titres['contacts-memory']).toBe('Contacts');
    expect(titres['crm']).toBe('Pipeline');
    expect(titres['files-rag']).toBe('Fichiers');
  });

  it('la navigation dit « Décision », jamais « Board » en libellé', () => {
    const board = APP_ACTIONS.find((a) => a.id === 'board.open');
    expect(board?.label).toBe('Décision');
    const libellesRaccourcis = SHORTCUT_GROUPS.flatMap((g) =>
      g.shortcuts.map((s) => s.description),
    );
    expect(libellesRaccourcis).not.toContain('Board de décision');
    expect(libellesRaccourcis).toContain('Décision');
  });
});
