/**
 * B-378 (05/09/2026) : « 0 calendrier importé. Il apparaîtra à la prochaine
 * ouverture de l'Agenda. » en vert : une promesse pour rien.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ testCaldavConnection: vi.fn(), setupCaldavCalendars: vi.fn() }));
vi.mock('../../services/api/calendar', async () => {
  const actual = await vi.importActual<typeof import('../../services/api/calendar')>('../../services/api/calendar');
  return { ...actual, testCaldavConnection: apiMocks.testCaldavConnection, setupCaldavCalendars: apiMocks.setupCaldavCalendars };
});

import { CalDAVSection } from './CalDAVSection';

describe('B-378 - zéro calendrier importé est dit tel quel', () => {
  it("ne promet pas l'Agenda pour zéro calendrier", async () => {
    apiMocks.setupCaldavCalendars.mockResolvedValueOnce([]);
    render(<CalDAVSection />);
    fireEvent.change(screen.getByLabelText(/Adresse du serveur/i), { target: { value: 'https://cal.test/' } });
    fireEvent.change(screen.getByLabelText(/Identifiant/i), { target: { value: 'marie' } });
    fireEvent.change(screen.getByLabelText(/Mot de passe/i), { target: { value: 'x' } });
    fireEvent.click(screen.getByRole('button', { name: /Enregistrer/i }));

    await waitFor(() => expect(apiMocks.setupCaldavCalendars).toHaveBeenCalled());
    const message = await screen.findByText(/aucun calendrier/i);
    expect(message.textContent).not.toMatch(/apparaîtra/);
  });
});
