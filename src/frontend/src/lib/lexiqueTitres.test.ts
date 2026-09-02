/**
 * Le lexique 0.48 vérifie que chaque chose porte UN nom — sur les registres
 * de textes exportés (Centre, manifeste, actions, raccourcis, commandes,
 * vues, onboarding). Il ne regarde pas les TITRES affichés dans les
 * panneaux, et quatre y avaient dérivé sans que rien ne le signale :
 * « Calendrier » pour l'Agenda, « Facturation » pour Devis et factures,
 * « Board de décision » et « Atelier de code ».
 *
 * D'où la sensation de « trop d'interfaces » signalée par Ludo le
 * 27/08/2026 : le même objet s'appelle Agenda dans le tiroir et Calendrier
 * une fois ouvert. Deux noms, une chose.
 *
 * Ce test ferme la porte restée ouverte. Il lit les sources plutôt que le
 * rendu : un titre est une constante d'écran, et le lire ainsi couvre les
 * panneaux qu'un test de rendu devrait monter un par un avec leurs données.
 */
import { describe, expect, it } from 'vitest';

const SOURCES = import.meta.glob('../components/**/*.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** Les titres interdits, et le mot du lexique qui doit les remplacer. */
const INTERDITS: { titre: string; lexique: string }[] = [
  { titre: 'Calendrier', lexique: 'Agenda' },
  { titre: 'Facturation', lexique: 'Devis et factures' },
  { titre: 'Board de décision', lexique: 'Décision' },
  { titre: 'Atelier de code', lexique: 'Améliorer THÉRÈSE' },
];

/**
 * Extrait le texte des titres statiques d'un fichier.
 *
 * B-241 (02/09) : les huit panneaux embarqués ont vu leur titre passer de
 * `<h1>`/`<h2>` à `<p>` - la coque de la vue unifiée en posait déjà un, et
 * deux titres de même texte font un plan de page qui ment. Ces libellés
 * restent le NOM de l'écran à l'oeil, donc ils restent du ressort du
 * lexique : une règle indexée sur la seule balise `<h*>` serait devenue
 * aveugle à ce qu'elle protégeait, et « Calendrier » pourrait revenir en
 * tête de l'Agenda sans que rien ne bronche. Un titre démoté reste un titre.
 */
function titresDe(source: string): string[] {
  const titres: string[] = [];
  const motifs = [
    /<h[123][^>]*>([^<>{]+)<\/h[123]>/g,
    // Titre démoté : un <p> qui porte la typographie d'un titre d'écran.
    /<p[^>]*className="[^"]*text-lg font-(?:semibold|bold)[^"]*"[^>]*>([^<>{]+)<\/p>/g,
  ];
  for (const motif of motifs) {
    let trouve: RegExpExecArray | null;
    while ((trouve = motif.exec(source)) !== null) {
      const texte = trouve[1].trim();
      if (texte) titres.push(texte);
    }
  }
  return titres;
}

describe('Un nom ne désigne qu’une chose — jusque dans les titres', () => {
  it.each(INTERDITS)(
    '« $titre » n’apparaît dans aucun titre : le lexique dit « $lexique »',
    ({ titre, lexique }) => {
      const fautifs = Object.entries(SOURCES)
        .filter(([chemin]) => !chemin.includes('.test.'))
        .filter(([, source]) => titresDe(source).includes(titre))
        .map(([chemin]) => chemin.replace('../components/', ''));

      expect(
        fautifs,
        `titre « ${titre} » au lieu de « ${lexique} » dans : ${fautifs.join(', ')}`,
      ).toEqual([]);
    },
  );

  it('les titres démotés en <p> restent dans le champ de la règle', () => {
    // Sans ce témoin, la correction B-241 sortirait huit noms d'écran du
    // lexique sans qu'aucun test ne le dise.
    const panneau = SOURCES[
      Object.keys(SOURCES).find((chemin) => chemin.endsWith('calendar/CalendarPanel.tsx')) as string
    ];
    expect(titresDe(panneau)).toContain('Agenda');
  });

  it('les titres du lexique, eux, sont bien présents à l’écran', () => {
    const tous = Object.entries(SOURCES)
      .filter(([chemin]) => !chemin.includes('.test.'))
      .flatMap(([, source]) => titresDe(source));

    // Témoin : si l'extraction de titres cassait, ce test tomberait aussi et
    // les quatre cas ci-dessus passeraient au vert pour une mauvaise raison.
    expect(tous.length).toBeGreaterThan(20);
  });
});
