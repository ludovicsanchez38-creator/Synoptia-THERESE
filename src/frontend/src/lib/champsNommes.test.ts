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

/**
 * Un champ nommé porte un `id` (relié par un label), ou un `aria-label`.
 *
 * Le détecteur couvre `input`, `textarea` ET `select` : la première version
 * ne regardait que `input`, et trois champs anonymes des écrans « couverts »
 * passaient donc au vert — le corps d'un mail, un modèle de prompt, un
 * sélecteur de contact.
 *
 * `id=` est cherché avec sa frontière gauche : sans elle, `data-id=` était
 * accepté comme un identifiant, et un champ anonyme passait pour nommé.
 */
function champsAnonymes(source: string): string[] {
  const anonymes: string[] = [];
  for (const balise of balisesDeChamp(source)) {
    if (/type="(checkbox|radio|file|hidden)"/.test(balise)) continue;
    if (/(?<![-\w])id=/.test(balise) || /aria-label/.test(balise)) continue;
    anonymes.push(balise.replace(/\s+/g, ' ').slice(0, 70));
  }
  return anonymes;
}

/**
 * Découpe les balises de champ en tenant compte des accolades JSX.
 *
 * Un `<input[^>]*>` naïf s'arrête au PREMIER `>` — or `onChange={(e) => …}`
 * en contient un. La balise était donc tronquée avant son `aria-label`, et
 * un champ correctement nommé était compté comme anonyme. Le défaut marche
 * aussi dans l'autre sens : il suffit qu'une flèche précède l'attribut
 * `id` pour qu'un champ anonyme passe pour nommé.
 */
function balisesDeChamp(source: string): string[] {
  const balises: string[] = [];
  // Les commentaires parlent parfois de `<input>` : les compter reviendrait
  // à exiger un nom accessible sur une phrase.
  source = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
  const debut = /<(input|textarea|select)\b/g;
  let m: RegExpExecArray | null;
  while ((m = debut.exec(source)) !== null) {
    let profondeur = 0;
    let i = m.index;
    for (; i < source.length; i += 1) {
      const c = source[i];
      if (c === '{') profondeur += 1;
      else if (c === '}') profondeur -= 1;
      else if (c === '>' && profondeur === 0) break;
    }
    balises.push(source.slice(m.index, i + 1));
    debut.lastIndex = i;
  }
  return balises;
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
