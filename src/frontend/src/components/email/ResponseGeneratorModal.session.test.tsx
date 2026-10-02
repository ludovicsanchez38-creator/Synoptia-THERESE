import { cleanup, fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ResponseGeneratorModal } from './ResponseGeneratorModal';
import * as api from '../../services/api';
vi.mock('../../services/api', () => ({ generateEmailResponse: vi.fn() }));
const generation = vi.mocked(api.generateEmailResponse);
function attente() { let resolve!: (value: {
    draft: string;
}) => void; const promise = new Promise<{
    draft: string;
}>(r => { resolve = r; }); return { promise, resolve }; }
function props(messageId = 'mail-A', isOpen = true) { return { isOpen, onClose: vi.fn(), messageId, accountId: 'compte-synthetique', onUseResponse: vi.fn() }; }
afterEach(cleanup);
beforeEach(() => { vi.clearAllMocks(); });
describe('Lecture indépendante c16 : génération de réponse, session et résultat tardif', () => {
    it('témoin sain : un résultat de la session courante devient utilisable', async () => {
        generation.mockResolvedValue({ draft: 'Réponse courante synthétique' } as never);
        render(<ResponseGeneratorModal {...props()}/>);
        await waitFor(() => expect(screen.getByRole('textbox', { name: 'Brouillon de réponse' })).toHaveValue('Réponse courante synthétique'));
        expect(screen.getByRole('button', { name: 'Utiliser' })).toBeEnabled();
        expect(generation).toHaveBeenCalledTimes(1);
    });
    it('une réponse arrivée après fermeture ne doit pas supprimer la nouvelle génération à la réouverture', async () => {
        const ancienne = attente();
        generation.mockReturnValueOnce(ancienne.promise as never);
        const courant = props();
        const vue = render(<ResponseGeneratorModal {...courant}/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(1));
        vue.rerender(<ResponseGeneratorModal {...courant} isOpen={false}/>);
        await act(async () => { ancienne.resolve({ draft: 'Brouillon tardif de la session fermée' }); await ancienne.promise; });
        generation.mockResolvedValueOnce({ draft: 'Réponse fraîche attendue' } as never);
        vue.rerender(<ResponseGeneratorModal {...courant}/>);
        console.info('OBSERVÉ après réouverture', { appels: generation.mock.calls.length, brouillon: (screen.getByRole('textbox', { name: 'Brouillon de réponse' }) as HTMLTextAreaElement).value, utiliserDesactive: (screen.getByRole('button', { name: 'Utiliser' }) as HTMLButtonElement).disabled });
        expect(generation).toHaveBeenCalledTimes(2);
    });
    it('la réponse du message A ne doit pas activer Utiliser pendant la génération du message B', async () => {
        const a = attente();
        const b = attente();
        generation.mockReturnValueOnce(a.promise as never).mockReturnValueOnce(b.promise as never);
        const courant = props();
        const vue = render(<ResponseGeneratorModal {...courant}/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(1));
        vue.rerender(<ResponseGeneratorModal {...courant} isOpen={false}/>);
        vue.rerender(<ResponseGeneratorModal {...courant} messageId="mail-B"/>);
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(2));
        await act(async () => { a.resolve({ draft: 'Texte réservé au message A' }); await a.promise; });
        console.info('OBSERVÉ pendant B', { appelB: generation.mock.calls[1], brouillon: (screen.getByRole('textbox', { name: 'Brouillon de réponse' }) as HTMLTextAreaElement).value, utiliserDesactive: (screen.getByRole('button', { name: 'Utiliser' }) as HTMLButtonElement).disabled });
        expect(screen.getByRole('button', { name: 'Utiliser' })).toBeDisabled();
        b.resolve({ draft: 'Texte réservé au message B' });
    });
});
