import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { InvoiceForm } from './InvoiceForm';

const { createInvoiceMock } = vi.hoisted(() => ({
  createInvoiceMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');

  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([
      {
        id: 'contact-1',
        first_name: 'Jean',
        last_name: 'Dupont',
        email: 'jean@example.com',
      },
    ]),
    createInvoice: createInvoiceMock,
    updateInvoice: vi.fn(),
    markInvoicePaid: vi.fn(),
  };
});

describe('InvoiceForm décimaux', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    createInvoiceMock.mockResolvedValue({ id: 'inv-1' });
  });

  it('accepte le point du pavé numérique dans le prix HT', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    const priceInput = await screen.findByLabelText('Prix HT ligne 1');
    fireEvent.change(priceInput, { target: { value: '12' } });
    fireEvent.change(priceInput, { target: { value: '12.' } });
    fireEvent.change(priceInput, { target: { value: '12.5' } });

    expect(priceInput).toHaveValue('12.5');
    expect(screen.getAllByText(/12.50 €/i)).toHaveLength(2);
  });

  it('accepte aussi la virgule dans le prix HT', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    const priceInput = await screen.findByLabelText('Prix HT ligne 1');
    fireEvent.change(priceInput, { target: { value: '12' } });
    fireEvent.change(priceInput, { target: { value: '12,' } });
    fireEvent.change(priceInput, { target: { value: '12,5' } });

    expect(priceInput).toHaveValue('12,5');
    expect(screen.getAllByText(/12.50 €/i)).toHaveLength(2);
  });

  it('bloque les valeurs vides ou invalides à la soumission', async () => {
    window.alert = vi.fn();
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    fireEvent.change(await screen.findByLabelText(/Client/i), { target: { value: 'contact-1' } });
    fireEvent.change(screen.getByPlaceholderText('Description'), { target: { value: 'Prestation' } });
    fireEvent.change(screen.getByLabelText('Quantité ligne 1'), { target: { value: '' } });

    fireEvent.click(screen.getByRole('button', { name: /Cre/i }));

    expect(createInvoiceMock).not.toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalled();
  });
});
