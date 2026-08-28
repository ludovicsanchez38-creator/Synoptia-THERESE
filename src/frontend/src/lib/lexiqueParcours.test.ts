/**
 * E3 — le titre d'une surface doit suivre le verbe qui l'ouvre.
 *
 * Campagne dix personas, constat U3 : après un clic sur **Écrire**, trois
 * libellés parlaient de LECTURE. `scenarioLabels[scenario]` n'est pas
 * décoratif — c'est le titre accessible du canevas : un utilisateur au lecteur
 * d'écran cliquait **Écrire** et s'entendait annoncer **« Consulter mes
 * emails »**.
 *
 * La dérive vient de la v0.53.0 : l'entrée 10 a changé ce que le verbe FAIT,
 * les titres sont restés. `lexiqueTitres.test.ts` ne les couvrait pas.
 *
 * Un premier jet de ce gate posait une liste de mots interdits (« consulter »,
 * « lecture »). La relecture l'a rejeté, à raison : il forçait à renommer la
 * boîte de réception, qui EST une consultation, et cassait au hasard des mots
 * sur les autres verbes. Le gate appariE désormais deux tables voisines —
 * rigide sur cinq paires, ce qui est le bon grain : la prochaine entrée qui
 * change un comportement devra toucher la table, sinon ce test tombe.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { ACTIONS_ETABLI, TITRES_ETABLI } from './etabli';

describe('E3 — chaque verbe de l’établi porte le titre de sa surface', () => {
  it('les cinq verbes ont un titre, et rien d’autre n’en a', () => {
    const verbes = ACTIONS_ETABLI.map((a) => a.id).sort();
    expect(Object.keys(TITRES_ETABLI).sort()).toEqual(verbes);
  });

  it('le titre de « Écrire » annonce une écriture, pas une consultation', () => {
    // Le cas qui a dérivé : « Écrire » → « Consulter mes emails ».
    // Un premier jet acceptait /message/i, donc « Consulter mes messages »
    // serait passé. On exige un verbe d'écriture ET on refuse les verbes de
    // consultation sur CE titre — la boîte de réception, elle, garde les siens.
    expect(TITRES_ETABLI.email).toMatch(/écrire|rédiger|rédaction/i);
    expect(TITRES_ETABLI.email).not.toMatch(/consulter|lecture|voir|afficher/i);
  });

  it('la coque n’écrase aucun de ces titres', () => {
    // La dérive venait de la duplication : la coque tenait sa propre table,
    // loin des verbes.
    //
    // Un premier jet vérifiait `toContain('TITRES_ETABLI')`. Insuffisant :
    // l'identifiant apparaît dès l'import, et un override APRÈS le spread
    // aurait reproduit le bug d'origine tout en restant vert —
    //     { ...TITRES_ETABLI, email: 'Consulter mes emails', ... }
    // TypeScript l'accepte, `TITRES_ETABLI.email` reste juste, et l'écran ment.
    // On vérifie donc qu'aucune clé de l'établi n'est redéfinie dans le bloc.
    const coque = readFileSync(
      join(__dirname, '..', 'components', 'prototype', 'ConversationCanvasPrototype.tsx'),
      'utf-8',
    );
    const debut = coque.indexOf('const scenarioLabels');
    expect(debut, 'table scenarioLabels introuvable').toBeGreaterThan(-1);
    const bloc = coque.slice(debut, coque.indexOf('};', debut));

    expect(bloc).toContain('...TITRES_ETABLI');

    const redefinis = ACTIONS_ETABLI
      .map((action) => action.id)
      .filter((id) => new RegExp(`(^|[^.\\w])${id}\\s*:`, 'm').test(bloc));

    expect(redefinis,
      `la coque redéfinit ${redefinis.join(', ')} après le spread : ` +
      'le titre affiché ne suivrait plus le verbe. Modifier TITRES_ETABLI.',
    ).toEqual([]);
  });
});

describe('E5 — les relabels ne laissent pas l’ancien terme à côté', () => {
  const ECRANS = [
    'components/invoices/InvoiceForm.tsx',
    'components/prototype/InvoiceConversationCard.tsx',
    'components/prototype/usePrototypeInvoiceData.ts',
    'components/prototype/ConversationCanvasPrototype.tsx',
    'components/prototype/CapabilityCenter.tsx',
  ];

  it('« profil émetteur » ne survit nulle part à l’écran', () => {
    // Relevé par la relecture : j'avais renommé le bandeau et laissé le terme
    // dans trois messages voisins, sur la surface que je venais d'éditer.
    for (const chemin of ECRANS) {
      const code = readFileSync(join(__dirname, '..', chemin), 'utf-8')
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^\s*\/\/.*$/gm, '');
      expect(code, `${chemin} porte encore « profil émetteur »`).not.toMatch(
        /profil émetteur/i,
      );
    }
  });

  it('la surface facturation dit devis ET factures', () => {
    // « Tes devis » était clair mais trop étroit : listInvoices() mélange les
    // deux, et le lexique 0.48 nomme l'objet « Devis et factures ».
    for (const chemin of ECRANS) {
      const code = readFileSync(join(__dirname, '..', chemin), 'utf-8')
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^\s*\/\/.*$/gm, '');
      expect(code, `${chemin} promet « tes devis » seuls`).not.toMatch(
        /["'>]Tes devis["'<]/,
      );
      expect(code).not.toMatch(/facturation locale/i);
    }
  });
});
