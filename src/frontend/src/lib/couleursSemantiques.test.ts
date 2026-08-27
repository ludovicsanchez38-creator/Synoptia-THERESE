/**
 * Une couleur d'état vient du thème, jamais de la palette brute.
 *
 * Le projet a des tokens sémantiques (`text-error`, `bg-success/10`,
 * `border-warning/40`…) qui suivent le thème clair comme le thème sombre, et
 * ils sont déjà largement adoptés. Mais la migration s'est arrêtée en
 * chemin : il restait 101 `text-red-400`, 75 `bg-red-500/*` et 27
 * `border-red-500/*` — des couleurs figées, choisies pour un fond sombre, qui
 * ignorent le thème.
 *
 * Le projet connaît déjà le prix de cet oubli : un commentaire de
 * `globals.css` (US-013) relève un `text-amber-500` mesuré à 2.3:1 sur fond
 * clair, très en dessous du minimum lisible.
 *
 * Ce test lit les sources plutôt que le rendu : une classe est un choix
 * d'écriture, et c'est à l'écriture qu'on l'attrape.
 */
import { describe, expect, it } from 'vitest';

const SOURCES = import.meta.glob('../components/**/*.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** Couleurs brutes bannies, et le token qui les remplace. */
const BANNIES: { motif: RegExp; nom: string; token: string }[] = [
  { motif: /\btext-red-\d{3}\b/, nom: 'text-red-*', token: 'text-error' },
  { motif: /\bbg-red-\d{3}\b/, nom: 'bg-red-*', token: 'bg-error/10' },
  { motif: /\bborder-red-\d{3}\b/, nom: 'border-red-*', token: 'border-error/40' },
];

/**
 * La seule exception, et elle est nommée : la ligne de l'heure actuelle du
 * calendrier. Son rouge n'est PAS un état d'erreur — c'est le repère
 * temporel que tous les agendas emploient. Le convertir en `bg-error` a
 * fait tomber un test de régression qui exigeait ce rouge, et il avait
 * raison : lire ce trait comme une alerte serait un contresens.
 *
 * Une exception nommée vaut mieux qu'une règle fausse.
 */
const EXCEPTIONS = new Set(['calendar/CalendarView.tsx']);

describe('Les couleurs d’état suivent le thème', () => {
  it.each(BANNIES)('plus aucun $nom : le thème a $token', ({ motif, token }) => {
    const fautifs = Object.entries(SOURCES)
      .filter(([chemin]) => !chemin.includes('.test.'))
      .filter(([chemin]) => !EXCEPTIONS.has(chemin.replace('../components/', '')))
      .filter(([, source]) =>
        source.split('\n').some((ligne) => motif.test(ligne)),
      )
      .map(([chemin]) => chemin.replace('../components/', ''));

    expect(fautifs, `à remplacer par ${token} dans : ${fautifs.join(', ')}`).toEqual([]);
  });

  it('les tokens sémantiques sont bien en usage, eux', () => {
    const tous = Object.values(SOURCES).join('\n');

    // Témoin : si l'extraction cassait, les tests ci-dessus passeraient au
    // vert pour une mauvaise raison.
    expect(tous.match(/\btext-error\b/g)?.length ?? 0).toBeGreaterThan(50);
  });
});
