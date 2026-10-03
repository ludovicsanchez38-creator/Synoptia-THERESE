import { cleanup, fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ExportProfileSection } from './ExportProfileSection';
import * as api from '../../services/api/exportProfile';
import { useStatusStore } from '../../stores/statusStore';
vi.mock('../../services/api/exportProfile', () => ({ getExportProfile: vi.fn(), saveExportProfile: vi.fn(), resetExportProfile: vi.fn() }));
const profil = { version: 1, language: 'fr-FR', body_font: 'Calibri', body_size_pt: 11, heading_font: 'Outfit', title_color: '#0F1E6D', heading_color: '#0F1E6D', h2_color: '#1733A6', body_color: '#1A1A2E', footer_text: 'Profil synthétique', margins_cm: { top: 2.5, bottom: 2.5, left: 2.5, right: 2.5 } };
afterEach(cleanup);
beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.getExportProfile).mockResolvedValue({ profile: profil, warning: null }); useStatusStore.setState({ notifications: [] }); });
describe('c16 : conservation des saisies du profil d’export', () => {
    it('témoin sain : une sauvegarde sans nouvelle saisie conserve la valeur confirmée', async () => {
        vi.mocked(api.saveExportProfile).mockResolvedValue({ profile: { ...profil, language: 'de-DE' }, warning: null });
        render(<ExportProfileSection />);
        await screen.findByDisplayValue('fr-FR');
        fireEvent.change(screen.getByLabelText('Langue du document'), { target: { value: 'de-DE' } });
        fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
        await waitFor(() => expect(useStatusStore.getState().notifications[0]?.type).toBe('success'));
        expect(screen.getByLabelText('Langue du document')).toHaveValue('de-DE');
    });
    it('une saisie admise pendant la sauvegarde ne doit pas disparaître à sa réponse', async () => {
        let resolve!: (r: {
            profile: typeof profil;
            warning: null;
        }) => void;
        const attente = new Promise<{
            profile: typeof profil;
            warning: null;
        }>(r => { resolve = r; });
        vi.mocked(api.saveExportProfile).mockReturnValueOnce(attente);
        render(<ExportProfileSection />);
        await screen.findByDisplayValue('fr-FR');
        fireEvent.change(screen.getByLabelText('Langue du document'), { target: { value: 'de-DE' } });
        fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
        await waitFor(() => expect(api.saveExportProfile).toHaveBeenCalledTimes(1));
        const champ = screen.getByLabelText('Langue du document');
        expect(champ).toBeEnabled();
        fireEvent.change(champ, { target: { value: 'it-IT' } });
        expect(champ).toHaveValue('it-IT');
        await act(async () => { resolve({ profile: { ...profil, language: 'de-DE' }, warning: null }); await attente; });
        console.info('OBSERVÉ réponse de sauvegarde', { envoye: vi.mocked(api.saveExportProfile).mock.calls[0][0].language, saisiePendantAttente: 'it-IT', affiche: (champ as HTMLInputElement).value, notification: useStatusStore.getState().notifications.at(-1)?.title });
        expect(champ).toHaveValue('it-IT');
    });
});
