/** B-1165 : le montant confirmé suit la TVA arrondie sur la base de chaque taux. */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Contact } from '../../services/api';
import { InvoiceWorkspaceCanvas } from './InvoiceConversationCard';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';

const CONTACT: Contact = {
  id: 'contact-1', first_name: 'Marie', last_name: 'Lefevre', company: null,
  email: 'marie@example.test', phone: null, address: null, notes: null, tags: [],
  stage: 'client', score: 60, source: 'local', last_interaction: null,
  created_at: '2026-07-01', updated_at: '2026-07-12',
};

const DONNEES: InvoiceWorkspaceData = {
  invoices: [], contacts: [CONTACT],
  billingProfile: { is_complete: true, missing: [] }, unavailableSources: [],
};

function rendreFormulaire() {
  render(
    <InvoiceWorkspaceCanvas
      resource={{ status: 'ready', data: DONNEES, error: null }}
      invoiceResource={null}
      selection="new-devis"
      onRetry={vi.fn()}
      onRetryInvoice={vi.fn()}
      onCreateDraft={vi.fn()}
      onCreateContact={vi.fn()}
      onOpenClassic={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText('Client du devis'), { target: { value: CONTACT.id } });
}

function saisirLigne(index: number, prixHt: string) {
  if (index > 0) fireEvent.click(screen.getByRole('button', { name: 'Ajouter' }));
  fireEvent.change(screen.getByLabelText(`Description ligne ${index + 1}`), {
    target: { value: `Prestation ${index + 1}` },
  });
  fireEvent.change(screen.getByLabelText(`Prix HT ligne ${index + 1}`), {
    target: { value: prixHt },
  });
}

/** Le récapitulatif est le seul endroit qui rend ces montants tant qu'on n'a pas confirmé. */
function texteRendu(): string {
  return document.body.textContent ?? '';
}

describe('B-017 - le pavé annonce le montant que le serveur produira', () => {
  it('B-1165 : trois lignes de 33,33 € à 20 % confirment 119,99 €', () => {
    rendreFormulaire();
    for (let index = 0; index < 3; index += 1) saisirLigne(index, '33,33');
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));

    const pave = screen.getByTestId('devis-draft-confirmation');
    expect(pave.textContent).toContain('119,99');
    expect(pave.textContent).not.toContain('120,00');
  });

  it('le récapitulatif du formulaire dit la même chose que le pavé', () => {
    // La base de 99,99 € à 20 % donne 20,00 € de TVA par taux.
    rendreFormulaire();
    for (let index = 0; index < 3; index += 1) saisirLigne(index, '33,33');

    const texte = texteRendu();
    expect(texte).toContain('99,99');
    expect(texte).toContain('20,00');
    expect(texte).toContain('119,99');
    expect(texte).not.toContain('120,00');
  });

  it('témoin : un cas sans troisième décimale reste inchangé', () => {
    // Sans ce témoin, un arrondi trop large (à l'euro, par exemple) passerait
    // au vert sur le cas ci-dessus.
    rendreFormulaire();
    saisirLigne(0, '490');

    const texte = texteRendu();
    expect(texte).toContain('490,00');
    expect(texte).toContain('98,00');
    expect(texte).toContain('588,00');
  });
});
