/**
 * B-017 - le montant confirmé est celui que le document portera.
 *
 * Constat du 02/09/2026 (reproduction RP10, Playwright, sans appel au
 * modèle) : trois lignes de 33,33 € à 20 % faisaient annoncer « Montant TTC :
 * 119,99 € » au pavé de confirmation, puis le devis créé par le serveur
 * portait 120,00 € et la liste affichait « DEV-2026-001 … 120,00 € ». Un
 * centime de plus que ce qui avait été confirmé.
 *
 * Le serveur arrondit AU CENTIME LIGNE PAR LIGNE
 * (`routers/invoices.py::_montants_de_ligne`, dont le commentaire raconte
 * exactement ce cas : « 119.98799999999999 en base pendant que le PDF
 * imprimait 119,99 »), puis somme des lignes déjà arrondies. Le formulaire,
 * lui, sommait des montants NON arrondis et n'arrondissait qu'à l'affichage.
 *
 * `formatMoney` insère une espace fine insécable avant le symbole : on
 * cherche le nombre, jamais la chaîne complète.
 */
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
  it('trois lignes de 33,33 € à 20 % confirment 120,00 €, pas 119,99 €', () => {
    rendreFormulaire();
    for (let index = 0; index < 3; index += 1) saisirLigne(index, '33,33');
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));

    const pave = screen.getByTestId('devis-draft-confirmation');
    expect(pave.textContent).toContain('120,00');
    expect(pave.textContent).not.toContain('119,99');
  });

  it('le récapitulatif du formulaire dit la même chose que le pavé', () => {
    // Les deux chiffres viennent du même calcul : le récapitulatif annonçait
    // « TTC 119,99 € » sous les yeux de l'utilisateur avant même la
    // confirmation. La TVA suit la même règle : 20,01 € et non 20,00 €.
    rendreFormulaire();
    for (let index = 0; index < 3; index += 1) saisirLigne(index, '33,33');

    const texte = texteRendu();
    expect(texte).toContain('99,99');
    expect(texte).toContain('20,01');
    expect(texte).toContain('120,00');
    expect(texte).not.toContain('119,99');
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
