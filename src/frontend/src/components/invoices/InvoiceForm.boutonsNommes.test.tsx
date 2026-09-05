/**
 * B-578 (05/09/2026) : les boutons icône seule « fermer » et « supprimer la
 * ligne » du formulaire de facture n'avaient pas de nom accessible.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { InvoiceForm } from './InvoiceForm';
import { useBillingProfileStore } from '../../stores/billingProfileStore';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listContacts: vi.fn().mockResolvedValue([]), getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }) };
});

describe('InvoiceForm : boutons nommés (B-578)', () => {
  it('fermer et supprimer la ligne ont un nom', async () => {
    useBillingProfileStore.setState({ missing: null });
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);
    expect(await screen.findByRole('button', { name: 'Fermer' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Supprimer la ligne 1' })).toBeInTheDocument();
  });
});
