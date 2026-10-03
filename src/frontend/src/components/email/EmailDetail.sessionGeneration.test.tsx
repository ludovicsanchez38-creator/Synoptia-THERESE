import { cleanup, fireEvent, render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EmailDetail } from './EmailDetail';
import { useEmailStore } from '../../stores/emailStore';
import * as api from '../../services/api';
vi.mock('../../services/api', () => ({ generateEmailResponse: vi.fn(), getEmailMessage: vi.fn(), modifyEmailMessage: vi.fn(), deleteEmailMessage: vi.fn(), createFollowUp: vi.fn() }));
const generation = vi.mocked(api.generateEmailResponse);
function attente() { let resolve!: (x: {
    draft: string;
}) => void; const promise = new Promise<{
    draft: string;
}>(r => { resolve = r; }); return { promise, resolve }; }
function message(id: string) { return { id, thread_id: id, subject: 'Sujet ' + id, from_email: id + '@exemple.test', from_name: id, to_emails: ['profil-jetable@exemple.test'], date: '2026-10-02T12:00:00Z', snippet: 'Texte synthétique', is_read: true, is_starred: false, body_plain: 'Message synthétique ' + id, body_html: null, labels: [], priority: null, priority_score: null }; }
afterEach(cleanup);
beforeEach(() => { vi.clearAllMocks(); useEmailStore.setState({ messages: [message('A'), message('B')], currentMessageId: 'A', isComposing: false, draftRecipients: [], draftSubject: '', draftBody: '' } as never); });
describe('c16 : intégration EmailDetail réelle sans aucune transmission', () => {
    it('Utiliser dans B ne doit pas composer à son destinataire le brouillon tardif de A', async () => {
        const a = attente();
        const b = attente();
        generation.mockReturnValueOnce(a.promise as never).mockReturnValueOnce(b.promise as never);
        const vue = render(<EmailDetail accountId="compte-synthetique" messageId="A"/>);
        fireEvent.click(screen.getByRole('button', { name: 'Générer une réponse' }));
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(1));
        fireEvent.click(screen.getByRole('button', { name: 'Fermer la génération de réponse' }));
        vue.rerender(<EmailDetail accountId="compte-synthetique" messageId="B"/>);
        fireEvent.click(screen.getByRole('button', { name: 'Générer une réponse' }));
        await waitFor(() => expect(generation).toHaveBeenCalledTimes(2));
        await act(async () => { a.resolve({ draft: 'Contenu réservé au destinataire A' }); await a.promise; });
        fireEvent.click(screen.getByRole('button', { name: 'Utiliser' }));
        const s = useEmailStore.getState();
        console.info('OBSERVÉ composition réelle', { recipients: s.draftRecipients, subject: s.draftSubject, body: s.draftBody, isComposing: s.isComposing });
        try {
            expect(s.draftBody).not.toBe('Contenu réservé au destinataire A');
        }
        finally {
            await act(async () => { b.resolve({ draft: 'Contenu destiné à B' }); await b.promise; });
        }
    });
});
