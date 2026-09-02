/**
 * B-129 : les deux routes CalDAV n'avaient aucune surface cliente.
 *
 * `POST /api/calendar/calendars/caldav-setup` et `.../caldav-test` existent
 * depuis longtemps, et la création d'un calendrier `provider_type=caldav`
 * répond même un 400 qui RENVOIE l'utilisateur vers `caldav-setup`. Or aucun
 * fichier de `src/frontend/src` ne mentionnait ces routes : le message
 * d'erreur désignait une porte qui n'existait pas côté client, et personne ne
 * pouvait brancher un calendrier CalDAV depuis l'application.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CalDAVSection } from './CalDAVSection';

const apiMocks = vi.hoisted(() => ({
  testCaldavConnection: vi.fn(),
  setupCaldavCalendars: vi.fn(),
}));

vi.mock('../../services/api/calendar', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/calendar')>(
    '../../services/api/calendar',
  );
  return {
    ...actual,
    testCaldavConnection: apiMocks.testCaldavConnection,
    setupCaldavCalendars: apiMocks.setupCaldavCalendars,
  };
});

function remplirLeFormulaire() {
  fireEvent.change(screen.getByLabelText(/Adresse du serveur/i), {
    target: { value: 'https://cloud.exemple.fr/remote.php/dav' },
  });
  fireEvent.change(screen.getByLabelText(/Identifiant/i), {
    target: { value: 'ludo' },
  });
  fireEvent.change(screen.getByLabelText(/Mot de passe/i), {
    target: { value: 'motdepasse-application' },
  });
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('B-129 : brancher un calendrier CalDAV depuis les Réglages', () => {
  it('teste la connexion et annonce les calendriers trouvés', async () => {
    apiMocks.testCaldavConnection.mockResolvedValue({
      success: true,
      message: 'Connected successfully. Found 2 calendar(s).',
      calendars: [
        { id: 'perso', name: 'Personnel' },
        { id: 'pro', name: 'Professionnel' },
      ],
    });

    render(<CalDAVSection />);
    remplirLeFormulaire();
    fireEvent.click(screen.getByRole('button', { name: /Tester/i }));

    await waitFor(() => {
      expect(apiMocks.testCaldavConnection).toHaveBeenCalledWith({
        url: 'https://cloud.exemple.fr/remote.php/dav',
        username: 'ludo',
        password: 'motdepasse-application',
      });
    });
    expect(await screen.findByText('Personnel')).toBeInTheDocument();
    expect(screen.getByText('Professionnel')).toBeInTheDocument();
  });

  it('un test qui échoue est dit, et rien n’est enregistré', async () => {
    apiMocks.testCaldavConnection.mockResolvedValue({
      success: false,
      message: 'Connection failed: 401 Unauthorized',
      calendars: [],
    });

    render(<CalDAVSection />);
    remplirLeFormulaire();
    fireEvent.click(screen.getByRole('button', { name: /Tester/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/401/);
    expect(apiMocks.setupCaldavCalendars).not.toHaveBeenCalled();
  });

  it('enregistrer importe les calendriers par la route caldav-setup', async () => {
    apiMocks.setupCaldavCalendars.mockResolvedValue([
      { id: 'c1', summary: 'Personnel', provider: 'caldav' },
    ]);

    render(<CalDAVSection />);
    remplirLeFormulaire();
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/i }));

    await waitFor(() => {
      expect(apiMocks.setupCaldavCalendars).toHaveBeenCalledWith({
        url: 'https://cloud.exemple.fr/remote.php/dav',
        username: 'ludo',
        password: 'motdepasse-application',
      });
    });
    expect(await screen.findByText(/1 calendrier/i)).toBeInTheDocument();
  });

  it('un enregistrement refusé par le serveur est dit', async () => {
    apiMocks.setupCaldavCalendars.mockRejectedValue(
      new Error('Connection failed: 403 Forbidden'),
    );

    render(<CalDAVSection />);
    remplirLeFormulaire();
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/403/);
  });

  it('le mot de passe n’est pas affiché en clair', () => {
    render(<CalDAVSection />);
    expect(screen.getByLabelText(/Mot de passe/i)).toHaveAttribute('type', 'password');
  });

  it('la section est bien montée dans les Réglages (une porte orpheline n’en est pas une)', async () => {
    const { readFileSync } = await import('node:fs');
    const { resolve } = await import('node:path');
    const servicesTab = readFileSync(
      resolve(process.cwd(), 'src/components/settings/ServicesTab.tsx'),
      'utf-8',
    );
    expect(servicesTab).toContain('<CalDAVSection');
    expect(servicesTab).toContain("from './CalDAVSection'");
  });
});
