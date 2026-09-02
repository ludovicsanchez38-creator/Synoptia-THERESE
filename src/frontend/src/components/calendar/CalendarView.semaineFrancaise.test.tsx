/**
 * B-247 : la grille du mois commençait par dimanche.
 *
 * Le même fichier tenait deux conventions : la vue Mois étiquetait
 * « Dim Lun Mar… » et calait ses cellules de tête sur `getDay()` (0 =
 * dimanche), tandis que la vue Semaine du même composant commence au lundi
 * ISO. Sur un agenda français, la semaine commence le lundi — et les deux vues
 * doivent s'accorder, sinon la même semaine ne se lit pas pareil d'un onglet à
 * l'autre.
 *
 * Étiquettes ET décalage vont ensemble : corriger l'un sans l'autre décalerait
 * tous les jours d'une colonne.
 */
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { CalendarView } from './CalendarView';

const SEMAINE_FRANCAISE = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

/** Les étiquettes de jour, dans l'ordre du document : un div dont le texte
 *  ENTIER est un nom de jour abrégé. */
function etiquettesJours(container: HTMLElement): string[] {
  return [...container.querySelectorAll('div')]
    .map((element) => element.textContent?.trim() ?? '')
    .filter((texte) => /^(Lun|Mar|Mer|Jeu|Ven|Sam|Dim)$/.test(texte));
}

describe('B-247 : la vue Mois commence le lundi comme la vue Semaine', () => {
  beforeEach(() => {
    useCalendarStore.setState({
      // Septembre 2026 : le 1er est un MARDI, donc une grille qui commence au
      // lundi s'ouvre sur le 31 août, et une grille au dimanche sur le 30.
      selectedDate: new Date(2026, 8, 15),
      viewMode: 'month',
      events: [],
      showCancelled: false,
      searchQuery: '',
      currentEventId: null,
      isEventFormOpen: false,
    });
  });

  it('la vue Mois étiquette de lundi à dimanche', () => {
    const { container } = render(<CalendarView />);
    expect(etiquettesJours(container)).toEqual(SEMAINE_FRANCAISE);
  });

  it('la première cellule du mois est le lundi 31 août, pas le dimanche 30', () => {
    const { container } = render(<CalendarView />);

    const grilles = container.querySelectorAll('div.grid-cols-7');
    expect(grilles.length).toBe(2); // en-tête + grille
    const cellules = [...grilles[1].children];
    expect(cellules.length).toBe(42); // 6 semaines : sans ça, rien n'est prouvé

    const troisPremiers = cellules
      .slice(0, 3)
      .map((cellule) => cellule.firstElementChild?.textContent?.trim());
    expect(troisPremiers).toEqual(['31', '1', '2']);
  });

  it('la vue Semaine étiquette dans le même ordre', () => {
    useCalendarStore.setState({ viewMode: 'week' });
    const { container } = render(<CalendarView />);
    expect(etiquettesJours(container)).toEqual(SEMAINE_FRANCAISE);
  });
});
