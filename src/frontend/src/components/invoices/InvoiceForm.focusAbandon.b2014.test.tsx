import { act, fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { InvoiceForm } from './InvoiceForm';

vi.mock('../../services/api', async (original) => ({
  ...await original<typeof import('../../services/api')>(),
  listContacts: vi.fn().mockResolvedValue([]),
  getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
}));

it.each(['Tab', 'Maj+Tab'])('garde le focus dans la facture avec %s pendant la question d’abandon', async (touche) => {
  const fermer = vi.fn();
  await act(async () => { render(<InvoiceForm invoice={null} onClose={fermer} onSave={vi.fn()} />); });
  fireEvent.change(screen.getByLabelText('Description ligne 1'), { target: { value: 'Prestation fictive' } });
  fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

  const premier = screen.getByRole('button', { name: 'Fermer' });
  const dernier = screen.getByRole('button', { name: 'Abandonner' });
  const source = touche === 'Tab' ? dernier : premier;
  const cible = touche === 'Tab' ? premier : dernier;
  source.focus();
  fireEvent.keyDown(source, { key: 'Tab', shiftKey: touche === 'Maj+Tab' });

  expect(cible).toHaveFocus();
  expect(fermer).not.toHaveBeenCalled();
});
