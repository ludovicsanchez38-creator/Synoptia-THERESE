/**
 * B-220 : quatre boutons en icône seule de l'Agenda ne s'annonçaient que
 * « bouton » — rafraîchir, importer un .ics, mois précédent, mois suivant.
 *
 * Le voisin immédiat (« Exporter en .ics ») portait déjà son `title` : l'oubli
 * était local, pas systémique. Le test recense TOUS les boutons du panneau
 * plutôt que les quatre connus : un cinquième bouton muet ajouté demain doit
 * échouer ici, pas passer parce que la liste était figée.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: false, accounts: [] }),
    listCalendars: vi.fn().mockResolvedValue([]),
    listEvents: vi.fn().mockResolvedValue([]),
  };
});

import { CalendarPanel } from './CalendarPanel';

/** Le nom accessible d'un bouton en icône seule : son texte, sinon un
 *  `aria-label`, un `title` ou l'élément désigné par `aria-labelledby`. */
function nomAccessible(bouton: HTMLButtonElement): string {
  const texte = bouton.textContent?.trim();
  if (texte) return texte;
  const label = bouton.getAttribute('aria-label')?.trim();
  if (label) return label;
  const title = bouton.getAttribute('title')?.trim();
  if (title) return title;
  const idsDecrits = bouton.getAttribute('aria-labelledby');
  if (idsDecrits) {
    return idsDecrits
      .split(/\s+/)
      .map((id) => document.getElementById(id)?.textContent?.trim() ?? '')
      .join(' ')
      .trim();
  }
  return '';
}

describe("B-220 : aucun bouton de l'Agenda ne s'annonce seulement « bouton »", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalendarStore.setState({
      calendars: [], currentCalendarId: null, events: [], currentEventId: null,
      isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({ accounts: [], currentAccountId: null, needsReauth: false });
  });

  it('chaque bouton du panneau porte un nom', async () => {
    const { container } = render(<CalendarPanel standalone />);
    await waitFor(() => expect(screen.getByText('Agenda')).toBeInTheDocument());

    const boutons = [...container.querySelectorAll('button')] as HTMLButtonElement[];
    // Sans cette borne, une régression de rendu (panneau vide) rendrait le
    // test vert sans avoir examiné le moindre bouton.
    expect(boutons.length).toBeGreaterThanOrEqual(8);

    const muets = boutons
      .filter((bouton) => nomAccessible(bouton) === '')
      .map((bouton) => bouton.querySelector('svg')?.getAttribute('class') ?? '(sans icône)');
    expect(muets, `boutons sans nom accessible : ${muets.join(', ')}`).toEqual([]);
  });

  it('les quatre boutons du bug se nomment', async () => {
    render(<CalendarPanel standalone />);
    await waitFor(() => expect(screen.getByText('Agenda')).toBeInTheDocument());

    for (const nom of [/synchroniser/i, /importer/i, /précédent/i, /suivant/i]) {
      expect(screen.getByRole('button', { name: nom })).toBeInTheDocument();
    }
  });
});
