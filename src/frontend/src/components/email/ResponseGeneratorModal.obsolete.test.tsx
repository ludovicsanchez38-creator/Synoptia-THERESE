import { cleanup, fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ResponseGeneratorModal } from './ResponseGeneratorModal';
import * as api from '../../services/api';
vi.mock('../../services/api', () => ({ generateEmailResponse: vi.fn() }));
const generation = vi.mocked(api.generateEmailResponse);
function attente() { let resolve!: (x: {
    draft: string;
}) => void; let reject!: (x: Error) => void; const promise = new Promise<{
    draft: string;
}>((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
function props() { return { isOpen: true, onClose: vi.fn(), messageId: 'A', accountId: 'compte-1', onUseResponse: vi.fn() }; }
afterEach(cleanup);
beforeEach(() => { vi.clearAllMocks(); });
describe('Relecture c16 : les réponses et erreurs obsolètes ne pilotent pas la session courante', () => {
    it('message changé sans fermer : erreur/finally de A ignorés, B reste en attente puis devient utilisable', async () => {
        const a = attente();
        const b = attente();
        generation.mockReturnValueOnce(a.promise as never).mockReturnValueOnce(b.promise as never);
        const h = props();
        const vue = render(<ResponseGeneratorModal {...h}/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(1));
        vue.rerender(<ResponseGeneratorModal {...h} messageId="B"/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(2));
        await act(async () => { a.reject(new Error('Erreur privée appartenant au message A')); try {
            await a.promise;
        }
        catch { /*témoin attendu*/ } });
        expect(screen.queryByText('Erreur privée appartenant au message A')).toBeNull();
        expect(screen.getByRole('textbox', { name: 'Brouillon de réponse' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Utiliser' })).toBeDisabled();
        await act(async () => { b.resolve({ draft: 'Réponse de B' }); await b.promise; });
        expect(screen.getByRole('textbox', { name: 'Brouillon de réponse' })).toHaveValue('Réponse de B');
        fireEvent.click(screen.getByRole('button', { name: 'Utiliser' }));
        expect(h.onUseResponse).toHaveBeenCalledTimes(1);
        expect(h.onUseResponse).toHaveBeenCalledWith('Réponse de B');
    });
    it('compte changé sans fermer et même UID : le vieux résultat ne remplace pas la réponse du nouveau compte', async () => {
        const a = attente();
        const b = attente();
        generation.mockReturnValueOnce(a.promise as never).mockReturnValueOnce(b.promise as never);
        const h = props();
        const vue = render(<ResponseGeneratorModal {...h}/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(1));
        vue.rerender(<ResponseGeneratorModal {...h} accountId="compte-2"/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(2));
        expect(generation.mock.calls[1]).toEqual(['A', 'compte-2', 'formal', 'medium']);
        await act(async () => { b.resolve({ draft: 'Réponse compte-2' }); await b.promise; });
        await act(async () => { a.resolve({ draft: 'Réponse privée compte-1' }); await a.promise; });
        expect(screen.getByRole('textbox', { name: 'Brouillon de réponse' })).toHaveValue('Réponse compte-2');
        expect(screen.getByRole('button', { name: 'Utiliser' })).toBeEnabled();
        fireEvent.click(screen.getByRole('button', { name: 'Utiliser' }));
        expect(h.onUseResponse).toHaveBeenCalledWith('Réponse compte-2');
    });
});
