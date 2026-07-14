import { useMemo, useRef, useState, type ReactNode } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  FilePlus2,
  FileText,
  Loader2,
  Plus,
  Receipt,
  RefreshCw,
  ShieldCheck,
  Trash2,
  Users,
} from 'lucide-react';
import type { Contact, CreateInvoiceRequest, Invoice } from '../../services/api';
import type { InvoiceWorkspaceData } from './usePrototypeInvoiceData';
import type { ReadResource } from './usePrototypeReadData';

type InvoiceSelection = string | 'new-devis' | null;

interface DraftLine {
  description: string;
  quantity: string;
  unitPrice: string;
  tvaRate: number;
}

const statusLabels: Record<string, string> = {
  draft: 'Brouillon', sent: 'Envoyé', paid: 'Payé', overdue: 'En retard',
  cancelled: 'Annulé', converted: 'Converti', accepted: 'Accepté',
  refused: 'Refusé', expired: 'Expiré',
};

function StateShell({ children }: { children: ReactNode }) {
  return <div className="flex min-h-48 items-center justify-center px-5 py-8">{children}</div>;
}

function contactLabel(contact: Contact | undefined): string {
  if (!contact) return 'Contact introuvable';
  return [contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.company || contact.email || 'Contact sans nom';
}

function formatMoney(value: number, currency: string): string {
  try {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currency}`;
  }
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date inconnue' : date.toLocaleDateString('fr-FR');
}

function todayIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function dueDateIso(): string {
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + 30);
  const offset = dueDate.getTimezoneOffset() * 60_000;
  return new Date(dueDate.getTime() - offset).toISOString().slice(0, 10);
}

function parseDecimal(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value.replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : null;
}

function sortedInvoices(invoices: Invoice[]): Invoice[] {
  return [...invoices].sort((left, right) => (right.updated_at || '').localeCompare(left.updated_at || ''));
}

export function InvoiceWorkspaceCard({
  resource,
  onRetry,
  onOpenInvoice,
  onCreateDevis,
  onOpenClassic,
}: {
  resource: ReadResource<InvoiceWorkspaceData>;
  onRetry: () => void;
  onOpenInvoice: (invoiceId: string) => void;
  onCreateDevis: () => void;
  onOpenClassic: () => void;
}) {
  const invoices = resource.status === 'ready' ? sortedInvoices(resource.data.invoices).slice(0, 6) : [];

  return (
    <section
      aria-labelledby="invoice-workspace-title"
      className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]"
      data-testid="invoice-workspace-card"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[9px] border border-text bg-[var(--color-warning-tint)] text-warning">
            <Receipt className="h-4 w-4" />
          </span>
          <div>
            <h2 id="invoice-workspace-title" className="text-sm font-semibold text-text">Devis et factures</h2>
            <p className="text-[11px] text-text-muted">
              {resource.status === 'ready' ? `${resource.data.invoices.length} document${resource.data.invoices.length > 1 ? 's' : ''} enregistré${resource.data.invoices.length > 1 ? 's' : ''}` : 'Lecture de la facturation locale'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onCreateDevis} className="inline-flex items-center gap-1.5 rounded-[8px] bg-text px-2.5 py-1.5 text-[11px] font-semibold text-white">
            <Plus className="h-3.5 w-3.5" />
            Nouveau devis
          </button>
          <button type="button" onClick={onOpenClassic} className="rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text hover:bg-surface-2">
            Facturation complète
          </button>
        </div>
      </div>

      {resource.status === 'loading' ? (
        <StateShell>
          <div className="flex items-center gap-2 text-sm text-text-muted" role="status">
            <Loader2 className="h-4 w-4 animate-spin text-warning" />
            Je consulte les documents…
          </div>
        </StateShell>
      ) : resource.status === 'error' ? (
        <StateShell>
          <div className="max-w-sm text-center" data-testid="invoice-workspace-error">
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">Facturation indisponible</p>
            <p className="mt-1 text-xs leading-5 text-text-muted">{resource.error}</p>
            <div className="mt-4 flex justify-center gap-2">
              <button type="button" onClick={onRetry} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">
                <RefreshCw className="h-3.5 w-3.5" />
                Réessayer
              </button>
              <button type="button" onClick={onOpenClassic} className="rounded-[9px] border border-border px-3 py-2 text-xs font-semibold text-text">Ouvrir Facturation</button>
            </div>
          </div>
        </StateShell>
      ) : invoices.length === 0 ? (
        <StateShell>
          <div className="text-center" data-testid="invoice-workspace-empty">
            <FileText className="mx-auto h-6 w-6 text-text-muted" />
            <p className="mt-2 text-sm font-semibold text-text">Aucun devis ni facture</p>
            <p className="mt-1 text-xs text-text-muted">Tu peux préparer un premier devis sans l’envoyer.</p>
            <button type="button" onClick={onCreateDevis} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Préparer un devis</button>
          </div>
        </StateShell>
      ) : (
        <div className="divide-y divide-[#EDF1F7]">
          {invoices.map((invoice) => {
            const contact = resource.data.contacts.find((item) => item.id === invoice.contact_id);
            return (
              <button key={invoice.id} type="button" onClick={() => onOpenInvoice(invoice.id)} className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-surface-2">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[9px] bg-[var(--color-warning-tint)] text-warning">
                  <FileText className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <strong className="text-sm text-text">{invoice.invoice_number}</strong>
                    <span className="rounded-full bg-bg px-2 py-0.5 text-[10px] font-semibold text-text-muted">{statusLabels[invoice.status] || invoice.status}</span>
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-text-muted">{contactLabel(contact)} · {invoice.document_type}</span>
                </span>
                <span className="shrink-0 text-sm font-bold text-text">{formatMoney(invoice.total_ttc, invoice.currency)}</span>
                <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />
              </button>
            );
          })}
        </div>
      )}

      {resource.status === 'ready' && resource.data.unavailableSources.length > 0 && (
        <div className="border-t border-border bg-[var(--color-warning-tint)] px-4 py-2 text-[10px] text-warning">
          Source{resource.data.unavailableSources.length > 1 ? 's' : ''} indisponible{resource.data.unavailableSources.length > 1 ? 's' : ''} : {resource.data.unavailableSources.join(', ')}.
        </div>
      )}
    </section>
  );
}

function ExistingInvoiceDetail({ data, invoice }: { data: InvoiceWorkspaceData; invoice: Invoice }) {
  const contact = data.contacts.find((item) => item.id === invoice.contact_id);
  return (
    <div className="space-y-4" data-testid="invoice-detail">
      <section className="rounded-[13px] border border-border bg-surface p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">{invoice.document_type}</div>
            <h3 className="mt-1 text-lg font-bold text-text">{invoice.invoice_number}</h3>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-text-muted"><Users className="h-3.5 w-3.5" />{contactLabel(contact)}</p>
          </div>
          <div className="text-right">
            <span className="rounded-full bg-bg px-2.5 py-1 text-[10px] font-semibold text-text-muted">{statusLabels[invoice.status] || invoice.status}</span>
            <div className="mt-2 text-xl font-bold text-text">{formatMoney(invoice.total_ttc, invoice.currency)}</div>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-[9px] bg-surface-2 p-2.5"><span className="block text-[10px] text-text-muted">Émission</span><strong>{formatDate(invoice.issue_date)}</strong></div>
          <div className="rounded-[9px] bg-surface-2 p-2.5"><span className="block text-[10px] text-text-muted">Échéance</span><strong>{formatDate(invoice.due_date)}</strong></div>
        </div>
      </section>

      <section className="overflow-hidden rounded-[13px] border border-border bg-surface">
        <div className="border-b border-border px-4 py-3 text-sm font-bold text-text">Lignes</div>
        <div className="divide-y divide-[#EDF1F7]">
          {invoice.lines.map((line) => (
            <div key={line.id} className="grid grid-cols-[1fr_auto] gap-3 px-4 py-3 text-xs">
              <div><strong className="text-text">{line.description}</strong><p className="mt-0.5 text-text-muted">{line.quantity} × {formatMoney(line.unit_price_ht, invoice.currency)} · TVA {line.tva_rate}%</p></div>
              <strong className="text-text">{formatMoney(line.total_ttc, invoice.currency)}</strong>
            </div>
          ))}
        </div>
        <div className="border-t border-border bg-surface-2 px-4 py-3 text-right text-xs text-text-muted">
          Total HT {formatMoney(invoice.subtotal_ht, invoice.currency)} · TVA {formatMoney(invoice.total_tax, invoice.currency)}
        </div>
      </section>

      {data.billingProfile && !data.billingProfile.is_complete && (
        <div className="flex items-start gap-2 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Profil émetteur incomplet : {data.billingProfile.missing.join(', ')}. La génération PDF doit rester bloquée.
        </div>
      )}
      {!data.billingProfile && (
        <div className="flex items-start gap-2 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Le profil émetteur n’a pas pu être vérifié. Aucune génération PDF n’est proposée dans ce canevas.
        </div>
      )}
      <div className="flex items-start gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3 text-xs text-accent">
        <ShieldCheck className="h-4 w-4 shrink-0" />
        Lecture seule dans ce canevas. L’envoi de facture n’est pas disponible et aucune action n’a été exécutée.
      </div>
    </div>
  );
}

function DevisDraftForm({
  data,
  onCreateDraft,
}: {
  data: InvoiceWorkspaceData;
  onCreateDraft: (request: CreateInvoiceRequest) => Promise<Invoice>;
}) {
  const [contactId, setContactId] = useState('');
  const [currency, setCurrency] = useState('EUR');
  const [issueDate, setIssueDate] = useState(todayIso);
  const [dueDate, setDueDate] = useState(dueDateIso);
  const [validity, setValidity] = useState('30');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<DraftLine[]>([
    { description: '', quantity: '1', unitPrice: '0', tvaRate: 20 },
  ]);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Invoice | null>(null);

  const totals = useMemo(() => lines.reduce((result, line) => {
    const quantity = parseDecimal(line.quantity) || 0;
    const unitPrice = parseDecimal(line.unitPrice) || 0;
    const subtotal = quantity * unitPrice;
    return {
      ht: result.ht + subtotal,
      tax: result.tax + subtotal * line.tvaRate / 100,
    };
  }, { ht: 0, tax: 0 }), [lines]);

  function updateLine(index: number, updates: Partial<DraftLine>) {
    setLines((current) => current.map((line, lineIndex) => lineIndex === index ? { ...line, ...updates } : line));
    setCreated(null);
  }

  function validate(): string | null {
    if (!contactId) return 'Sélectionne un contact.';
    if (lines.length === 0) return 'Ajoute au moins une ligne.';
    if (lines.some((line) => !line.description.trim())) return 'Chaque ligne doit avoir une description.';
    if (lines.some((line) => (parseDecimal(line.quantity) || 0) < 1)) return 'Chaque quantité doit être supérieure ou égale à 1.';
    if (lines.some((line) => parseDecimal(line.unitPrice) === null || (parseDecimal(line.unitPrice) || 0) < 0)) return 'Chaque prix HT doit être un nombre positif ou nul.';
    if (!issueDate || !dueDate) return 'Les dates sont obligatoires.';
    if (dueDate < issueDate) return 'L’échéance ne peut pas précéder la date d’émission.';
    const validityDays = Number.parseInt(validity, 10);
    if (!Number.isFinite(validityDays) || validityDays < 1) return 'La durée de validité doit être positive.';
    return null;
  }

  function requestConfirmation() {
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setConfirmationOpen(true);
  }

  async function confirmCreation() {
    if (savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    setError(null);
    try {
      const invoice = await onCreateDraft({
        contact_id: contactId,
        document_type: 'devis',
        currency,
        issue_date: issueDate,
        due_date: dueDate,
        validite_jours: Number.parseInt(validity, 10),
        notes: notes.trim() || undefined,
        lines: lines.map((line) => ({
          description: line.description.trim(),
          quantity: parseDecimal(line.quantity) || 0,
          unit_price_ht: parseDecimal(line.unitPrice) || 0,
          tva_rate: line.tvaRate,
        })),
      });
      setCreated(invoice);
      setConfirmationOpen(false);
    } catch {
      setError('Impossible d’enregistrer le devis brouillon.');
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }

  if (data.contacts.length === 0) {
    const contactsUnavailable = data.unavailableSources.includes('contacts');
    return (
      <StateShell>
        <div className="text-center" data-testid="invoice-no-contact">
          <Users className="mx-auto h-6 w-6 text-text-muted" />
          <p className="mt-2 text-sm font-semibold text-text">{contactsUnavailable ? 'Contacts indisponibles' : 'Aucun contact disponible'}</p>
          <p className="mt-1 text-xs text-text-muted">{contactsUnavailable ? 'Le référentiel de contacts n’a pas pu être chargé.' : 'Un devis doit être rattaché à un contact réel.'}</p>
        </div>
      </StateShell>
    );
  }

  return (
    <div className="space-y-4" data-testid="devis-draft-form">
      {data.billingProfile && !data.billingProfile.is_complete && (
        <div className="flex items-start gap-2 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Profil émetteur incomplet : {data.billingProfile.missing.join(', ')}. Tu peux enregistrer le brouillon, mais pas générer un PDF conforme.
        </div>
      )}
      {!data.billingProfile && (
        <div className="flex items-start gap-2 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-xs text-warning">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Le profil émetteur n’a pas pu être vérifié. Le brouillon reste possible, mais aucune génération PDF n’est proposée.
        </div>
      )}

      <section className="rounded-[13px] border border-border bg-surface p-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-xs text-text-muted sm:col-span-2">Client
            <select aria-label="Client du devis" value={contactId} onChange={(event) => setContactId(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border bg-surface px-2.5 py-2 text-xs text-text">
              <option value="">Sélectionner un contact</option>
              {data.contacts.map((contact) => <option key={contact.id} value={contact.id}>{contactLabel(contact)}</option>)}
            </select>
          </label>
          <label className="text-xs text-text-muted">Date d’émission
            <input aria-label="Date d’émission" type="date" value={issueDate} onChange={(event) => setIssueDate(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border px-2.5 py-2 text-xs text-text" />
          </label>
          <label className="text-xs text-text-muted">Échéance
            <input aria-label="Échéance du devis" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border px-2.5 py-2 text-xs text-text" />
          </label>
          <label className="text-xs text-text-muted">Devise
            <select aria-label="Devise du devis" value={currency} onChange={(event) => setCurrency(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border bg-surface px-2.5 py-2 text-xs text-text">
              {['EUR', 'CHF', 'USD', 'GBP', 'CAD'].map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label className="text-xs text-text-muted">Validité en jours
            <input aria-label="Validité du devis" inputMode="numeric" value={validity} onChange={(event) => setValidity(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border px-2.5 py-2 text-xs text-text" />
          </label>
        </div>
      </section>

      <section className="rounded-[13px] border border-border bg-surface p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-text">Lignes du devis</h3>
          <button type="button" onClick={() => setLines((current) => [...current, { description: '', quantity: '1', unitPrice: '0', tvaRate: 20 }])} className="inline-flex items-center gap-1 rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text"><Plus className="h-3.5 w-3.5" />Ajouter</button>
        </div>
        <div className="mt-3 space-y-3">
          {lines.map((line, index) => (
            <div key={index} className="grid gap-2 rounded-[10px] bg-surface-2 p-3 sm:grid-cols-[1fr_70px_100px_86px_32px]">
              <input aria-label={`Description ligne ${index + 1}`} placeholder="Description" value={line.description} onChange={(event) => updateLine(index, { description: event.target.value })} className="rounded-[8px] border border-border px-2.5 py-2 text-xs" />
              <input aria-label={`Quantité ligne ${index + 1}`} inputMode="decimal" value={line.quantity} onChange={(event) => updateLine(index, { quantity: event.target.value })} className="rounded-[8px] border border-border px-2.5 py-2 text-xs" />
              <input aria-label={`Prix HT ligne ${index + 1}`} inputMode="decimal" value={line.unitPrice} onChange={(event) => updateLine(index, { unitPrice: event.target.value })} className="rounded-[8px] border border-border px-2.5 py-2 text-xs" />
              <select aria-label={`TVA ligne ${index + 1}`} value={line.tvaRate} onChange={(event) => updateLine(index, { tvaRate: Number(event.target.value) })} className="rounded-[8px] border border-border bg-surface px-2 py-2 text-xs">
                {[20, 10, 5.5, 2.1, 0].map((rate) => <option key={rate} value={rate}>{rate}%</option>)}
              </select>
              <button type="button" aria-label={`Supprimer la ligne ${index + 1}`} onClick={() => setLines((current) => current.filter((_, lineIndex) => lineIndex !== index))} className="grid h-8 w-8 place-items-center rounded-[8px] text-error hover:bg-surface"><Trash2 className="h-3.5 w-3.5" /></button>
            </div>
          ))}
        </div>
        <label className="mt-3 block text-xs text-text-muted">Notes
          <textarea aria-label="Notes du devis" value={notes} onChange={(event) => setNotes(event.target.value)} className="mt-1.5 h-20 w-full resize-y rounded-[8px] border border-border p-2.5 text-xs text-text" />
        </label>
        <div className="mt-3 rounded-[10px] bg-bg p-3 text-right text-xs text-text-muted">
          HT {formatMoney(totals.ht, currency)} · TVA {formatMoney(totals.tax, currency)}
          <strong className="ml-3 text-sm text-text">TTC {formatMoney(totals.ht + totals.tax, currency)}</strong>
        </div>

        {error && <p className="mt-3 text-xs font-semibold text-error" role="alert">{error}</p>}
        {created && (
          <div className="mt-3 flex items-start gap-2 rounded-[10px] border border-success/40 bg-[var(--color-success-tint)] p-3 text-xs text-success" data-testid="devis-draft-saved">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span><strong>{created.invoice_number} enregistré comme brouillon.</strong> Aucun PDF n’a été généré et aucun email n’a été envoyé.</span>
          </div>
        )}

        {confirmationOpen && (
          <div className="mt-3 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3" data-testid="devis-draft-confirmation">
            <div className="flex items-start gap-2 text-xs text-accent">
              <ShieldCheck className="h-4 w-4 shrink-0" />
              <div>
                <strong>Confirmer la création du devis brouillon</strong>
                <p className="mt-1">Client : {contactLabel(data.contacts.find((contact) => contact.id === contactId))}</p>
                <p>Montant TTC : {formatMoney(totals.ht + totals.tax, currency)}</p>
                <p className="mt-1 font-semibold">Cette action crée un document local. Elle ne génère aucun PDF et n’envoie rien.</p>
              </div>
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <button type="button" onClick={() => setConfirmationOpen(false)} className="rounded-[8px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Annuler</button>
              <button type="button" disabled={saving} onClick={() => void confirmCreation()} className="rounded-[8px] bg-[#047857] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60">{saving ? 'Création…' : 'Confirmer le brouillon'}</button>
            </div>
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button type="button" onClick={requestConfirmation} disabled={saving} className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"><FilePlus2 className="h-3.5 w-3.5" />Enregistrer le brouillon</button>
        </div>
      </section>
    </div>
  );
}

export function InvoiceWorkspaceCanvas({
  resource,
  invoiceResource,
  selection,
  onRetry,
  onRetryInvoice,
  onCreateDraft,
  onOpenClassic,
}: {
  resource: ReadResource<InvoiceWorkspaceData>;
  invoiceResource: ReadResource<Invoice> | null;
  selection: InvoiceSelection;
  onRetry: () => void;
  onRetryInvoice: () => void;
  onCreateDraft: (request: CreateInvoiceRequest) => Promise<Invoice>;
  onOpenClassic: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted"><Receipt className="h-3.5 w-3.5" />Facturation locale</div>
        <h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">{selection === 'new-devis' ? 'Nouveau devis brouillon' : 'Détail du document'}</h2>
        <p className="mt-1 text-sm text-text-muted">Les données affichées viennent du module Facturation existant.</p>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {resource.status === 'loading' ? (
          <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement de la facturation…</div></StateShell>
        ) : resource.status === 'error' ? (
          <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{resource.error}</p><button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell>
        ) : selection === 'new-devis' ? (
          <DevisDraftForm data={resource.data} onCreateDraft={onCreateDraft} />
        ) : !invoiceResource || invoiceResource.status === 'loading' ? (
          <StateShell><div className="flex items-center gap-2 text-sm text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement du document…</div></StateShell>
        ) : invoiceResource.status === 'error' ? (
          <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">{invoiceResource.error}</p><button type="button" onClick={onRetryInvoice} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">Réessayer</button></div></StateShell>
        ) : invoiceResource.status === 'ready' ? (
          <ExistingInvoiceDetail data={resource.data} invoice={invoiceResource.data} />
        ) : (
          <StateShell><div className="text-center"><AlertCircle className="mx-auto h-5 w-5 text-warning" /><p className="mt-2 text-sm font-semibold text-text">Document introuvable</p></div></StateShell>
        )}
      </div>

      <div className="border-t border-border bg-surface p-4">
        <button type="button" onClick={onOpenClassic} className="flex w-full items-center justify-center gap-2 rounded-[10px] bg-text px-4 py-3 text-sm font-semibold text-white"><ExternalLink className="h-4 w-4" />Ouvrir la facturation complète</button>
      </div>
    </div>
  );
}
