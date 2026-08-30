import { lazy, Suspense, useRef } from 'react';
import { ArrowLeft } from 'lucide-react';
import type { AppView } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

const CRMPanel = lazy(() => import('../crm').then((module) => ({ default: module.CRMPanel })));
const EmailPanel = lazy(() => import('../email').then((module) => ({ default: module.EmailPanel })));
const CalendarPanel = lazy(() => import('../calendar').then((module) => ({ default: module.CalendarPanel })));
const TasksPanel = lazy(() => import('../tasks').then((module) => ({ default: module.TasksPanel })));
const InvoicesPanel = lazy(() => import('../invoices').then((module) => ({ default: module.InvoicesPanel })));
const MemoryPanel = lazy(() => import('../memory/MemoryPanel').then((module) => ({ default: module.MemoryPanel })));
const FileBrowser = lazy(() => import('../files/FileBrowser').then((module) => ({ default: module.FileBrowser })));
const ProjectsPanel = lazy(() => import('../memory/ProjectsPanel').then((module) => ({ default: module.ProjectsPanel })));
const DocumentsList = lazy(() => import('../documents/DocumentsList').then((module) => ({ default: module.DocumentsList })));

export const viewLabels: Record<Exclude<AppView, 'chat'>, string> = {
  memory: 'Contacts',
  crm: 'Pipeline',
  email: 'Email',
  calendar: 'Agenda',
  tasks: 'Tâches',
  invoices: 'Devis et factures',
  files: 'Fichiers',
  projects: 'Projets',
  documents: 'Documents',
};

export function PrototypeUnifiedViewCanvas({
  view,
  onClose,
}: {
  view: Exclude<AppView, 'chat'>;
  onClose: () => void;
}) {
  const openNewContact = usePanelStore((state) => state.openNewContact);
  const openEditContact = usePanelStore((state) => state.openEditContact);
  const dialogRef = useRef<HTMLElement>(null);
  // Hotfix 0.48.1 : une vue embarquée est TOUJOURS côte à côte (flex-1) -
  // jamais une modale. Focus initial et restauration conservés, mais ni
  // isolation du fond ni piégeage clavier : la colonne principale reste
  // vivante et Tab peut y revenir. Échap est géré par la cascade de la coque.
  useDialogFocusTrap(dialogRef, {
    active: true,
    isolateBackground: false,
    piegeClavier: false,
  });

  return (
    <section ref={dialogRef} role="region" aria-labelledby="prototype-unified-view-title" tabIndex={-1} className="relative flex min-w-0 flex-1 flex-col overflow-hidden bg-bg" data-testid="prototype-unified-view" data-view={view}>
      <header className="flex h-12 shrink-0 items-center gap-3 border-b border-border bg-surface px-4">
        <button type="button" onClick={onClose} aria-label="Revenir à la conversation unifiée" className="flex items-center gap-1.5 rounded-sm px-2 py-1.5 text-xs font-medium text-text-muted hover:bg-surface-elevated hover:text-text">
          <ArrowLeft className="h-4 w-4" />
          Retour
        </button>
        <h2 id="prototype-unified-view-title" data-dialog-autofocus tabIndex={-1} className="text-sm font-semibold text-text outline-none">{viewLabels[view]}</h2>
      </header>
      {/* flex-col obligatoire : borne la hauteur des panels embarqués
          (sinon leur scroll interne est inerte - bug « impossible de
          scroller dans le mail », revue harmonisation 17/07) */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <Suspense fallback={<div className="grid h-full place-items-center text-sm text-text-muted">Chargement…</div>}>
          {view === 'crm' && <CRMPanel standalone />}
          {view === 'email' && <EmailPanel standalone />}
          {view === 'calendar' && <CalendarPanel standalone />}
          {view === 'tasks' && <TasksPanel standalone />}
          {view === 'invoices' && <InvoicesPanel standalone />}
          {view === 'memory' && <MemoryPanel standalone onNewContact={openNewContact} onEditContact={openEditContact} />}
          {view === 'files' && <div className="h-full overflow-auto p-4"><FileBrowser /></div>}
          {view === 'projects' && <ProjectsPanel />}
          {view === 'documents' && <DocumentsList />}
        </Suspense>
      </div>
    </section>
  );
}
