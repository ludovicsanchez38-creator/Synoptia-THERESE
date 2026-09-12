import { useEffect, useMemo, useRef, useState } from 'react';
import { BoutonOuvrirLaVue } from './BoutonOuvrirLaVue';
import {
  AlertCircle,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  Circle,
  Clock3,
  FileCheck2,
  ListTodo,
  PanelRightClose,
  Receipt,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from 'lucide-react';
import { createDeliverable, updateDeliverable, type DeliverableResponse } from '../../services/api/crm-extended';
import { STATUTS_LIVRABLE, estEnRetard } from '../../lib/livrables';
import type { Invoice } from '../../services/api/invoices';
import type { Task } from '../../services/api/tasks';
import {
  usePrototypeDeliverableProjectData,
  usePrototypeDeliverablesProjects,
} from './usePrototypeDeliverablesData';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { usePanneauCouvrant } from '../../hooks/usePanneauCouvrant';
import { handleRovingFocus } from '../../lib/rovingFocus';
import { Spinner } from '../ui/Spinner';
import { Alerte, Button, Carte, EtatVide, Input, Select } from '../ui';

type DeliverableStatus = 'all' | 'a_faire' | 'en_cours' | 'en_revision' | 'valide';

const STATUS: Record<string, { label: string; textClass: string; tintClass: string; icon: typeof Circle }> = {
  a_faire: { label: 'À faire', textClass: 'text-text-muted', tintClass: 'bg-surface-2', icon: Circle },
  en_cours: { label: 'En cours', textClass: 'text-info', tintClass: 'bg-[var(--color-info-tint)]', icon: Clock3 },
  en_revision: { label: 'En révision', textClass: 'text-warning', tintClass: 'bg-[var(--color-warning-tint)]', icon: AlertCircle },
  valide: { label: 'Validé', textClass: 'text-success', tintClass: 'bg-[var(--color-success-tint)]', icon: CheckCircle2 },
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
  return estEnRetard(deliverable);
}

function messageDerreur(err: unknown): string {
  return err instanceof Error && err.message ? err.message : 'Écriture impossible pour le moment.';
}

/** P-048 : créer un livrable (titre, échéance, statut) depuis la vue. */
function AjoutLivrable({ projectId, onCree }: { projectId: string; onCree: (projectId: string, livrable: DeliverableResponse) => void }) {
  const [ouvert, setOuvert] = useState(false);
  const [titre, setTitre] = useState('');
  const [echeance, setEcheance] = useState('');
  const [statut, setStatut] = useState<string>('a_faire');
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [succes, setSucces] = useState<string | null>(null);
  const titreRef = useRef<HTMLInputElement>(null);

  const soumettre = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!titre.trim() || enCours) return;
    setEnCours(true);
    setErreur(null);
    setSucces(null);
    try {
      const cree = await createDeliverable({ project_id: projectId, title: titre.trim(), status: statut, ...(echeance ? { due_date: echeance } : {}) });
      onCree(projectId, cree);
      setTitre('');
      setEcheance('');
      setStatut('a_faire');
      setSucces(`Livrable « ${cree.title} » ajouté.`);
      setOuvert(false);
    } catch (err) {
      setErreur(messageDerreur(err));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div className="mt-3">
      {!ouvert ? (
        <Button type="button" onClick={() => { setOuvert(true); setSucces(null); requestAnimationFrame(() => titreRef.current?.focus()); }}>Ajouter un livrable</Button>
      ) : (
        <form onSubmit={soumettre} aria-label="Nouveau livrable" className="rounded-md border border-border bg-surface p-3 shadow-sm">
          <label className="block text-sm font-semibold text-text">Titre<Input ref={titreRef} required value={titre} onChange={(e) => setTitre(e.target.value)} maxLength={200} className="mt-1" /></label>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <label className="block text-sm font-semibold text-text">Échéance<Input type="date" value={echeance} onChange={(e) => setEcheance(e.target.value)} className="mt-1" /></label>
            <label className="block text-sm font-semibold text-text">Statut<Select value={statut} onChange={(e) => setStatut(e.target.value)} className="mt-1" options={STATUTS_LIVRABLE.map((code) => ({ value: code, label: STATUS[code].label }))} /></label>
          </div>
          {erreur && <Alerte className="mt-2" titre="Ajout impossible">{erreur}</Alerte>}
          <div className="mt-3 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => { setOuvert(false); setErreur(null); }}>Annuler</Button>
            <Button type="submit" disabled={!titre.trim() || enCours}>{enCours ? 'Ajout…' : 'Ajouter'}</Button>
          </div>
        </form>
      )}
      {succes && <p role="status" className="mt-2 text-xs text-success">{succes}</p>}
    </div>
  );
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

function DeliverableRow({ deliverable, onChangerStatut }: { deliverable: DeliverableResponse; onChangerStatut?: (id: string, statut: string) => Promise<void> }) {
  const status = STATUS[deliverable.status] ?? {
    label: deliverable.status || 'Statut inconnu',
    textClass: 'text-text-muted',
    tintClass: 'bg-surface-2',
    icon: Circle,
  };
  const Icon = status.icon;
  const overdue = isOverdue(deliverable);
  // P-048 (revue COCO, findings 2 et 5) : une seule écriture en vol par
  // livrable, la ligne prend le DTO renvoyé ; un statut existant inconnu
  // reste affiché tel quel jusqu'à un choix volontaire.
  const [enEcriture, setEnEcriture] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const statutConnu = (STATUTS_LIVRABLE as readonly string[]).includes(deliverable.status);
  const changer = async (cible: string) => {
    if (!onChangerStatut || cible === deliverable.status) return;
    setEnEcriture(true);
    setErreur(null);
    try {
      await onChangerStatut(deliverable.id, cible);
    } catch (err) {
      setErreur(messageDerreur(err));
    } finally {
      setEnEcriture(false);
    }
  };
  return (
    <Carte className="p-3" data-testid="deliverable-row">
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md ${status.tintClass} ${status.textClass}`}><Icon className="h-4 w-4" /></span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-semibold leading-5 text-text">{deliverable.title}</h4>
            {onChangerStatut ? (
              <Select aria-label={`Statut de ${deliverable.title}`} value={deliverable.status} disabled={enEcriture} onChange={(event) => void changer(event.target.value)} className={`min-w-32 shrink-0 font-semibold ${status.tintClass} ${status.textClass}`} options={[...(!statutConnu ? [{ value: deliverable.status, label: status.label }] : []), ...STATUTS_LIVRABLE.map((code) => ({ value: code, label: STATUS[code].label }))]} />
            ) : (
              <span className={`shrink-0 rounded-full border border-current px-2 py-0.5 text-xs font-semibold ${status.tintClass} ${status.textClass}`}>{status.label}</span>
            )}
          </div>
          {erreur && <div role="alert" className="mt-1 text-xs text-error">{erreur}</div>}
          {deliverable.description && <p className="mt-1 text-xs leading-5 text-text-muted">{deliverable.description}</p>}
          <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-text-muted">
            {deliverable.due_date && <span className={`flex items-center gap-1 ${overdue ? 'font-semibold text-warning' : ''}`}><CalendarClock className="h-3 w-3" />{overdue ? 'En retard · ' : 'Échéance · '}{formatDate(deliverable.due_date)}</span>}
            {deliverable.status === 'valide' && deliverable.completed_at && <span className="flex items-center gap-1 text-success"><CheckCircle2 className="h-3 w-3" />Validé · {formatDate(deliverable.completed_at)}</span>}
          </div>
        </div>
      </div>
    </Carte>
  );
}

function RelatedTask({ task }: { task: Task }) {
  return (
    <div className="flex items-start gap-2 border-t border-border py-2 first:border-0 first:pt-0">
      <ListTodo className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
      <div className="min-w-0 flex-1"><div className="truncate text-xs font-medium text-text">{task.title}</div><div className="mt-0.5 text-xs text-text-muted">{task.priority === 'urgent' ? 'Urgente' : task.priority === 'high' ? 'Priorité haute' : 'À traiter'}{task.due_date ? ` · ${formatDate(task.due_date)}` : ''}</div></div>
    </div>
  );
}

function RelatedInvoice({ invoice }: { invoice: Invoice }) {
  const statusLabels: Record<string, string> = { draft: 'Brouillon', sent: 'Envoyé', paid: 'Payée', overdue: 'En retard', accepted: 'Accepté', converted: 'Converti', refused: 'Refusé', expired: 'Expiré', cancelled: 'Annulé' };
  return (
    <div className="flex items-start gap-2 border-t border-border py-2 first:border-0 first:pt-0">
      <Receipt className="mt-0.5 h-3.5 w-3.5 shrink-0 text-domaine-factures" />
      <div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><span className="truncate text-xs font-medium text-text">{invoiceLabel(invoice)}</span><span className="shrink-0 text-xs font-semibold text-text">{formatMoney(invoice.total_ttc, invoice.currency)}</span></div><div className="mt-0.5 text-xs text-text-muted">{statusLabels[invoice.status] ?? invoice.status} · {formatDate(invoice.issue_date)}</div></div>
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
  const dialogRef = useRef<HTMLElement>(null);
  // Hotfix 0.48.1 : isolation seulement quand le panneau RECOUVRE la zone.
  // Revue passe 2 : le clavier reste À LA PAGE en toutes circonstances -
  // le rail et l'en-tête sont actifs, un piège les rendrait inatteignables,
  // et un réarmement au redimensionnement volerait Escape à une modale.
  const estCouvrant = usePanneauCouvrant();
  useDialogFocusTrap(dialogRef, {
    active: true,
    onEscape: onClose,
    isolateBackground: estCouvrant,
    piegeClavier: false,
  });

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
  const { data: loadedDetail, refresh: refreshDetail, appliquerLivrable } = usePrototypeDeliverableProjectData(selectedProject);
  // P-048 : les écritures capturent leur projet ; le hook ignore un résultat
  // qui arrive après un changement de projet.
  const changerStatut = async (projectId: string, id: string, statut: string) => {
    const dto = await updateDeliverable(id, { status: statut });
    appliquerLivrable?.(projectId, dto);
  };
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
    <aside ref={dialogRef} role="region" aria-labelledby="deliverables-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full max-w-[650px] flex-col border-l border-border bg-surface-2 shadow-lg sm:w-[calc(100%-48px)] xl:relative xl:w-[45%] xl:min-w-[460px] xl:shadow-none" data-testid="deliverables-workspace-canvas">
      <Button type="button" variant="secondary" size="icon" onClick={onClose} aria-label="Fermer le suivi client" className="absolute right-4 top-3.5 z-30"><PanelRightClose className="h-4 w-4" /></Button>
      <header className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted"><FileCheck2 className="h-3.5 w-3.5" />Suivi local unifié</div>
        <h2 id="deliverables-workspace-title" data-dialog-autofocus tabIndex={-1} className="mt-2 text-xl font-bold tracking-[-0.02em] text-text outline-none">Livrables et suivi client</h2>
        <p className="mt-1 text-sm text-text-muted">Promis, livré, tâches restantes et facturation du contact. Tu peux ajouter un livrable et changer son statut ; le reste se lit ici et se modifie dans sa vue.</p>
      </header>

      {projectsResource.status === 'loading' ? (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-text-muted"><Spinner taille="zone" className="text-accent" />Chargement du suivi réel…</div>
      ) : projectsResource.status === 'error' ? (
        <Alerte className="m-auto max-w-sm" ton="attention" titre="Suivi indisponible" icone={<AlertCircle className="h-5 w-5" />} action={<Button type="button" variant="secondary" onClick={() => void refreshProjects()}><RefreshCw className="h-4 w-4" />Réessayer</Button>}>{projectsResource.error}</Alerte>
      ) : projectsResource.data.length === 0 ? (
        <EtatVide className="m-auto max-w-sm" titre="Aucun projet enregistré" action={<Button type="button" onClick={onOpenProjects}>Gérer mes projets</Button>}><BriefcaseBusiness className="mx-auto mb-2 h-9 w-9" />Les livrables sont rattachés à un projet réel. Crée d’abord le projet dans la vue Projets.</EtatVide>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {projectLimitReached && <Alerte ton="attention" className="mb-4">Les 200 projets les plus récents sont affichés. Ouvre Projets pour consulter un projet plus ancien.</Alerte>}

          <div className="flex items-end gap-2"><label className="min-w-0 flex-1 text-sm font-semibold text-text">Projet suivi<Select aria-label="Projet suivi" value={selectedProjectId} onChange={(event) => { setSelectedProjectId(event.target.value); setStatusFilter('all'); }} className="mt-1.5 font-medium" options={projectsResource.data.map((project) => ({ value: project.id, label: project.name }))} /></label><Button type="button" variant="secondary" size="icon" onClick={() => void refreshDetail()} aria-label="Actualiser le suivi du projet"><RefreshCw className="h-4 w-4" /></Button></div>

          {view?.project && <>
            <Carte as="section" className="mt-4 p-4">
              <div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-text-muted"><UserRound className="h-3 w-3" />{contactLabel}</div><h3 className="mt-1 text-base font-bold text-text">{view.project.name}</h3></div><span className="rounded-full bg-bg px-2 py-1 text-xs font-semibold text-text-muted">{projectStatus}</span></div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center"><div className="rounded-md bg-surface-2 p-2"><div className="text-lg font-bold text-text">{detail?.deliverables.status === 'ready' ? view.deliverables.length : '—'}</div><div className="text-xs text-text-muted">Livrables</div></div><div className="rounded-md bg-accent-tint p-2"><div className="text-lg font-bold text-success">{detail?.deliverables.status === 'ready' ? view.validated : '—'}</div><div className="text-xs text-text-muted">Validés</div></div><div className="rounded-md bg-surface-2 p-2"><div className="text-lg font-bold text-text">{detail?.tasks.status === 'ready' ? view.tasks.length : '—'}</div><div className="text-xs text-text-muted">Tâches ouvertes</div></div></div>
              {detail?.deliverables.status === 'ready' && <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-label="Livrables validés" aria-valuemin={0} aria-valuemax={view.deliverables.length} aria-valuenow={view.validated} aria-valuetext={`${view.validated} livrable${view.validated > 1 ? 's' : ''} validé${view.validated > 1 ? 's' : ''} sur ${view.deliverables.length}`}><div className="h-full rounded-full bg-domaine-agenda transition-[width]" style={{ width: `${view.deliverables.length ? Math.round((view.validated / view.deliverables.length) * 100) : 0}%` }} /></div>}
            </Carte>

            {/* B-635 : des filtres de statut sur un ensemble vide ne filtrent rien. */}
            {view.deliverables.length > 0 && <div role="toolbar" aria-label="Filtrer les livrables" className="mt-4 flex flex-wrap gap-1.5">{STATUS_FILTERS.map((filter) => <button key={filter.id} data-deliverable-filter type="button" aria-pressed={statusFilter === filter.id} tabIndex={statusFilter === filter.id ? 0 : -1} onKeyDown={(event) => handleRovingFocus(event, '[data-deliverable-filter]', 'horizontal')} onClick={() => setStatusFilter(filter.id)} className={`rounded-full border px-2.5 py-1.5 text-sm font-semibold ${statusFilter === filter.id ? 'border-accent-fill bg-accent-fill text-accent-ink' : 'border-border bg-surface text-text-muted'}`}>{filter.label}</button>)}</div>}

            <section className="mt-3 space-y-2" aria-label="Livrables du projet">
              {!detail || detail.deliverables.status === 'loading' ? <div className="flex items-center justify-center gap-2 rounded-md border border-border bg-surface px-4 py-7 text-sm text-text-muted"><Spinner taille="bouton" />Chargement des livrables…</div> : detail.deliverables.status === 'error' ? <Alerte ton="attention">{detail.deliverables.error}</Alerte> : view.filteredDeliverables.length > 0 ? view.filteredDeliverables.map((deliverable) => <DeliverableRow key={deliverable.id} deliverable={deliverable} onChangerStatut={(id, statut) => changerStatut(view.project.id, id, statut)} />) : <EtatVide className="rounded-md border border-dashed border-border bg-surface" titre={view.deliverables.length === 0 ? 'Aucun livrable : ajoute le premier' : 'Aucun résultat'}>{view.deliverables.length === 0 ? 'Il sera rattaché à ce projet.' : 'Aucun livrable avec ce statut.'}</EtatVide>}
              <AjoutLivrable projectId={view.project.id} onCree={(projectId, livrable) => appliquerLivrable?.(projectId, livrable)} />
            </section>

            <section className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-md border border-border bg-surface p-3"><div className="mb-2 flex items-center gap-2 text-xs font-bold text-text"><ListTodo className="h-4 w-4 text-accent" />Reste à faire</div>{!detail || detail.tasks.status === 'loading' ? <p className="text-xs leading-5 text-text-muted">Chargement des tâches…</p> : detail.tasks.status === 'error' ? <p className="text-xs leading-5 text-warning">{detail.tasks.error}</p> : view.tasks.length > 0 ? view.tasks.slice(0, 4).map((task) => <RelatedTask key={task.id} task={task} />) : <p className="text-xs leading-5 text-text-muted">Aucune tâche ouverte reliée au projet.</p>}{detail?.taskLimitReached && <p className="mt-2 text-xs leading-4 text-warning">Limite de 1 000 tâches atteinte. Consulte la vue Tâches pour la liste complète.</p>}</div>
              <div className="rounded-md border border-border bg-surface p-3"><div className="mb-2 flex items-center gap-2 text-xs font-bold text-text"><Receipt className="h-4 w-4 text-domaine-factures" />Facturation du contact</div>{!selectedProject?.contact_id ? <p className="text-xs leading-5 text-text-muted">Projet sans contact : aucune recherche de facturation effectuée.</p> : !detail || detail.invoices.status === 'loading' ? <p className="text-xs leading-5 text-text-muted">Chargement de la facturation…</p> : detail.invoices.status === 'error' ? <p className="text-xs leading-5 text-warning">{detail.invoices.error}</p> : detail.invoices.data.length > 0 ? detail.invoices.data.slice(0, 4).map((invoice) => <RelatedInvoice key={invoice.id} invoice={invoice} />) : <p className="text-xs leading-5 text-text-muted">Aucun devis ou facture pour le contact relié.</p>}{detail?.invoiceLimitReached && <p className="mt-2 text-xs leading-4 text-warning">Limite de 100 documents atteinte. Consulte Facturation pour la liste complète.</p>}<p className="mt-2 border-t border-border pt-2 text-xs leading-4 text-text-muted">La facturation est reliée au contact du projet, pas au livrable lui-même.</p></div>
            </section>
          </>}

          <div className="mt-4 flex items-start gap-2 rounded-md border border-accent-cyan/30 bg-accent-tint p-3 text-sm leading-5 text-accent"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />Lu depuis Projets, CRM, Tâches et Facturation. Ajouter un livrable ou changer son statut écrit dans ta base locale ; aucune suppression ni synchronisation n’est déclenchée ici.</div>
          <div className="mt-3 grid grid-cols-2 gap-2"><BoutonOuvrirLaVue vue="projects" onOuvrir={onOpenProjects} className="rounded-md border border-border bg-surface px-3 py-2 text-sm font-semibold text-text" /><BoutonOuvrirLaVue vue="invoices" onOuvrir={onOpenInvoices} className="rounded-md border border-border bg-surface px-3 py-2 text-sm font-semibold text-text" /></div>
        </div>
      )}
    </aside>
  );
}
