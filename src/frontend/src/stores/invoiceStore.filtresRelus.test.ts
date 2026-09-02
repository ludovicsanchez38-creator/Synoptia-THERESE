/**
 * B-005 : des filtres relus du stockage sans fusion ni contrôle.
 *
 * `persist()` était déclaré sans `merge`. La fusion par défaut de zustand est
 * un étalement de PREMIER niveau : l'objet `filters` venu du stockage
 * REMPLACE le défaut en bloc. Trois conséquences, toutes visibles à l'écran :
 * un `filters` partiel perd `status: 'all'` ; une paire impossible
 * (« devis » + « payée », un statut de facture) est restaurée telle quelle et
 * la rangée de statuts n'affiche alors aucun bouton sélectionné au-dessus
 * d'une liste vide ; `filters: null` fait planter la liste dès qu'elle n'est
 * pas vide.
 *
 * La paire impossible n'exige aucun stockage abîmé : l'application la produit
 * elle-même (Factures > Payée > Devis). Le second verrou vit donc dans le
 * panneau, cf. InvoicesPanel.filtreType.test.tsx.
 */
import { beforeEach, describe, expect, it } from 'vitest';

import { installLocalStorageStub } from '../test/localStorage-stub';
import { useInvoiceStore } from './invoiceStore';

const CLE = 'therese-invoice-storage';

function semer(filters: unknown) {
  localStorage.setItem(CLE, JSON.stringify({ state: { filters } }));
}

function facture(id: string, status: string) {
  return { id, contact_id: 'contact-1', status, document_type: 'facture' } as never;
}

describe('B-005 : les filtres relus du stockage sont fusionnés et assainis', () => {
  beforeEach(() => {
    installLocalStorageStub();
    localStorage.clear();
    useInvoiceStore.setState({ invoices: [], filters: { status: 'all' } });
  });

  it("un filtre partiel garde le défaut « toutes »", async () => {
    semer({ document_type: 'devis' });

    await useInvoiceStore.persist.rehydrate();

    expect(useInvoiceStore.getState().filters.status).toBe('all');
    expect(useInvoiceStore.getState().filters.document_type).toBe('devis');
  });

  it("une paire type/statut impossible est ramenée à « toutes »", async () => {
    semer({ document_type: 'devis', status: 'paid' });

    await useInvoiceStore.persist.rehydrate();

    expect(useInvoiceStore.getState().filters.status).toBe('all');
  });

  it('un statut valide pour son type est conservé', async () => {
    semer({ document_type: 'devis', status: 'accepted' });

    await useInvoiceStore.persist.rehydrate();

    expect(useInvoiceStore.getState().filters.status).toBe('accepted');
  });

  it('des filtres nuls ne font pas tomber la liste', async () => {
    semer(null);

    await useInvoiceStore.persist.rehydrate();
    useInvoiceStore.getState().setInvoices([facture('a', 'draft'), facture('b', 'paid')]);

    expect(() => useInvoiceStore.getState().getFilteredInvoices()).not.toThrow();
    expect(useInvoiceStore.getState().getFilteredInvoices()).toHaveLength(2);
  });

  it('un statut inconnu du domaine est refusé', async () => {
    semer({ status: 'gribouille' });

    await useInvoiceStore.persist.rehydrate();

    expect(useInvoiceStore.getState().filters.status).toBe('all');
  });
});
