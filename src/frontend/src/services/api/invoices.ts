/**
 * THÉRÈSE v2 - Invoices API Module
 *
 * Facturation : factures, devis, avoirs et génération PDF.
 */

import { API_BASE, apiFetch } from './core';

export interface InvoiceLine {
  id: string;
  invoice_id: string;
  description: string;
  quantity: number;
  unit_price_ht: number;
  tva_rate: number;
  total_ht: number;
  total_ttc: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  contact_id: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  subtotal_ht: number;
  total_tax: number;
  total_ttc: number;
  notes: string | null;
  payment_date: string | null;
  created_at: string;
  updated_at: string;
  lines: InvoiceLine[];
}

export interface InvoiceLineRequest {
  description: string;
  quantity: number;
  unit_price_ht: number;
  tva_rate: number;
}

export interface CreateInvoiceRequest {
  contact_id: string;
  issue_date?: string;
  due_date?: string;
  lines: InvoiceLineRequest[];
  notes?: string;
}

export interface UpdateInvoiceRequest {
  contact_id?: string;
  issue_date?: string;
  due_date?: string;
  status?: string;
  lines?: InvoiceLineRequest[];
  notes?: string;
}

export async function listInvoices(params?: {
  status?: string;
  contact_id?: string;
}): Promise<Invoice[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set('status', params.status);
  if (params?.contact_id) queryParams.set('contact_id', params.contact_id);

  const response = await apiFetch(`${API_BASE}/api/invoices?${queryParams}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function getInvoice(invoiceId: string): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function createInvoice(req: CreateInvoiceRequest): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function updateInvoice(invoiceId: string, req: UpdateInvoiceRequest): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteInvoice(invoiceId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}`, {
    method: 'DELETE',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function markInvoicePaid(invoiceId: string, paymentDate?: string): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}/mark-paid`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_date: paymentDate }),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function generateInvoicePDF(invoiceId: string): Promise<{ pdf_path: string; invoice_number: string }> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}/pdf`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function sendInvoiceByEmail(invoiceId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}/send`, {
    method: 'POST',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}
