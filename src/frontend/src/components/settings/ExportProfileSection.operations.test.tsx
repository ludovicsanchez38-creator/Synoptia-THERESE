import { cleanup, fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ExportProfileSection } from './ExportProfileSection';
import * as api from '../../services/api/exportProfile';
import { useStatusStore } from '../../stores/statusStore';
vi.mock('../../services/api/exportProfile', () => ({ getExportProfile: vi.fn(), saveExportProfile: vi.fn(), resetExportProfile: vi.fn() }));
const profil = { version: 1, language: 'fr-FR', body_font: 'Calibri', body_size_pt: 11, heading_font: 'Outfit', title_color: '#0F1E6D', heading_color: '#0F1E6D', h2_color: '#1733A6', body_color: '#1A1A2E', footer_text: 'Profil synthétique', margins_cm: { top: 2.5, bottom: 2.5, left: 2.5, right: 2.5 } };
function attente<T>() { let resolve!: (x: T) => void; const promise = new Promise<T>(r => { resolve = r; }); return { promise, resolve }; }
afterEach(cleanup);
beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.getExportProfile).mockReset().mockResolvedValue({ profile: profil, warning: null }); vi.mocked(api.resetExportProfile).mockReset(); useStatusStore.setState({ notifications: [] }); });
describe('Relecture c16 : import/export sous réponse différée', () => {
    it('l’import bloque les opérations concurrentes et préserve une nouvelle marge malgré la réponse de profil', async () => {
        const texte = attente<string>();
        const sauvegarde = attente<{
            profile: typeof profil;
            warning: null;
        }>();
        vi.mocked(api.saveExportProfile).mockReturnValueOnce(sauvegarde.promise);
        const vue = render(<ExportProfileSection />);
        await screen.findByDisplayValue('fr-FR');
        const f = new File(['profil synthétique'], 'profil.json', { type: 'application/json' });
        Object.defineProperty(f, 'text', { value: () => texte.promise });
        const input = vue.container.querySelector('input[type="file"]')!;
        fireEvent.change(input, { target: { files: [f] } });
        expect(screen.getByRole('button', { name: 'Réinitialiser' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Importer JSON' })).toBeDisabled();
        expect(input).toBeDisabled();
        fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser' }));
        expect(api.resetExportProfile).not.toHaveBeenCalled();
        fireEvent.change(screen.getByLabelText('Gauche'), { target: { value: '3.5' } });
        await act(async () => { texte.resolve(JSON.stringify({ ...profil, body_size_pt: '12', language: 'de-DE' })); await texte.promise; });
        await waitFor(() => expect(api.saveExportProfile).toHaveBeenCalledTimes(1));
        await act(async () => { sauvegarde.resolve({ profile: { ...profil, body_size_pt: 12, language: 'de-DE' }, warning: null }); await sauvegarde.promise; });
        expect(screen.getByLabelText('Gauche')).toHaveValue(3.5);
        expect(useStatusStore.getState().notifications.at(-1)?.message).toBe('Tes modifications plus récentes restent à enregistrer.');
        expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeEnabled();
        console.info('IMPORT OBSERVÉ', { margeAffichee: (screen.getByLabelText('Gauche') as HTMLInputElement).value, notification: useStatusStore.getState().notifications.at(-1) });
    });
    it('une réinitialisation suivie d’un GET en échec ne doit pas annoncer le profil courant comme restauré', async () => {
        vi.mocked(api.getExportProfile).mockResolvedValueOnce({ profile: { ...profil, language: 'de-DE' }, warning: null }).mockRejectedValueOnce(new Error('Lecture de profil indisponible'));
        vi.mocked(api.resetExportProfile).mockResolvedValue(undefined);
        const journal = vi.spyOn(console, 'error').mockImplementation(() => { });
        render(<ExportProfileSection />);
        await screen.findByDisplayValue('de-DE');
        fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser' }));
        await waitFor(() => expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeEnabled());
        const notifications = useStatusStore.getState().notifications;
        console.info('RESET OBSERVÉ', { langue: (screen.getByLabelText('Langue du document') as HTMLInputElement).value, notifications: notifications.map(n => ({ type: n.type, title: n.title, message: n.message })), erreurJournal: journal.mock.calls });
        try {
            expect(notifications.at(-1)?.type).toBe('error');
        }
        finally {
            journal.mockRestore();
        }
    });
});
