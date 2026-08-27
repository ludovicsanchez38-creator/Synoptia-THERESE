/**
 * Entrée 2 du plan du 28/08 : le devis redemandait un client déjà à l'écran.
 *
 * `selectedContactId` SURVIT au passage de « Retrouver » à « Facturer » — la
 * relecture l'a vérifié, et c'est ce qui rend l'entrée petite : la valeur est
 * en mémoire, elle n'est simplement pas tendue au formulaire, qui naît sur un
 * `useState('')`.
 *
 * Condition non négociable : la valeur reste modifiable, et sa provenance se
 * voit. Un préremplissage silencieux qui verrouille serait pire que le champ
 * vide.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';

const DONNEES = {
  contacts: [
    { id: 'c-alpha', display_name: 'Client Alpha', first_name: 'Alpha', last_name: '', company: 'Alpha SA' },
    { id: 'c-beta', display_name: 'Client Beta', first_name: 'Beta', last_name: '', company: 'Beta SARL' },
  ],
  invoices: [],
  totals: { draft: 0, sent: 0, paid: 0 },
};

function rendre(contactInitial?: string) {
  return render(
    <InvoiceWorkspaceCanvas
      resource={{ status: 'ready', error: null, data: DONNEES as never }}
      invoiceResource={{ status: 'loading', error: null, data: null }}
      selection={'new-devis'}
      contactInitial={contactInitial}
      onRetry={vi.fn()}
      onRetryInvoice={vi.fn()}
      onCreateDraft={vi.fn()}
      onCreateContact={vi.fn()}
      onOpenClassic={vi.fn()}
    />,
  );
}

describe('Entrée 2 : le devis hérite du client déjà à l’écran', () => {
  it('reprend le contact que la coque a en mémoire', () => {
    rendre('c-beta');

    const champ = screen.getByLabelText('Client du devis') as HTMLSelectElement;
    expect(champ.value).toBe('c-beta');
  });

  it('laisse changer d’avis : la valeur héritée n’est pas un verrou', () => {
    rendre('c-beta');

    const champ = screen.getByLabelText('Client du devis') as HTMLSelectElement;
    fireEvent.change(champ, { target: { value: 'c-alpha' } });

    expect(champ.value).toBe('c-alpha');
    expect(champ).not.toBeDisabled();
  });

  it('sans contact en mémoire, le champ reste vide comme avant', () => {
    rendre(undefined);

    expect((screen.getByLabelText('Client du devis') as HTMLSelectElement).value).toBe('');
  });
});
