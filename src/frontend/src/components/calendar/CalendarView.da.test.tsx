/**
 * DA « Application affinée », lot 8 : les quatre vues de l'Agenda
 * (`docs/plans/2026-09-11-da-lot8-agenda-design.md`, § 9).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { CalendarView } from './CalendarView';

const GABARIT = /grid-cols-\[3\.5rem_repeat\(7,1fr\)\]/;
const JOURS = ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.'];

/** Mercredi 2 septembre 2026, 11 h 48 : l'instant de la maquette. */
const MAINTENANT = new Date(2026, 8, 2, 11, 48, 0);

function evenement(champs: Record<string, unknown>) {
  return {
    id: 'evt', calendar_id: 'cal-1', summary: 'Rendez-vous', description: null, location: null,
    start_datetime: null, end_datetime: null, start_date: null, end_date: null, all_day: false,
    attendees: null, recurrence: null, status: 'confirmed', synced_at: null, ...champs,
  } as never;
}

const SEANCE = evenement({
  id: 'evt-1', summary: 'Séance 1 · Garage Benali', location: 'sur place',
  start_datetime: '2026-09-02T09:00:00', end_datetime: '2026-09-02T10:30:00',
});
const CHEVAUCHE_A = evenement({
  id: 'evt-a', summary: 'Point chantier Roux',
  start_datetime: '2026-09-02T14:00:00', end_datetime: '2026-09-02T15:00:00',
});
const CHEVAUCHE_B = evenement({
  id: 'evt-b', summary: 'Lucie Fabre, découverte',
  start_datetime: '2026-09-02T14:30:00', end_datetime: '2026-09-02T15:30:00',
});
const SALON = evenement({
  id: 'evt-jour', summary: 'Salon pro', all_day: true,
  start_date: '2026-09-02', end_date: '2026-09-02',
});
const COURT = evenement({
  id: 'evt-court', summary: 'Appel éclair', location: 'visio',
  start_datetime: '2026-09-02T16:00:00', end_datetime: '2026-09-02T16:30:00',
});

function semer(etat: Record<string, unknown>) {
  useCalendarStore.setState({
    events: [], viewMode: 'week', selectedDate: new Date(2026, 8, 2),
    showCancelled: false, searchQuery: '', currentEventId: null, isEventFormOpen: false,
    ...etat,
  } as never);
}

/** Les nœuds qui portent le gabarit à sept colonnes, dans l'ordre du document. */
function gabarits(container: HTMLElement): HTMLElement[] {
  return ([...container.querySelectorAll('div')] as HTMLElement[]).filter((d) => GABARIT.test(d.className));
}

function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

function texteEntier(container: HTMLElement, motif: RegExp): HTMLElement[] {
  return ([...container.querySelectorAll('div')] as HTMLElement[]).filter((d) =>
    motif.test(d.textContent?.trim() ?? ''),
  );
}

function laSection(container: HTMLElement): HTMLElement {
  return container.querySelector('section') as HTMLElement;
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(MAINTENANT);
});

afterEach(() => {
  vi.useRealTimers();
});

describe('lot 8 (1) : la grille semaine', () => {
  it('les trois gabarits partagent les sept colonnes et la même gouttière de défilement', () => {
    semer({ events: [SEANCE, SALON] });
    const { container } = render(<CalendarView />);

    const trois = gabarits(container);
    expect(trois.length, 'en-tête, rangée Journée, piste horaire').toBe(3);
    for (const g of trois) expect(g.className).not.toMatch(/\bw-16\b/);

    const gouttiere = ([...container.querySelectorAll('div')] as HTMLElement[]).filter((d) =>
      /\[scrollbar-gutter:stable\]/.test(d.className),
    );
    expect(gouttiere.length, 'les trois réservent la même gouttière').toBe(3);
    expect(trois[0].className, "l'en-tête clippe pour que la gouttière s'applique").toMatch(/\boverflow-hidden\b/);
    expect(trois[1].className, 'la rangée « Journée » aussi').toMatch(/\boverflow-hidden\b/);
  });

  it('les sept en-têtes se lisent « lun. » à « dim. », cadrés à gauche', () => {
    semer({ events: [] });
    const { container } = render(<CalendarView />);

    const etiquettes = texteEntier(container, /^(lun|mar|mer|jeu|ven|sam|dim)\.$/);
    expect(etiquettes.map((d) => d.textContent?.trim())).toEqual(JOURS);

    const cellules = [...gabarits(container)[0].children] as HTMLElement[];
    expect(cellules, 'gouttière + sept jours').toHaveLength(8);
    for (const cellule of cellules.slice(1)) {
      expect(cellule.className).toMatch(/\bpx-2\b/);
      expect(cellule.className).toMatch(/\bpy-2\b/);
      expect(cellule.className).toMatch(/\btext-left\b/);
    }
  });

  it('la première cellule de la rangée « Journée » est cadrée et garde 12 px', () => {
    semer({ events: [SALON] });
    const { container } = render(<CalendarView />);

    const gouttiere = gabarits(container)[1].firstElementChild as HTMLElement;
    expect(gouttiere.textContent?.trim()).toBe('Journée');
    expect(gouttiere.className).toMatch(/\bpy-2\b/);
    expect(gouttiere.className).toMatch(/\btext-left\b/);
    expect(gouttiere.className, 'pas de padding horizontal dans 3,5 rem').not.toMatch(/\bpx-\d/);
    expect(gouttiere.className).toMatch(/\btext-xs\b/);
  });

  it('chaque colonne de jour porte un trait plein, la gouttière des heures aucun', () => {
    semer({ events: [SALON] });
    const { container } = render(<CalendarView />);

    const trois = gabarits(container);
    expect(trois.length, 'sans les trois gabarits, cette garde ne prouve rien').toBe(3);
    for (const gabarit of trois.slice(0, 2)) {
      const cellules = [...gabarit.children] as HTMLElement[];
      expect(cellules[0].className, 'la gouttière ne porte pas de trait').not.toMatch(/\bborder-l\b/);
      for (const jour of cellules.slice(1)) {
        expect(jour.className).toMatch(/\bborder-l\b/);
        expect(jour.className).toMatch(/\bborder-border\b/);
        expect(jour.className, 'le jeton est plein, sans opacité').not.toMatch(/border-border\/\d/);
      }
    }
  });

  it('la piste horaire porte les mêmes sept traits, et son repère ne traverse pas la gouttière', () => {
    semer({ events: [SEANCE] });
    const { container } = render(<CalendarView />);

    const piste = gabarits(container).at(-1) as HTMLElement;
    const enfants = [...piste.children] as HTMLElement[];
    expect(enfants, 'la gouttière des heures, puis les sept jours en un seul bloc').toHaveLength(2);
    expect(enfants[0].className, 'la gouttière ne porte pas de trait').not.toMatch(/\bborder-l\b/);

    const zoneDesJours = enfants[1];
    expect(zoneDesJours.className).toMatch(/col-start-2/);
    expect(zoneDesJours.className).toMatch(/col-span-7/);
    expect(zoneDesJours.className, "c'est lui qui positionne le repère").toMatch(/\brelative\b/);

    const colonnes = [...zoneDesJours.querySelectorAll(':scope > div')].filter((d) =>
      /\bborder-l\b/.test(classesDUnNoeud(d)),
    );
    expect(colonnes, 'sept colonnes de jour').toHaveLength(7);
    for (const colonne of colonnes) {
      expect(classesDUnNoeud(colonne)).toMatch(/\bborder-border\b/);
      expect(classesDUnNoeud(colonne)).not.toMatch(/border-border\/\d/);
    }

    const repere = container.querySelector('[role="img"]') as HTMLElement;
    expect(zoneDesJours.contains(repere), 'le repère vit hors de la gouttière des heures').toBe(true);
  });

  it('le jour courant : teinte d’accent en tête, surface 2 sur la colonne', () => {
    semer({ events: [SEANCE] });
    const { container } = render(<CalendarView />);

    const enTete = [...gabarits(container)[0].children][3] as HTMLElement; // mercredi
    expect(enTete.className).toMatch(/\bbg-accent-tint\b/);

    const colonnes = ([...container.querySelectorAll('div')] as HTMLElement[]).filter((d) =>
      /\bbg-surface-2\b/.test(d.className),
    );
    expect(colonnes.length, 'la colonne du jour et sa cellule « Journée » si elle existe').toBeGreaterThanOrEqual(1);
    for (const colonne of colonnes) {
      expect(colonne.className, 'jamais la teinte des blocs sous les blocs').not.toMatch(/\bbg-accent-tint\b/);
    }
  });

  it('les lignes d’heure passent au-dessus d’un fond opaque, les blocs au-dessus d’elles', () => {
    semer({ events: [SEANCE] });
    const { container } = render(<CalendarView />);

    const lignes = ([...container.querySelectorAll('div')] as HTMLElement[]).filter((d) =>
      /\bborder-t\b/.test(d.className) && /\babsolute\b/.test(d.className),
    );
    expect(lignes.length).toBeGreaterThan(0);
    for (const ligne of lignes) expect(ligne.className).toMatch(/(^| )z-\[1\]( |$)/);

    const bloc = screen.getByRole('button', { name: /Séance 1/ });
    expect(bloc.className).toMatch(/\bz-10\b/);
  });

  it('le repère de l’heure s’annonce, et seulement quand il est dans la fenêtre', () => {
    semer({ events: [SEANCE] });
    const { container } = render(<CalendarView />);
    const repere = container.querySelector('[role="img"]') as HTMLElement;
    expect(repere).not.toBeNull();
    expect(repere.getAttribute('aria-label')).toMatch(/^Il est 11:48$/);
    expect(repere.className).toMatch(/\bpointer-events-none\b/);

    const dedans = ([...repere.querySelectorAll('div')] as HTMLElement[]).some((d) =>
      /\bbg-instant\b/.test(d.className),
    );
    expect(dedans).toBe(true);
  });

  it('une semaine sans aujourd’hui n’a pas de repère', () => {
    semer({ events: [], selectedDate: new Date(2026, 9, 14) });
    const { container } = render(<CalendarView />);
    expect(texteEntier(container, /^lun\.$/).length, 'la semaine est bien rendue').toBe(1);
    expect(container.querySelector('[role="img"]')).toBeNull();
  });
});

describe('lot 8 (2) : les blocs de rendez-vous', () => {
  it('semaine : un bouton, titre en 14 px, horaire complet et lieu sur la même ligne', () => {
    semer({ events: [SEANCE] });
    const { container } = render(<CalendarView />);

    const bloc = screen.getByRole('button', { name: /Séance 1 · Garage Benali/ });
    expect(bloc.tagName).toBe('BUTTON');
    expect(bloc.textContent).toContain('Séance 1 · Garage Benali');
    expect(bloc.textContent).toContain('09:00 à 10:30 · sur place');

    const titre = bloc.firstElementChild as HTMLElement;
    expect(titre.className).toMatch(/\btext-sm\b/);
    expect(classesDUnNoeud(bloc.lastElementChild as Element)).toMatch(/\btruncate\b/);
    expect(container.textContent).not.toContain('09:00 - 10:30');
  });

  it('jour : même horaire, et le lieu survit à un bloc court', () => {
    semer({ events: [COURT], viewMode: 'day' });
    render(<CalendarView />);
    const bloc = screen.getByRole('button', { name: /Appel éclair/ });
    expect(bloc.textContent).toContain('16:00 à 16:30 · visio');
  });

  it('jour : le titre interne ne passe pas par `capitalize`', () => {
    semer({ events: [], viewMode: 'day' });
    const { container } = render(<CalendarView />);
    const titres = [...container.querySelectorAll('h3')] as HTMLElement[];
    expect(titres.length).toBeGreaterThan(0);
    for (const titre of titres) expect(titre.className).not.toMatch(/\bcapitalize\b/);
    expect(container.textContent).toContain("(aujourd'hui)");
  });
});

describe('lot 8 (3) : deux rendez-vous au même créneau restent lisibles', () => {
  it('les deux boutons sont posés côte à côte, par leur style', () => {
    semer({ events: [CHEVAUCHE_A, CHEVAUCHE_B] });
    render(<CalendarView />);

    const a = screen.getByRole('button', { name: /Point chantier Roux/ });
    const b = screen.getByRole('button', { name: /Lucie Fabre/ });
    expect(a.style.left).toBe('0%');
    expect(b.style.left).toBe('50%');
    expect(a.style.width).toBe('50%');
    expect(b.style.width).toBe('50%');
  });
});

describe('lot 8 (4) : la grille mois', () => {
  beforeEach(() => {
    semer({ events: [], viewMode: 'month', selectedDate: new Date(2026, 8, 15) });
  });

  it('une seule grille : sept en-têtes collants puis quarante-deux cases', () => {
    const { container } = render(<CalendarView />);

    const grilles = container.querySelectorAll('div.grid-cols-7');
    expect(grilles.length).toBe(1);
    const enfants = [...grilles[0].children] as HTMLElement[];
    expect(enfants).toHaveLength(49);

    for (const entete of enfants.slice(0, 7)) {
      expect(entete.className).toMatch(/\bsticky\b/);
      expect(entete.className).toMatch(/\btop-0\b/);
      expect(entete.className, 'fond opaque, sinon les cases défilent au travers').toMatch(/\bbg-surface\b/);
      expect(entete.className).toMatch(/\bpx-2\b/);
      expect(entete.className).toMatch(/\btext-left\b/);
    }
    expect(enfants.slice(0, 7).map((e) => e.textContent?.trim())).toEqual(JOURS);
    expect(
      enfants.slice(7, 10).map((c) => c.firstElementChild?.textContent?.trim()),
    ).toEqual(['31', '1', '2']);
  });

  it('c’est la carte qui défile, et la grille qui la remplit', () => {
    const { container } = render(<CalendarView />);
    const section = laSection(container);
    expect(section.className).toMatch(/\boverflow-y-auto\b/);

    const grille = container.querySelector('div.grid-cols-7') as HTMLElement;
    expect(grille.className).not.toMatch(/\boverflow-/);
    expect(grille.className).toMatch(/\bmin-h-full\b/);
    expect(grille.className).toMatch(/grid-rows-\[auto_repeat\(6,minmax\(5\.5rem,1fr\)\)\]/);
    expect(grille.className, 'la carte porte déjà le trait et le rayon').not.toMatch(/\brounded-md\b/);

    for (const case_ of [...grille.children].slice(7)) {
      expect(classesDUnNoeud(case_), 'la hauteur minimale vit sur les rangées').not.toMatch(/min-h-\[5\.5rem\]/);
    }
  });

  it('le jour courant garde sa pastille remplie', () => {
    const { container } = render(<CalendarView />);
    const pastilles = ([...container.querySelectorAll('div, span')] as HTMLElement[]).filter((n) =>
      /\bbg-accent-fill\b/.test(classesDUnNoeud(n)),
    );
    expect(pastilles).toHaveLength(1);
    expect(pastilles[0].textContent?.trim()).toBe('2');
  });
});

describe('lot 8 (5) : la liste', () => {
  it('chaque rendez-vous est un bouton dont le nom porte résumé et horaire', () => {
    semer({ events: [SEANCE], viewMode: 'list' });
    const { container } = render(<CalendarView />);

    const bouton = screen.getByRole('button', { name: /Séance 1 · Garage Benali/ });
    expect(bouton.textContent).toContain('sur place');
    expect(bouton.textContent).toContain('09:00');
    expect(bouton.className).toMatch(/\bborder-t\b/);
    expect(bouton.className).not.toMatch(/first:border-t-0/);
    expect(bouton.className).toMatch(/\bhover:bg-surface-2\b/);

    const titreDeGroupe = container.querySelector('h3') as HTMLElement;
    expect(titreDeGroupe.className).toMatch(/\btext-accent\b/);
    expect(titreDeGroupe.className).toMatch(/\bpx-4\b/);
  });

  it('un événement de toute la journée l’annonce à droite', () => {
    semer({ events: [SALON], viewMode: 'list' });
    render(<CalendarView />);
    const bouton = screen.getByRole('button', { name: /Salon pro/ });
    expect(bouton.textContent).toContain('Toute la journée');
  });

  it('sans rendez-vous, l’état vide le dit', () => {
    semer({ events: [], viewMode: 'list' });
    render(<CalendarView />);
    expect(screen.getByRole('heading', { name: 'Aucun événement' })).toBeInTheDocument();
  });
});

describe('lot 8 (6) : les quatre vues ont le même châssis', () => {
  for (const [vue, classes] of [
    ['week', /\boverflow-hidden\b/],
    ['day', /\boverflow-hidden\b/],
    ['month', /\boverflow-y-auto\b/],
    ['list', /\boverflow-y-auto\b/],
  ] as const) {
    it(`« ${vue} » est une section nommée par la période, en flex-1 min-h-0`, () => {
      semer({ events: [SEANCE], viewMode: vue });
      const { container } = render(<CalendarView />);
      const section = laSection(container);
      expect(section, 'la racine est une section').not.toBeNull();
      expect(section.getAttribute('aria-labelledby')).toBe('agenda-periode');
      expect(section.className).toMatch(/\bflex-1\b/);
      expect(section.className).toMatch(/\bmin-h-0\b/);
      expect(section.className, 'la hauteur vient du flex, plus de h-full').not.toMatch(/\bh-full\b/);
      expect(section.className).toMatch(classes);
    });
  }
});

describe('lot 8 (7) : survol et anneau rentrant', () => {
  for (const vue of ['week', 'day', 'month'] as const) {
    it(`« ${vue} » : chaque interactif de la grille garde son survol et son anneau`, () => {
      semer({ events: [SEANCE, SALON], viewMode: vue });
      const { container } = render(<CalendarView />);
      const interactifs = [...container.querySelectorAll('button')] as HTMLElement[];
      expect(interactifs.length).toBeGreaterThan(0);
      for (const interactif of interactifs) {
        expect(interactif.className, interactif.textContent ?? '').toMatch(/\bhover:brightness-95\b/);
        expect(interactif.className).toMatch(/focus-visible:outline-offset-\[-3px\]/);
      }
    });
  }

  it('« list » : la ligne prend le survol de surface et le même anneau', () => {
    semer({ events: [SEANCE], viewMode: 'list' });
    const { container } = render(<CalendarView />);
    for (const interactif of [...container.querySelectorAll('button')] as HTMLElement[]) {
      expect(interactif.className).toMatch(/\bhover:bg-surface-2\b/);
      expect(interactif.className).toMatch(/focus-visible:outline-offset-\[-3px\]/);
    }
  });
});
