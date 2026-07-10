/**
 * Chantier 5 - section Réglages > Données : profil d'export DOCX.
 * Charge le profil, affiche l'avertissement si le fichier est illisible,
 * enregistre les modifications (PUT), réinitialise (DELETE).
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ExportProfileSection } from './ExportProfileSection';
import { getExportProfile, saveExportProfile } from '../../services/api/exportProfile';

vi.mock('../../services/api/exportProfile', () => ({
  getExportProfile: vi.fn(),
  saveExportProfile: vi.fn(),
  resetExportProfile: vi.fn(),
}));

const mockedGet = vi.mocked(getExportProfile);
const mockedSave = vi.mocked(saveExportProfile);

const PROFILE = {
  version: 1,
  language: 'fr-FR',
  body_font: 'Calibri',
  body_size_pt: 11,
  heading_font: 'Outfit',
  title_color: '#0F1E6D',
  heading_color: '#0F1E6D',
  h2_color: '#1733A6',
  body_color: '#1A1A2E',
  footer_text: 'Généré par THÉRÈSE - Synoptïa',
  margins_cm: { top: 2.5, bottom: 2.5, left: 2.5, right: 2.5 },
};

describe('ExportProfileSection', () => {
  beforeEach(() => {
    mockedGet.mockReset();
    mockedSave.mockReset();
  });

  it('charge et affiche le profil courant', async () => {
    mockedGet.mockResolvedValue({ profile: PROFILE, warning: null });
    render(<ExportProfileSection />);
    await waitFor(() => expect(screen.getByDisplayValue('fr-FR')).toBeInTheDocument());
    expect(screen.getByDisplayValue('Calibri')).toBeInTheDocument();
    expect(screen.getByDisplayValue(/Généré par THÉRÈSE/)).toBeInTheDocument();
  });

  it("affiche l'avertissement quand le fichier est illisible", async () => {
    mockedGet.mockResolvedValue({
      profile: PROFILE,
      warning: 'Profil d\'export illisible : les réglages par défaut sont utilisés.',
    });
    render(<ExportProfileSection />);
    await waitFor(() =>
      expect(screen.getByText(/illisible/i)).toBeInTheDocument()
    );
  });

  it('enregistre les modifications', async () => {
    mockedGet.mockResolvedValue({ profile: PROFILE, warning: null });
    mockedSave.mockResolvedValue({ profile: PROFILE, warning: null });
    render(<ExportProfileSection />);
    await waitFor(() => expect(screen.getByDisplayValue('fr-FR')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/langue/i), { target: { value: 'de-DE' } });
    fireEvent.click(screen.getByRole('button', { name: /enregistrer/i }));

    await waitFor(() => expect(mockedSave).toHaveBeenCalled());
    expect(mockedSave.mock.calls[0][0].language).toBe('de-DE');
  });
});
