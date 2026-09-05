/**
 * B-459 : la fusion relisait TOUT le stockage local (`...brut`), sans version
 * ni migration. Une clé étrangère ou héritée (factures figées, `loading`
 * bloqué à true) rentrait dans le magasin sans contrôle.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { installLocalStorageStub } from '../test/localStorage-stub';
import { useInvoiceStore } from './invoiceStore';

const CLE = 'therese-invoice-storage';

describe('invoiceStore - stockage étranger (B-459)', () => {
  beforeEach(() => installLocalStorageStub());

  it('ne relit que les filtres, jamais les factures ni un état de chargement', async () => {
    localStorage.setItem(
      CLE,
      JSON.stringify({
        state: { filters: { status: 'paid' }, invoices: [{ id: 'zombie' }], loading: true, clefInconnue: 1 },
        version: 0,
      }),
    );
    await useInvoiceStore.persist.rehydrate();
    const etat = useInvoiceStore.getState() as unknown as Record<string, unknown>;
    expect(etat.invoices).toEqual([]);
    expect(etat).not.toHaveProperty('loading');
    expect(etat).not.toHaveProperty('clefInconnue');
    expect((etat.filters as { status?: string }).status).toBe('paid');
  });
});
