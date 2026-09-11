/**
 * DA « Application affinée », lot 8 : l'écran Agenda
 * (`docs/plans/2026-09-11-da-lot8-agenda-design.md`, § 9).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

const api = vi.hoisted(() => ({
  getEmailAuthStatus: vi.fn(),
  listCalendars: vi.fn(),
  listEvents: vi.fn(),
  syncCalendar: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: (...a: unknown[]) => api.getEmailAuthStatus(...a),
    listCalendars: (...a: unknown[]) => api.listCalendars(...a),
    listEvents: (...a: unknown[]) => api.listEvents(...a),
    syncCalendar: (...a: unknown[]) => api.syncCalendar(...a),
  };
});

import { CalendarPanel } from './CalendarPanel';

const CAUSE_403 = 'Google Calendar API has not been used in project 42 before or it is disabled.';

const AGENDA_LOCAL = {
  id: 'cal-1',
  account_id: null,
  summary: 'Agenda Atelier',
  description: null,
  timezone: 'Europe/Paris',
  primary: true,
  provider: 'local',
  synced_at: null,
} as never;

const AGENDA_CALDAV = { ...(AGENDA_LOCAL as object), id: 'cal-2', summary: 'Agenda CalDAV', provider: 'caldav', primary: false } as never;

const RENDEZ_VOUS = {
  id: 'evt-1',
  calendar_id: 'cal-1',
  summary: 'Séance 1 · Garage Benali',
  description: null,
  location: 'sur place',
  start_datetime: '2026-09-02T09:00:00',
  end_datetime: '2026-09-02T10:30:00',
  start_date: null,
  end_date: null,
  all_day: false,
  attendees: null,
  recurrence: null,
  status: 'confirmed',
  synced_at: null,
} as never;

function semer(etat: Record<string, unknown> = {}) {
  useCalendarStore.setState({
    calendars: [AGENDA_LOCAL],
    currentCalendarId: 'cal-1',
    events: [RENDEZ_VOUS],
    currentEventId: null,
    isEventFormOpen: false,
    viewMode: 'week',
    selectedDate: new Date(2026, 8, 2),
    draftEvent: {},
    showCancelled: false,
    searchQuery: '',
    lastSyncAt: null,
    ...etat,
  } as never);
}

async function monter() {
  const rendu = render(<CalendarPanel standalone />);
  // `{ selector: 'p' }` : le formulaire porte un `<label>Agenda</label>`, et
  // un `getByText` nu se mettrait à trouver deux nœuds le jour où le panneau
  // s'ouvrirait directement sur lui.
  await waitFor(() => expect(screen.getByText('Agenda', { selector: 'p' })).toBeInTheDocument());
  for (let tour = 0; tour < 6; tour++) {
    await act(async () => { await Promise.resolve(); });
  }
  return rendu;
}

const FICHIERS = ['CalendarPanel.tsx', 'CalendarView.tsx', 'EventForm.tsx', 'EventDetail.tsx'];

function source(fichier: string): string {
  return readFileSync(join(__dirname, fichier), 'utf8');
}

/** Les classes d'un nœud, `className` d'un SVG compris. */
function classesDUnNoeud(n: Element): string {
  const brut = (n as HTMLElement).className;
  if (typeof brut === 'string') return brut;
  const svg = (n as SVGElement).className;
  return typeof svg === 'object' && svg && 'baseVal' in svg ? svg.baseVal : '';
}

/** Tout nœud du sous-arbre d'un interactif qui porte `text-xs` : le plancher
 *  des interactifs est 14 px (§ 9, garde 6). */
function textesMinusculesDansUnInteractif(racine: HTMLElement): string[] {
  const fautifs: string[] = [];
  for (const interactif of racine.querySelectorAll('button, a, input, select, textarea, [role="button"]')) {
    const visiter = (n: Element) => {
      if (/\btext-xs\b/.test(classesDUnNoeud(n))) fautifs.push(classesDUnNoeud(n).slice(0, 80));
      for (const enfant of Array.from(n.children)) visiter(enfant);
    };
    visiter(interactif);
  }
  return fautifs;
}

function boutonsNommes(racine: HTMLElement, nom: string): HTMLButtonElement[] {
  return ([...racine.querySelectorAll('button')] as HTMLButtonElement[]).filter(
    (b) => (b.textContent?.trim() ?? '') === nom || b.getAttribute('aria-label') === nom,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  api.getEmailAuthStatus.mockResolvedValue({ authenticated: false, accounts: [] });
  api.listCalendars.mockResolvedValue([AGENDA_LOCAL]);
  api.listEvents.mockResolvedValue([RENDEZ_VOUS]);
  api.syncCalendar.mockResolvedValue({ synced_at: '2026-09-11T10:00:00Z' });
  semer();
  useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false } as never);
});

describe('lot 8 (1) : les crochets de test survivent', () => {
  it('la racine garde `calendar-panel`', async () => {
    await monter();
    expect(screen.getByTestId('calendar-panel')).toBeInTheDocument();
  });

  it('le bandeau de péremption garde `calendar-stale-warning`', async () => {
    api.listEvents.mockRejectedValue(new Error('réseau injoignable'));
    await monter();
    expect(await screen.findByTestId('calendar-stale-warning')).toBeInTheDocument();
  });
});

describe('lot 8 (2) : les segments de vue', () => {
  it('sont un groupe nommé « Vue de l’agenda » de quatre boutons pressés', async () => {
    await monter();
    const groupe = screen.getByRole('group', { name: "Vue de l'agenda" });
    const boutons = [...groupe.querySelectorAll('button')];
    expect(boutons).toHaveLength(4);
    expect(boutons.map((b) => b.textContent?.trim())).toEqual(['Jour', 'Semaine', 'Mois', 'Liste']);
    expect(boutons.every((b) => b.hasAttribute('aria-pressed'))).toBe(true);
  });

  it('« Semaine » pose `week` et range la fiche', async () => {
    semer({ viewMode: 'month', currentEventId: 'evt-1' });
    await monter();
    fireEvent.click(screen.getByRole('button', { name: 'Semaine' }));
    expect(useCalendarStore.getState().viewMode).toBe('week');
    expect(useCalendarStore.getState().currentEventId).toBeNull();
  });
});

describe('lot 8 (3) : le grand geste', () => {
  it('« Nouveau rendez-vous » est un bouton `lg` qui ouvre le formulaire', async () => {
    await monter();
    const geste = screen.getByRole('button', { name: /Nouveau rendez-vous/ });
    expect(geste.className).toMatch(/\bh-11\b/);
    fireEvent.click(geste);
    expect(useCalendarStore.getState().isEventFormOpen).toBe(true);
  });
});

describe('lot 8 (4) : un seul « Réessayer » à l’écran', () => {
  it('grille saine : aucun', async () => {
    const { container } = await monter();
    expect(container.querySelector('section[aria-labelledby="agenda-periode"]'), 'la grille est rendue').not.toBeNull();
    expect(boutonsNommes(container, 'Réessayer')).toHaveLength(0);
  });

  it('péremption seule : un seul, et il appelle la synchronisation', async () => {
    api.listEvents.mockRejectedValue(new Error('réseau injoignable'));
    const { container } = await monter();
    const reprises = boutonsNommes(container, 'Réessayer');
    expect(reprises).toHaveLength(1);
    fireEvent.click(reprises[0]);
    await waitFor(() => expect(api.syncCalendar).toHaveBeenCalledTimes(1));
  });

  it('403 agendas et péremption : un seul bandeau qui dit les deux, un seul « Réessayer »', async () => {
    api.listCalendars.mockRejectedValue(new Error(CAUSE_403));
    api.listEvents.mockRejectedValue(new Error('réseau injoignable'));
    const { container } = await monter();

    const bandeaux = [...container.querySelectorAll('[role="alert"]')];
    expect(bandeaux, 'un seul bandeau, jamais deux').toHaveLength(1);
    const fusionne = screen.getByTestId('calendar-stale-warning');
    expect(fusionne.textContent, 'le titre porte le message 403').toContain(CAUSE_403.slice(0, 40));
    expect(fusionne.textContent, 'le corps dit que les données sont conservées').toMatch(/[Dd]onnées conservées/);
    expect(boutonsNommes(container, 'Réessayer')).toHaveLength(1);
  });

  it('reconnexion : aucun « Réessayer », le geste reste « Reconnecter »', async () => {
    api.listCalendars.mockRejectedValue(new Error('OAuth credentials not found. Please reconnect your account.'));
    const { container } = await monter();
    expect(boutonsNommes(container, 'Réessayer')).toHaveLength(0);
    expect(screen.getByRole('button', { name: /Reconnecter/ })).toBeInTheDocument();
  });

  it('la péremption reste lisible quand le formulaire est ouvert', async () => {
    api.listEvents.mockRejectedValue(new Error('réseau injoignable'));
    semer({ isEventFormOpen: true });
    await monter();
    expect(screen.getByTestId('calendar-stale-warning')).toBeInTheDocument();
  });

  it("l'icône « Synchroniser l'agenda » reste rendue sous un bandeau", async () => {
    api.listEvents.mockRejectedValue(new Error('réseau injoignable'));
    const { container } = await monter();
    expect(boutonsNommes(container, 'Réessayer')).toHaveLength(1);
    expect(screen.getByRole('button', { name: "Synchroniser l'agenda" })).toBeInTheDocument();
  });
});

describe('lot 8 (5) : le lexique porte aussi sur les noms accessibles', () => {
  it('le sélecteur est un `Select` nommé « Agenda affiché »', async () => {
    const { container } = await monter();
    const selecteur = screen.getByLabelText('Agenda affiché');
    expect(selecteur.tagName).toBe('SELECT');
    expect(container.querySelector('select + svg'), 'la flèche de la primitive Select').not.toBeNull();
  });

  it('liste vide : aucune option, et aucun bouton de création (BUG-143)', async () => {
    api.listCalendars.mockResolvedValue([]);
    semer({ calendars: [], currentCalendarId: null, events: [] });
    const { container } = await monter();
    expect(screen.getByLabelText('Agenda affiché').querySelectorAll('option')).toHaveLength(0);
    expect(boutonsNommes(container, 'Créer un agenda')).toHaveLength(0);
    expect(container.textContent).not.toMatch(/[Cc]réer un (agenda|calendrier)/);
  });

  it('plus aucun `aria-label` des quatre fichiers ne dit « Calendrier »', () => {
    for (const fichier of FICHIERS) {
      const fautifs = source(fichier)
        .split('\n')
        .filter((l) => /aria-label=(["'{])[^\n]*[Cc]alendrier/.test(l));
      expect(fautifs, `${fichier} : ${fautifs.join(' | ')}`).toEqual([]);
    }
  });
});

describe('lot 8 (6) : typographie et palette', () => {
  it('aucun `text-xs` dans le sous-arbre d’un interactif', async () => {
    const { container } = await monter();
    const fautifs = textesMinusculesDansUnInteractif(container);
    expect(fautifs, fautifs.join(' | ')).toEqual([]);
  });

  it('la palette du lot est bannie des quatre fichiers, nommément', () => {
    const BANNIES = /\bbg-black\b|\b(bg|text|border)-accent-(cyan|magenta)\b|\b(bg|text|border)-agent-amber\b/;
    for (const fichier of FICHIERS) {
      const fautifs = source(fichier)
        .split('\n')
        .map((ligne, i) => [i + 1, ligne] as const)
        .filter(([, ligne]) => BANNIES.test(ligne))
        .map(([n, ligne]) => `${fichier}:${n} ${ligne.trim().slice(0, 60)}`);
      expect(fautifs, fautifs.join('\n')).toEqual([]);
    }
  });
});

describe('lot 8 (7) : l’overlay', () => {
  it('ne peint plus en noir', () => {
    expect(source('CalendarPanel.tsx')).not.toMatch(/\bbg-black\b/);
    expect(source('CalendarPanel.tsx')).toMatch(/\bbg-bg\/80\b/);
  });
});

describe('lot 8 (8) : le groupe d’actions est poussé à droite', () => {
  it('le parent commun des segments et du grand geste porte `ml-auto`', async () => {
    await monter();
    const groupe = screen.getByRole('group', { name: "Vue de l'agenda" });
    const geste = screen.getByRole('button', { name: /Nouveau rendez-vous/ });
    const parent = groupe.parentElement as HTMLElement;
    expect(parent.contains(geste), 'segments et geste partagent un parent').toBe(true);
    expect(parent.className).toMatch(/\bml-auto\b/);
  });
});

describe('lot 8 (9) : le pied qui nomme l’agenda courant', () => {
  it('agenda local seul : le nom et le suffixe « aucun agenda en ligne branché »', async () => {
    const { container } = await monter();
    expect(container.textContent).toContain('Agenda local « Agenda Atelier »');
    expect(container.textContent).toContain('aucun agenda en ligne branché');
  });

  it('un CalDAV branché retire le suffixe', async () => {
    api.listCalendars.mockResolvedValue([AGENDA_LOCAL, AGENDA_CALDAV]);
    semer({ calendars: [AGENDA_LOCAL, AGENDA_CALDAV] });
    const { container } = await monter();
    expect(container.textContent, "le pied nomme quand même l'agenda courant").toContain('Agenda local « Agenda Atelier »');
    expect(container.textContent).not.toContain('aucun agenda en ligne branché');
  });

  it('aucun agenda du tout : aucun pied (BUG-143)', async () => {
    api.listCalendars.mockResolvedValue([]);
    semer({ calendars: [], currentCalendarId: null, events: [] });
    const { container } = await monter();
    expect(container.querySelector('section[aria-labelledby="agenda-periode"]'), 'la grille est rendue').not.toBeNull();
    expect(container.textContent).not.toContain('aucun agenda en ligne branché');
    expect(container.textContent).not.toContain('Agenda local');
  });
});

describe('lot 8 (10) : le chargement', () => {
  it('chaque rangée porte deux barres, dont la seconde en `flex-1`', async () => {
    let libere: (v: unknown) => void = () => {};
    api.listCalendars.mockReturnValue(new Promise((r) => { libere = r; }));
    semer({ calendars: [], currentCalendarId: null, events: [] });
    // Un compte déjà là : sans lui, `getEmailAuthStatus` retombe sur une liste
    // vide et coupe le chargement avant que la liste d'agendas n'arrive.
    useEmailStore.setState({
      accounts: [{ id: 'a1', email: 'ludo@example.fr', provider: 'gmail' }],
      currentAccountId: 'a1',
      needsReauth: false,
    } as never);
    const { container } = render(<CalendarPanel standalone />);
    await waitFor(() => expect(container.querySelectorAll('[aria-hidden="true"]').length).toBeGreaterThan(0));

    const rangees = [...container.querySelectorAll('div')].filter(
      (d) => /\bflex items-center gap-2\b/.test(d.className) && d.querySelectorAll('[aria-hidden="true"]').length === 2,
    );
    expect(rangees.length, 'trois rangées de squelette').toBe(3);
    for (const rangee of rangees) {
      const barres = [...rangee.querySelectorAll(':scope > [aria-hidden="true"]')];
      expect(barres).toHaveLength(2);
      expect(barres[1].className, 'le second squelette porte flex-1').toMatch(/\bflex-1\b/);
    }
    expect(screen.getByRole('status').textContent).toMatch(/Chargement de l['’]agenda/);
    await act(async () => { libere([]); });
  });
});

describe('lot 8 (11) : le châssis de la branche « grille »', () => {
  it('la vue et le pied partagent un conteneur `h-full flex flex-col`, le pied est `shrink-0`', async () => {
    const { container } = await monter();
    const vue = container.querySelector('section[aria-labelledby="agenda-periode"]') as HTMLElement;
    expect(vue, 'la vue est une section nommée par la période').not.toBeNull();
    const conteneur = vue.parentElement as HTMLElement;
    expect(conteneur.className).toMatch(/\bh-full\b/);
    expect(conteneur.className).toMatch(/\bflex-col\b/);
    const pied = conteneur.lastElementChild as HTMLElement;
    expect(pied).not.toBe(vue);
    expect(pied.className).toMatch(/\bshrink-0\b/);
    expect(pied.textContent).toContain('Agenda local « Agenda Atelier »');
  });

  it('la zone de contenu garde `flex-1 overflow-hidden`', async () => {
    const { container } = await monter();
    const vue = container.querySelector('section[aria-labelledby="agenda-periode"]') as HTMLElement;
    const zone = (vue.parentElement as HTMLElement).parentElement as HTMLElement;
    expect(zone.className).toMatch(/\bflex-1\b/);
    expect(zone.className).toMatch(/\boverflow-hidden\b/);
  });

  it('le formulaire ne reçoit pas le conteneur de la grille', async () => {
    semer({ isEventFormOpen: true });
    const { container } = await monter();
    expect(screen.getByRole('heading', { level: 3, name: 'Nouveau rendez-vous' }), 'le formulaire est rendu').toBeInTheDocument();
    expect(container.querySelector('section[aria-labelledby="agenda-periode"]')).toBeNull();
    expect(container.textContent).not.toContain('Agenda local « Agenda Atelier »');
  });
});
