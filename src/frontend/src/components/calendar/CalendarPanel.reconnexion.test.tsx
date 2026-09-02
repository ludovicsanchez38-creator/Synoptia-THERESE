/**
 * B-057 — « Reconnecter » concluait au succès sans vérifier le fournisseur.
 *
 * Le fichier s'impose la règle deux fois ailleurs (lignes 114-124 et 176-180,
 * BUG-162) : « seul un calendrier GOOGLE réellement rendu prouve que le jeton
 * fonctionne. Un succès sur un calendrier local n'apprend rien sur Google et ne
 * doit pas éteindre une vraie expiration. » Le sondage de `handleReauthorize`,
 * lui, jetait la valeur de retour : toute résolution sans exception arrêtait le
 * sondage et éteignait la bannière. Une liste vide, ou un unique agenda local,
 * suffisait — et l'utilisateur croyait le problème réglé pendant que l'agenda
 * restait muet.
 *
 * Le test couvre les trois cas dans l'ordre où ils comptent : rien, du local,
 * puis du Google. Et il vérifie que le sondage S'ARRÊTE au succès, sans quoi le
 * correctif se contenterait de repousser la conclusion.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCalendarStore } from '../../stores/calendarStore';
import { useEmailStore } from '../../stores/emailStore';

const agenda = vi.hoisted(() => ({ reponseCourante: [] as unknown[] }));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    getEmailAuthStatus: vi.fn().mockResolvedValue({ authenticated: true, accounts: [] }),
    listCalendars: vi.fn(() => Promise.resolve(agenda.reponseCourante as never)),
    listEvents: vi.fn().mockResolvedValue([]),
    reauthorizeEmail: vi.fn().mockResolvedValue({ auth_url: 'https://accounts.example/oauth' }),
  };
});

import * as api from '../../services/api';
import { CalendarPanel } from './CalendarPanel';

const banniere = () => screen.queryByText(/Connexion Google expirée/);

describe('B-057 — la reconnexion exige un agenda Google réellement rendu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    agenda.reponseCourante = [];
    useCalendarStore.setState({
      calendars: [], currentCalendarId: null, events: [], currentEventId: null,
      isEventFormOpen: false, draftEvent: {},
    });
    useEmailStore.setState({
      accounts: [{ id: 'a1', email: 'ludo@example.fr', provider: 'gmail' }] as never,
      currentAccountId: 'a1',
      needsReauth: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('ni une liste vide ni un agenda local n’éteignent la bannière ; un agenda Google l’éteint et arrête le sondage', async () => {
    render(<CalendarPanel standalone />);
    await act(async () => { await Promise.resolve(); });
    expect(banniere()).not.toBeNull();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Reconnecter/ }));
    });
    // `handleReauthorize` enchaîne un appel réseau puis un `import()` dynamique
    // du plugin shell avant de poser l'intervalle : plusieurs tours de
    // micro-tâches séparent le clic de l'armement du sondage.
    for (let tour = 0; tour < 10; tour++) {
      await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    }
    // Le bouton passe en « En attente... » : le sondage est bien armé.
    expect(screen.getByText('En attente...')).toBeInTheDocument();

    // 1. Le fournisseur ne rend rien : rien n'est prouvé, le sondage continue.
    const apresClic = vi.mocked(api.listCalendars).mock.calls.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(vi.mocked(api.listCalendars).mock.calls.length).toBeGreaterThan(apresClic);
    expect(banniere()).not.toBeNull();

    // 2. Un agenda local répond : il n'apprend rien sur Google.
    agenda.reponseCourante = [{ id: 'loc', provider: 'local', summary: 'Mon calendrier' }];
    const apresVide = vi.mocked(api.listCalendars).mock.calls.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(vi.mocked(api.listCalendars).mock.calls.length).toBeGreaterThan(apresVide);
    expect(banniere()).not.toBeNull();

    // 3. Google répond enfin : la bannière s'éteint.
    agenda.reponseCourante = [{ id: 'g1', provider: 'google', summary: 'Agenda', primary: true }];
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(banniere()).toBeNull();

    // ... et le sondage s'arrête : plus aucun appel sur les tours suivants.
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    const apresSucces = vi.mocked(api.listCalendars).mock.calls.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(9000); });
    expect(vi.mocked(api.listCalendars).mock.calls.length).toBe(apresSucces);
  });
});
