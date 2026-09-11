/**
 * DA « Application affinée », lot 8 : le formulaire de rendez-vous
 * (`docs/plans/2026-09-11-da-lot8-agenda-design.md`, § 9).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, createEvent: vi.fn(), updateEvent: vi.fn() };
});

import { EventForm } from './EventForm';

const AGENDA = {
  id: 'cal-1', account_id: null, summary: 'Agenda Atelier', description: null,
  timezone: 'Europe/Paris', primary: true, provider: 'local', synced_at: null,
} as never;

function monter() {
  return render(
    <PrototypeExternalActionConfirmationProvider>
      <EventForm />
    </PrototypeExternalActionConfirmationProvider>,
  );
}

const IDS: [RegExp, string][] = [
  [/^Titre/, 'eventform-titre'],
  [/^Date de début/, 'eventform-date-de-debut'],
  [/^Heure de début/, 'eventform-heure-de-debut'],
  [/^Date de fin/, 'eventform-date-de-fin'],
  [/^Heure de fin/, 'eventform-heure-de-fin'],
  [/^Lieu ou visio/, 'eventform-lieu'],
  [/^Description/, 'eventform-description'],
  [/^Participants/, 'eventform-participants'],
  [/^Agenda/, 'eventform-agenda'],
];

beforeEach(() => {
  vi.clearAllMocks();
  useCalendarStore.setState({
    calendars: [AGENDA], currentCalendarId: 'cal-1', currentEventId: null,
    events: [], isEventFormOpen: true, draftEvent: {},
  } as never);
  useEmailStore.setState({ currentAccountId: null } as never);
});

describe('lot 8 : les champs gardent leurs identifiants et leurs libellés', () => {
  it('chaque champ répond à son libellé par `htmlFor`', () => {
    monter();
    for (const [libelle, id] of IDS) {
      const champ = screen.getByLabelText(libelle);
      expect(champ.id, `« ${libelle} » doit porter ${id}`).toBe(id);
    }
  });

  it('la case « toute la journée » vit hors de FormField', () => {
    const { container } = monter();
    const case_ = screen.getByLabelText('Événement sur toute la journée') as HTMLInputElement;
    expect(case_.type).toBe('checkbox');
    expect(case_.id).toBe('all-day');
    const etiquette = container.querySelector('label[for="all-day"]') as HTMLElement;
    expect(etiquette.className, "le label d'une case est à côté, pas au-dessus").not.toMatch(/\bblock\b/);
  });

  it('la description ne prend pas de poignée de redimensionnement', () => {
    monter();
    const description = screen.getByLabelText(/^Description/) as HTMLTextAreaElement;
    expect(description.tagName).toBe('TEXTAREA');
    // La primitive rend `resize-y` dès qu'elle n'auto-grandit pas : sur ce
    // champ, `main` posait `resize-none`, et la poignée n'est pas au design.
    expect(description.className).toMatch(/\bresize-none\b/);
    expect(description.className).not.toMatch(/\bresize-y\b/);
  });

  it('l’aide des participants est reliée au champ, et se lit avant lui', () => {
    const { container } = monter();
    const champ = screen.getByLabelText(/^Participants/) as HTMLInputElement;
    const aide = container.querySelector('#eventform-participants-desc') as HTMLElement;
    expect(aide, 'la description est rendue par FormField').not.toBeNull();
    expect(aide.textContent).toBe('Séparez les emails par des virgules');
    expect(champ.getAttribute('aria-describedby')).toContain('eventform-participants-desc');
    // Position assumée au design (§ 6) : une consigne de saisie se lit avant
    // le champ, et `aria-describedby` l'annonce désormais au lecteur d'écran.
    expect(aide.compareDocumentPosition(champ) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('le titre et le geste d’enregistrement sont ceux du lot', () => {
    monter();
    expect(screen.getByRole('heading', { level: 3, name: 'Nouveau rendez-vous' })).toBeInTheDocument();
    const enregistrer = screen.getByRole('button', { name: /Enregistrer/ });
    expect(enregistrer.className).toMatch(/\bh-9\b/);
    expect(screen.getByRole('button', { name: 'Retour' })).toBeInTheDocument();
  });
});

describe('lot 8 : l’obligation ne sort pas du nom accessible', () => {
  it('les cinq champs obligatoires portent `required`', () => {
    monter();
    for (const libelle of [/^Titre/, /^Date de début/, /^Heure de début/, /^Date de fin/, /^Heure de fin/]) {
      expect(screen.getByLabelText(libelle)).toBeRequired();
    }
  });

  it('sur toute la journée, les deux heures sortent du DOM et les trois autres restent requis', () => {
    monter();
    fireEvent.click(screen.getByLabelText('Événement sur toute la journée'));
    expect(screen.queryByLabelText(/^Heure de début/)).toBeNull();
    expect(screen.queryByLabelText(/^Heure de fin/)).toBeNull();
    expect(screen.getByLabelText(/^Titre/)).toBeRequired();
    expect(screen.getByLabelText(/^Date de début/)).toBeRequired();
    expect(screen.getByLabelText(/^Date de fin/)).toBeRequired();
  });

  it('le champ « Agenda » n’est pas requis, il est en lecture seule', () => {
    monter();
    const agenda = screen.getByLabelText(/^Agenda/) as HTMLInputElement;
    expect(agenda).not.toBeRequired();
    expect(agenda.readOnly).toBe(true);
    expect(agenda.getAttribute('aria-readonly')).toBe('true');
    expect(agenda.disabled, 'un champ désactivé sort de la tabulation').toBe(false);
    expect(agenda.value).toBe('Agenda Atelier');
  });

  it('sans agenda sélectionné, le champ reste contrôlé et vide', () => {
    useCalendarStore.setState({ calendars: [], currentCalendarId: null } as never);
    monter();
    expect((screen.getByLabelText(/^Agenda/) as HTMLInputElement).value).toBe('');
  });
});

describe('lot 8 : un seul bandeau d’erreur, pour les deux sources', () => {
  it('l’erreur de saisie s’affiche une seule fois', () => {
    monter();
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    const bandeaux = screen.getAllByRole('alert');
    expect(bandeaux).toHaveLength(1);
    expect(bandeaux[0].textContent).toContain('Ajoute un titre');
  });

  it('le garde-fou « aucun calendrier » passe par le même bandeau', () => {
    useCalendarStore.setState({ calendars: [], currentCalendarId: null } as never);
    monter();
    fireEvent.change(screen.getByPlaceholderText("Titre de l'événement"), { target: { value: 'Point projet' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/ }));
    const bandeaux = screen.getAllByRole('alert');
    expect(bandeaux).toHaveLength(1);
    expect(bandeaux[0].textContent).toMatch(/Aucun calendrier sélectionné/);
  });
});
