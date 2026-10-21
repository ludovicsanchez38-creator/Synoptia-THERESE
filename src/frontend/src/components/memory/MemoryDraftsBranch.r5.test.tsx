import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { MemoryDraftsBranch } from './MemoryDraftsBranch';
import * as api from '../../services/api/memoryDrafts';
import { useEmailStore } from '../../stores/emailStore';
import { useDemoStore } from '../../stores/demoStore';
vi.mock('../../services/api/memoryDrafts', () => ({ listMemoryDrafts: vi.fn(), getLocalEmailDraft: vi.fn() }));
vi.mock('../../services/api/invoices', () => ({ getInvoice: vi.fn().mockResolvedValue({ id: 'facture', status: 'draft' }) }));
vi.mock('../invoices/InvoiceForm', () => ({ InvoiceForm: ({ invoice }: { invoice: { id: string } }) => <p>Éditeur facture {invoice.id}</p> }));
vi.mock('../documents/DocumentWorkspace', () => ({ DocumentWorkspace: ({ documentId }: { documentId: string }) => <p>Éditeur document {documentId}</p> }));
vi.mock('../email/EmailCompose', () => ({ EmailCompose: ({ draftId }: { draftId?: string }) => <p>Éditeur mail {draftId || 'temporaire'}</p> }));
beforeEach(() => {
  vi.clearAllMocks(); useDemoStore.setState({ enabled: false });
  useEmailStore.getState().clearDraft(); useEmailStore.setState({ isComposing: false });
  vi.mocked(api.listMemoryDrafts).mockResolvedValue({ total: 4, items: [
    { id: 'facture', kind: 'facture', title: 'Facture fictive', status: 'draft' },
    { id: 'devis', kind: 'devis', title: 'Devis fictif', status: 'draft' },
    { id: 'document', kind: 'document', title: 'Document fictif', status: 'en_cours' },
    { id: 'mail', kind: 'email', title: 'Mail fictif', account_id: 'compte', status: 'draft' },
  ] });
  vi.mocked(api.getLocalEmailDraft).mockResolvedValue({ id: 'mail', account_id: 'compte', subject: 'Mail fictif',
    to_emails: ['fictif@example.test'], cc_emails: [], bcc_emails: [], body_plain: 'Texte fictif', body_html: null });
});
it.each(['Facture fictive', 'Devis fictif', 'Document fictif', 'Mail fictif'])('ouvre le véritable éditeur : %s', async title => {
  render(<MemoryDraftsBranch />);
  fireEvent.click(await screen.findByRole('button', { name: title }));
  expect(await screen.findByText(/Éditeur/)).toBeVisible();
  expect(api.listMemoryDrafts).toHaveBeenCalledTimes(1);
});
it('sépare la saisie temporaire et ne l’écrase pas en ouvrant un mail sauvegardé', async () => {
  useEmailStore.getState().startComposing([], 'Saisie temporaire', 'Ne pas perdre');
  render(<MemoryDraftsBranch />);
  expect(screen.getByRole('button', { name: 'En cours de saisie' })).toBeVisible();
  expect(await screen.findByRole('button', { name: 'Mail fictif' })).toBeDisabled();
  expect(api.getLocalEmailDraft).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'En cours de saisie' }));
  expect(screen.getByText('Éditeur mail temporaire')).toBeVisible();
  expect(useEmailStore.getState().draftBody).toBe('Ne pas perdre');
});
it('masque tous les titres en démonstration', async () => {
  useDemoStore.setState({ enabled: true }); render(<MemoryDraftsBranch />);
  await waitFor(() => expect(api.listMemoryDrafts).toHaveBeenCalled());
  expect(screen.queryByText('Mail fictif')).not.toBeInTheDocument();
});
