import { useCallback, useEffect, useRef, useState } from 'react';
import {
  createInvoice,
  getBillingProfileStatus,
  getInvoice,
  listContacts,
  listInvoices,
  type Contact,
  type CreateInvoiceRequest,
  type Invoice,
} from '../../services/api';
import { useInvoiceStore } from '../../stores/invoiceStore';
import type { ReadResource } from './usePrototypeReadData';

export interface InvoiceWorkspaceData {
  invoices: Invoice[];
  contacts: Contact[];
  billingProfile: { is_complete: boolean; missing: string[] } | null;
  unavailableSources: string[];
}

export function usePrototypeInvoiceData(enabled = true) {
  const [resource, setResource] = useState<ReadResource<InvoiceWorkspaceData>>({
    status: 'loading', data: null, error: null,
  });
  const [invoiceResource, setInvoiceResource] = useState<ReadResource<Invoice> | null>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
  const requestId = useRef(0);
  const detailRequestId = useRef(0);

  const refresh = useCallback(async () => {
    const activeRequest = ++requestId.current;
    setResource({ status: 'loading', data: null, error: null });

    try {
      const invoices = await listInvoices();
      if (activeRequest !== requestId.current) return;
      useInvoiceStore.getState().setInvoices(invoices);

      const [contactsResult, profileResult] = await Promise.allSettled([
        listContacts(0, 100),
        getBillingProfileStatus(),
      ]);
      if (activeRequest !== requestId.current) return;

      const unavailableSources: string[] = [];
      const contacts = contactsResult.status === 'fulfilled' ? contactsResult.value : [];
      const billingProfile = profileResult.status === 'fulfilled' ? profileResult.value : null;
      if (contactsResult.status === 'rejected') unavailableSources.push('contacts');
      if (profileResult.status === 'rejected') unavailableSources.push('profil émetteur');

      setResource({
        status: 'ready',
        data: { invoices, contacts, billingProfile, unavailableSources },
        error: null,
      });
    } catch {
      if (activeRequest !== requestId.current) return;
      setResource({
        status: 'error', data: null,
        error: 'Impossible de charger les devis et factures pour le moment.',
      });
    }
  }, []);

  const createDevisDraft = useCallback(async (request: CreateInvoiceRequest) => {
    const created = await createInvoice({ ...request, document_type: 'devis' });
    useInvoiceStore.getState().addInvoice(created);
    setResource((current) => current.status === 'ready'
      ? {
          ...current,
          data: { ...current.data, invoices: [created, ...current.data.invoices] },
        }
      : current);
    return created;
  }, []);

  const openInvoice = useCallback(async (invoiceId: string) => {
    setSelectedInvoiceId(invoiceId);
    const activeRequest = ++detailRequestId.current;
    setInvoiceResource({ status: 'loading', data: null, error: null });
    try {
      const invoice = await getInvoice(invoiceId);
      if (activeRequest !== detailRequestId.current) return;
      useInvoiceStore.getState().updateInvoiceInStore(invoice);
      setResource((current) => current.status === 'ready'
        ? {
            ...current,
            data: {
              ...current.data,
              invoices: current.data.invoices.map((item) => item.id === invoice.id ? invoice : item),
            },
          }
        : current);
      setInvoiceResource({ status: 'ready', data: invoice, error: null });
    } catch {
      if (activeRequest !== detailRequestId.current) return;
      setInvoiceResource({
        status: 'error', data: null,
        error: 'Impossible de charger le détail de ce document.',
      });
    }
  }, []);

  const retryInvoice = useCallback(async () => {
    if (selectedInvoiceId) await openInvoice(selectedInvoiceId);
  }, [openInvoice, selectedInvoiceId]);

  useEffect(() => {
    if (!enabled) return undefined;
    void refresh();
    return () => {
      requestId.current += 1;
      detailRequestId.current += 1;
    };
  }, [enabled, refresh]);

  return {
    resource,
    invoiceResource,
    refresh,
    openInvoice,
    retryInvoice,
    createDevisDraft,
  };
}
