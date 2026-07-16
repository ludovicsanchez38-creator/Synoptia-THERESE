import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  Circle,
  Clock3,
  FileCheck2,
  ListTodo,
  Loader2,
  PanelRightClose,
  Receipt,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from 'lucide-react';
import type { DeliverableResponse } from '../../services/api/crm-extended';
import type { Invoice } from '../../services/api/invoices';
import type { Task } from '../../services/api/tasks';
import {
  usePrototypeDeliverableProjectData,
  usePrototypeDeliverablesProjects,
} from './usePrototypeDeliverablesData';

type DeliverableStatus = 'all' | 'a_faire' | 'en_cours' | 'en_revision' | 'valide';

const STATUS: Record<string, { label: string; color: string; icon: typeof Circle }> = {
  a_faire: { label: 'À faire', color: '#69788F', icon: Circle },
  en_cours: { label: 'En cours', color: '#0F8FB3', icon: Clock3 },
  en_revision: { label: 'En révision', color: '#B45309', icon: AlertCircle },
  valide: { label: 'Validé', color: '#0F766E', icon: CheckCircle2 },
};

const STATUS_FILTERS: Array<{ id: DeliverableStatus; label: string }> = [
  { id: 'all', label: 'Tous' },
  { id: 'a_faire', label: 'À faire' },
  { id: 'en_cours', label: 'En cours' },
  { id: 'en_revision', label: 'Révision' },
  { id: 'valide', label: 'Validés' },
];

function formatDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date non reconnue';
  return new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' }).format(date);
}

function isOverdue(deliverable: DeliverableResponse): boolean {
  if (!deliverable.due_date || deliverable.status === 'valide') return false;
  const dueDate = new Date(deliverable.due_date);
  return Number.isFinite(dueDate.getTime()) && dueDate.getTime() < Date.now();
}

function contactName(contact: { first_name: string | null; last_name: string | null; company: string | null } | undefined): string {
  if (!contact) return 'Contact non relié';
  return [contact.first_name, contact.last_name].filter(Boolean).join(' ').trim() || contact.company || 'Contact sans nom';
}

function formatMoney(value: number, currency: string): string {
  try {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);
  } catch {
    return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(value)} ${currency}`;
  }
}

function invoiceLabel(invoice: Invoice): string {
  const types = { devis: 'Devis', facture: 'Facture', avoir: 'Avoir' };
  return `${types[invoice.document_type]} ${invoice.invoice_number}`;
}

function DeliverableRow({ deliverable }: { deliverable: DeliverableResponse }) {
  const status = STATUS[deliverable.status] ?? { label: deliverable.status || 'Statut inconnu', color: '#69788F', icon: Circle };
  const Icon = status.icon;
  const overdue = isOverdue(deliverable);
  return (
    <article className="rounded-[11px] border border-border bg-surface p-3" data-testid="deliverable-row">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-[9px] bg-bg" style={{ color: status.color }}><Icon className="h-4 w-4" /></span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-semibold leading-5 text-text">{deliverable.title}</h4>
            <span className="shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-semibold" style={{ borderColor: `${status.color}55`, color: status.color, backgroundColor: `${status.color}0D` }}>{status.label}</span>
          </div>
          {deliverable.description && <p className="mt-1 text-xs leading-5 text-text-muted">{deliverable.description}</p>}
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-text-muted">
            {deliverable.due_date && <span className={`flex items-center gap-1 ${overdue ? 'font-semibold text-warning' : ''}`}><CalendarClock className="h-3 w-3" />{overdue ? 'En retard · ' : 'Échéance · '}{formatDate(deliverable.due_date)}</span>}
            {deliverable.status === 'valide' && deliverable.completed_at && <span className="flex items-center gap-1 text-success"><CheckCircle2 className="h-3 w-3" />Validé · {formatDate(deliverable.completed_at)}</span>}
          </div>
        </div>
      </div>
    </article>
  );
}

function RelatedTask({ task }: { task: Task }) {
  return (
    <div className="flex items-start gap-2 border-t border-border py-2 first:border-0 first:pt-0">
      <ListTodo className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
      <div className="min-w-0 flex-1"><div className="truncate text-xs font-medium text-text">{task.title}</div><div className="mt-0.5 text-[10px] text-text-muted">{task.priority === 'urgent' ? 'Urgente' : task.priority === 'high' ? 'Priorité haute' : 'À traiter'}{task.due_date ? ` · ${formatDate(task.due_date)}` : ''}</div></div>
    </div>
  );
}

function RelatedInvoice({ invoice }: { invoice: Invoice }) {
  const statusLabels: Record<string, string> = { draft: 'Brouillon', sent: 'Envoyé', paid: 'Payée', overdue: 'En retard', accepted: 'Accepté', converted: 'Converti', refused: 'Refusé', expired: 'Expiré', cancelled: 'Annulé' };
  return (
    <div className="flex items-start gap-2 border-t border-border py-2 first:border-0 first:pt-0">
      <Receipt className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--k3)]" />
      <div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><span className="truncate text-xs font-medium text-text">{invoiceLabel(invoice)}</span><span className="shrink-0 text-[10px] font-semibold text-text">{formatMoney(invoice.total_ttc, invoice.currency)}</span></div><div className="mt-0.5 text-[10px] text-text-muted">{statusLabels[invoice.status] ?? invoice.status} · {formatDate(invoice.issue_date)}</div></div>
    </div>
  );
}

export function DeliverablesWorkspaceCanvas({
  onClose,
  onOpenProjects,
  onOpenInvoices,
}: {
  onClose: () => void;
  onOpenProjects: () => void;
  onOpenInvoices: () => void;
}) {
  const { resource: projectsResource, refresh: refreshProjects, limitReached: projectLimitReached } = usePrototypeDeliverablesProjects();
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<DeliverableStatus>('all');

  useEffect(() => {
    if (projectsResource.status !== 'ready') return;
    if (!projectsResource.data.some((project) => project.id === selectedProjectId)) {
      setSelectedProjectId(projectsResource.data[0]?.id ?? '');
      setStatusFilter('all');
    }
  }, [projectsResource, selectedProjectId]);

  const selectedProject = projectsResource.status === 'ready'
    ? projectsResource.data.find((project) => project.id === selectedProjectId) ?? null
    : null;
  const { data: loadedDetail, refresh: refreshDetail } = usePrototypeDeliverableProjectData(selectedProject);
  const detail = loadedDetail?.projectId === selectedProjectId ? loadedDetail : null;

  const view = useMemo(() => {
    if (!selectedProject || !detail) return null;
    const deliverables = detail.deliverables.status === 'ready' ? detail.deliverables.data : [];
    const filteredDeliverables = statusFilter === 'all' ? deliverables : deliverables.filter((item) => item.status === statusFilter);
    const tasks = detail.tasks.status === 'ready'
      ? detail.tasks.data.filter((item) => item.status !== 'done' && item.status !== 'cancelled')
      : [];
    const validated = deliverables.filter((item) => item.status === 'valide').length;
    return { project: selectedProject, deliverables, filteredDeliverables, tasks, validated };
  }, [detail, selectedProject, statusFilter]);

  const contactLabel = !selectedProject?.contact_id
    ? 'Projet sans contact'
    : !detail || detail.contact.status === 'loading'
      ? 'Contact en chargement…'
      : detail.contact.status === 'error'
        ? 'Contact indisponible'
        : contactName(detail.contact.data ?? undefined);
  const projectStatus = selectedProject?.status === 'completed'
    ? 'Terminé'
    : selectedProject?.status === 'on_hold'
      ? 'En pause'
      : selectedProject?.status === 'cancelled'
        ? 'Annulé'
        : selectedProject?.status === 'active'
          ? 'Actif'
          : selectedProject?.status || 'Statut inconnu';

  return (
    <aside className="absolute inset-y-0 right-0 z-20 flex h-full w-full max-w-[650px] flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] sm:w-[calc(100%-48px)] xl:relative xl:w-[45%] xl:min-w-[460px] xl:shadow-none" data-testid="deliverables-workspace-canvas">
      <button type="button" onClick={onClose} aria-label="Fermer le suivi client" className="absolute right-4 top-3.5 z-30 grid h-9 w-9 place-items-center rounded-[9px] border border-border bg-surface text-text-muted shadow-sm hover:text-text"><PanelRightClose className="h-4 w-4" /></button>
      <header className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted"><FileCheck2 className="h-3.5 w-3.5" />Lecture locale unifiée</div>
        <h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">Livrables et suivi client</h2>
        <p className="mt-1 text-sm text-text-muted">Promis, livré, tâches restantes et facturation du contact, sans modifier les données.</p>
      </header>

      {projectsResource.status === 'loading' ? (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-text-muted"><Loader2 className="h-5 w-5 animate-spin text-accent" />Chargement du suivi réel…</div>
      ) : projectsResource.status === 'error' ? (
        <div className="m-auto max-w-sm px-6 text-center"><AlertCircle className="mx-auto h-8 w-8 text-warning" /><h3 className="mt-3 text-sm font-bold text-text">Suivi indisponible</h3><p className="mt-1 text-xs leading-5 text-text-muted">{projectsResource.error}</p><button type="button" onClick={() => void refreshProjects()} className="mt-4 inline-flex items-center gap-2 rounded-[9px] bg-text px-4 py-2 text-xs font-semibold text-white"><RefreshCw className="h-3.5 w-3.5" />Réessayer</button></div>
      ) : projectsResource.data.length === 0 ? (
        <div className="m-auto max-w-sm px-6 text-center"><BriefcaseBusiness className="mx-auto h-9 w-9 text-text-muted" /><h3 className="mt-3 text-sm font-bold text-text">Aucun projet enregistré</h3><p className="mt-1 text-xs leading-5 text-text-muted">Les livrables sont rattachés à un projet réel. Crée d’abord le projet dans la vue Projets.</p><button type="button" onClick={onOpenProjects} className="mt-4 rounded-[9px] bg-text px-4 py-2 text-xs font-semibold text-white">Ouvrir Projets</button></div>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {projectLimitReached && <div role="status" className="mb-4 rounded-[10px] border border-warning/40 bg-[var(--color-warning-tint)] px-3 py-2 text-xs leading-5 text-warning">Les 200 projets les plus récents sont affichés. Ouvre Projets pour consulter un projet plus ancien.</div>}

          <div className="flex items-end gap-2"><label className="min-w-0 flex-1 text-xs font-semibold text-text">Projet suivi<select aria-label="Projet suivi" value={selectedProjectId} onChange={(event) => { setSelectedProjectId(event.target.value); setStatusFilter('all'); }} className="mt-1.5 w-full rounded-[10px] border border-border bg-surface px-3 py-2.5 text-sm font-medium text-text outline-none focus:border-[#22D3EE]">{projectsResource.data.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label><button type="button" onClick={() => void refreshDetail()} aria-label="Actualiser le suivi du projet" className="grid h-[42px] w-[42px] place-items-center rounded-[10px] border border-border bg-surface text-text-muted"><RefreshCw className="h-4 w-4" /></button></div>

          {view?.project && <>
            <section className="mt-4 rounded-[13px] border border-border bg-surface p-4">
              <div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted"><UserRound className="h-3 w-3" />{contactLabel}</div><h3 className="mt-1 text-base font-bold text-text">{view.project.name}</h3></div><span className="rounded-full bg-bg px-2 py-1 text-[10px] font-semibold text-text-muted">{projectStatus}</span></div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center"><div className="rounded-[9px] bg-surface-2 p-2"><div className="text-lg font-bold text-text">{detail?.deliverables.status === 'ready' ? view.deliverables.length : '—'}</div><div className="text-[9px] text-text-muted">Livrables</div></div><div className="rounded-[9px] bg-accent-tint p-2"><div className="text-lg font-bold text-success">{detail?.deliverables.status === 'ready' ? view.validated : '—'}</div><div className="text-[9px] text-text-muted">Validés</div></div><div className="rounded-[9px] bg-surface-2 p-2"><div className="text-lg font-bold text-text">{detail?.tasks.status === 'ready' ? view.tasks.length : '—'}</div><div className="text-[9px] text-text-muted">Tâches ouvertes</div></div></div>
              {detail?.deliverables.status === 'ready' && <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-2"><div className="h-full rounded-full bg-[var(--k1)] transition-[width]" style={{ width: `${view.deliverables.length ? Math.round((view.validated / view.deliverables.length) * 100) : 0}%` }} /></div>}
            </section>

            <div className="mt-4 flex flex-wrap gap-1.5">{STATUS_FILTERS.map((filter) => <button key={filter.id} type="button" onClick={() => setStatusFilter(filter.id)} className={`rounded-full border px-2.5 py-1.5 text-[10px] font-semibold ${statusFilter === filter.id ? 'border-text bg-text text-white' : 'border-border bg-surface text-text-muted'}`}>{filter.label}</button>)}</div>

            <section className="mt-3 space-y-2" aria-label="Livrables du projet">
              {!detail || detail.deliverables.status === 'loading' ? <div className="flex items-center justify-center gap-2 rounded-[11px] border border-border bg-surface px-4 py-7 text-xs text-text-muted"><Loader2 className="h-4 w-4 animate-spin" />Chargement des livrables…</div> : detail.deliverables.status === 'error' ? <div role="alert" className="rounded-[11px] border border-warning/40 bg-[var(--color-warning-tint)] px-4 py-4 text-xs text-warning">{detail.deliverables.error}</div> : view.filteredDeliverables.length > 0 ? view.filteredDeliverables.map((deliverable) => <DeliverableRow key={deliverable.id} deliverable={deliverable} />) : <div className="rounded-[11px] border border-dashed border-[#C8D3E3] bg-surface px-4 py-7 text-center text-xs text-text-muted">{view.deliverables.length === 0 ? 'Aucun livrable réel n’est encore rattaché à ce projet.' : 'Aucun livrable avec ce statut.'}</div>}
            </section>

            <section className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[12px] border border-border bg-surface p-3"><div className="mb-2 flex items-center gap-2 text-xs font-bold text-text"><ListTodo className="h-4 w-4 text-accent" />Reste à faire</div>{!detail || detail.tasks.status === 'loading' ? <p className="text-[11px] leading-5 text-text-muted">Chargement des tâches…</p> : detail.tasks.status === 'error' ? <p className="text-[11px] leading-5 text-warning">{detail.tasks.error}</p> : view.tasks.length > 0 ? view.tasks.slice(0, 4).map((task) => <RelatedTask key={task.id} task={task} />) : <p className="text-[11px] leading-5 text-text-muted">Aucune tâche ouverte reliée au projet.</p>}{detail?.taskLimitReached && <p className="mt-2 text-[9px] leading-4 text-warning">Limite de 1 000 tâches atteinte. Consulte la vue Tâches pour la liste complète.</p>}</div>
              <div className="rounded-[12px] border border-border bg-surface p-3"><div className="mb-2 flex items-center gap-2 text-xs font-bold text-text"><Receipt className="h-4 w-4 text-[var(--k3)]" />Facturation du contact</div>{!selectedProject?.contact_id ? <p className="text-[11px] leading-5 text-text-muted">Projet sans contact : aucune recherche de facturation effectuée.</p> : !detail || detail.invoices.status === 'loading' ? <p className="text-[11px] leading-5 text-text-muted">Chargement de la facturation…</p> : detail.invoices.status === 'error' ? <p className="text-[11px] leading-5 text-warning">{detail.invoices.error}</p> : detail.invoices.data.length > 0 ? detail.invoices.data.slice(0, 4).map((invoice) => <RelatedInvoice key={invoice.id} invoice={invoice} />) : <p className="text-[11px] leading-5 text-text-muted">Aucun devis ou facture pour le contact relié.</p>}{detail?.invoiceLimitReached && <p className="mt-2 text-[9px] leading-4 text-warning">Limite de 100 documents atteinte. Consulte Facturation pour la liste complète.</p>}<p className="mt-2 border-t border-border pt-2 text-[9px] leading-4 text-text-muted">La facturation est reliée au contact du projet, pas au livrable lui-même.</p></div>
            </section>
          </>}

          <div className="mt-4 flex items-start gap-2 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3 text-xs leading-5 text-accent"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />Lecture seule depuis Projets, CRM, Tâches et Facturation. Aucune validation, suppression ou synchronisation n’est déclenchée ici.</div>
          <div className="mt-3 grid grid-cols-2 gap-2"><button type="button" onClick={onOpenProjects} className="rounded-[9px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Ouvrir Projets</button><button type="button" onClick={onOpenInvoices} className="rounded-[9px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Ouvrir Facturation</button></div>
        </div>
      )}
    </aside>
  );
}
