/**
 * Cycle 6, lecteur D203 (InvoiceConversationCard.tsx) : les échecs
 * d'écriture remplaçaient le message du serveur par un générique, à l'inverse
 * d'InvoicesPanel (B-218, B-207) qui affiche la cause renvoyée par l'API.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';
import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const contact: Contact = {
  id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Atelier Martin', email: 'camille@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 80, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
};
const donnees: InvoiceWorkspaceData = {
  invoices: [], contacts: [contact], billingProfile: { is_complete: true, missing: [] }, unavailableSources: [], contactsTronques: false,
};

describe('D203 : la cause du serveur arrive à l’écran du canevas Facturer', () => {
  it('un brouillon refusé affiche le message renvoyé par l’API', async () => {
    const onCreateDraft = vi.fn().mockRejectedValue(new Error('Profil émetteur incomplet : SIRET manquant'));
    render(
      <InvoiceWorkspaceCanvas
        resource={{ status: 'ready', data: donnees, error: null }} invoiceResource={null} selection="new-devis"
        onRetry={vi.fn()} onRetryInvoice={vi.fn()} onCreateDraft={onCreateDraft} onCreateContact={vi.fn()} onOpenClassic={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText('Client du devis'), { target: { value: contact.id } });
    fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Diagnostic IA' } });
    fireEvent.change(screen.getByLabelText('Prix HT ligne 1'), { target: { value: '490' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    expect(await screen.findByText(/SIRET manquant/)).toBeInTheDocument();
  });
});
