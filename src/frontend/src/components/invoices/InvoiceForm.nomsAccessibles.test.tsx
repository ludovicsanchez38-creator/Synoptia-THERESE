/**
 * B-234 : trois champs, un seul nom.
 *
 * Dans la modale « Nouvelle facture », les champs de description des lignes
 * portaient tous le nom accessible littéral « Description de la ligne », sans
 * numéro, alors que leurs voisins de la MÊME itération sont « Quantité ligne
 * 1/2/3 » et « Prix HT ligne 1/2/3 ». À la voix, trois champs identiques :
 * rien ne dit lequel on remplit.
 *
 * La forme attendue n'est pas inventée ici : `InvoiceConversationCard.tsx:553`
 * écrit déjà `Description ligne ${index + 1}` sur exactement le même champ.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useBillingProfileStore } from '../../stores/billingProfileStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listContacts: vi.fn().mockResolvedValue([
      { id: 'contact-1', first_name: 'Camille', last_name: 'Martin', email: 'camille@example.fr' },
    ]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import { InvoiceForm } from './InvoiceForm';

describe('B-234 : chaque ligne de facture a un nom accessible unique par champ', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBillingProfileStore.setState({ missing: null });
  });

  it('les trois descriptions sont numérotées comme la quantité et le prix', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    const ajouter = await screen.findByRole('button', { name: /Ajouter une ligne/i });
    fireEvent.click(ajouter);
    fireEvent.click(ajouter);

    // Les voisins portent déjà le numéro : la description doit suivre la même
    // convention, sur la même itération.
    for (const rang of [1, 2, 3]) {
      expect(screen.getByLabelText(`Quantité ligne ${rang}`)).toBeInTheDocument();
      expect(screen.getByLabelText(`Prix HT ligne ${rang}`)).toBeInTheDocument();
      expect(screen.getByLabelText(`Description ligne ${rang}`)).toBeInTheDocument();
    }

    // Et aucun doublon : `getByLabelText` ci-dessus jetterait déjà sur deux
    // champs de même nom, mais l'assertion explicite dit ce qui est en jeu.
    const noms = screen
      .getAllByLabelText(/^Description ligne/)
      .map((champ) => champ.getAttribute('aria-label'));
    expect(noms).toEqual(['Description ligne 1', 'Description ligne 2', 'Description ligne 3']);
    expect(new Set(noms).size).toBe(3);
  });

  it('le nom constant « Description de la ligne » a disparu', async () => {
    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    fireEvent.click(await screen.findByRole('button', { name: /Ajouter une ligne/i }));

    expect(screen.queryAllByLabelText('Description de la ligne')).toHaveLength(0);
  });
});
