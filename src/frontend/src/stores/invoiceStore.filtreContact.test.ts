/**
 * B-004 : un filtre client invisible et irréversible sur la facturation.
 *
 * `filters.contact_id` était persisté dans le stockage et renvoyé à chaque
 * `GET /api/invoices`. Or il n'apparaît nulle part dans le panneau, et AUCUN
 * contrôle ne le vide : les deux seuls appelants de `setFilters` recopient
 * `...filters`. Un état hérité (version antérieure, stockage bricolé, futur
 * bouton « factures de ce client ») restreignait donc la liste des devis et
 * factures pour toujours, en travers du rechargement et des deux boutons de
 * réinitialisation les plus larges, pendant que l'en-tête annonçait un nombre
 * de documents sans dire qu'un filtre le bornait.
 *
 * Le filtre reste utilisable le temps d'une session ; il ne SURVIT plus.
 */
import { beforeEach, describe, expect, it } from 'vitest';

import { installLocalStorageStub } from '../test/localStorage-stub';
import { useInvoiceStore } from './invoiceStore';

const CLE = 'therese-invoice-storage';

function stockage() {
  const brut = localStorage.getItem(CLE);
  return brut ? JSON.parse(brut) : null;
}

function facture(id: string, contactId: string) {
  return { id, contact_id: contactId, status: 'draft', document_type: 'facture' } as never;
}

describe('B-004 : le filtre client ne se fige pas dans le stockage', () => {
  beforeEach(() => {
    installLocalStorageStub();
    localStorage.clear();
    useInvoiceStore.setState({ invoices: [], filters: { status: 'all' } });
  });

  it("n'écrit pas le client filtré dans le stockage", () => {
    useInvoiceStore.getState().setFilters({ status: 'all', contact_id: 'contact-1' });

    expect(useInvoiceStore.getState().filters.contact_id).toBe('contact-1');
    expect(stockage()?.state?.filters?.contact_id).toBeUndefined();
  });

  it('ne relit pas un client filtré hérité du stockage', async () => {
    localStorage.setItem(
      CLE,
      JSON.stringify({ state: { filters: { status: 'all', contact_id: 'contact-1' } } }),
    );

    await useInvoiceStore.persist.rehydrate();

    expect(useInvoiceStore.getState().filters.contact_id).toBeUndefined();
  });

  it('la liste relue du stockage ne reste pas bornée à un client', async () => {
    localStorage.setItem(
      CLE,
      JSON.stringify({ state: { filters: { status: 'all', contact_id: 'contact-1' } } }),
    );

    await useInvoiceStore.persist.rehydrate();
    useInvoiceStore.getState().setInvoices([
      facture('a', 'contact-1'),
      facture('b', 'contact-2'),
    ]);

    expect(useInvoiceStore.getState().getFilteredInvoices().map((f) => f.id)).toEqual(['a', 'b']);
  });
});
