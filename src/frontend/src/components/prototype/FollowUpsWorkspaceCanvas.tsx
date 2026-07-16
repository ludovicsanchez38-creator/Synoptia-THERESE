import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Bell,
  CalendarClock,
  CheckCircle2,
  Loader2,
  Mail,
  PanelRightClose,
  Pencil,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import {
  deleteFollowUp,
  listFollowUps,
  updateFollowUp,
  type EmailFollowUp,
  type FollowUpStatus,
} from '../../services/api/follow-ups';

const FILTERS: Array<{ id: 'all' | FollowUpStatus; label: string }> = [
  { id: 'all', label: 'Toutes' },
  { id: 'pending', label: 'À traiter' },
  { id: 'done', label: 'Terminées' },
  { id: 'cancelled', label: 'Annulées' },
];

function formatDueDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
}

function dateInputValue(value: string): string {
  return value.slice(0, 10);
}

export function FollowUpsWorkspaceCanvas({
  onClose,
  onOpenEmail,
}: {
  onClose: () => void;
  onOpenEmail: () => void;
}) {
  const [items, setItems] = useState<EmailFollowUp[]>([]);
  const [filter, setFilter] = useState<'all' | FollowUpStatus>('pending');
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingDate, setEditingDate] = useState('');
  const [editingNote, setEditingNote] = useState('');
  const [deleteConfirmation, setDeleteConfirmation] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      setItems(await listFollowUps());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Impossible de charger les relances.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const visibleItems = useMemo(
    () => filter === 'all' ? items : items.filter((item) => item.status === filter),
    [filter, items],
  );

  async function mutate(id: string, operation: () => Promise<EmailFollowUp>) {
    setPendingId(id);
    setError(null);
    try {
      const updated = await operation();
      setItems((current) => current.map((item) => item.id === id ? updated : item));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'La relance n’a pas pu être modifiée.');
    } finally {
      setPendingId(null);
    }
  }

  async function saveEdit(item: EmailFollowUp) {
    if (!editingDate) return;
    await mutate(item.id, () => updateFollowUp(item.id, {
      due_date: `${editingDate}T09:00:00`,
      note: editingNote.trim(),
    }));
    setEditingId(null);
  }

  async function confirmDelete(id: string) {
    setPendingId(id);
    setError(null);
    try {
      await deleteFollowUp(id);
      setItems((current) => current.filter((item) => item.id !== id));
      setDeleteConfirmation(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'La relance n’a pas pu être supprimée.');
    } finally {
      setPendingId(null);
    }
  }

  return (
    <aside className="absolute inset-y-0 right-0 z-20 flex h-full w-full flex-col border-l border-border bg-surface-2 shadow-[-18px_0_45px_rgba(16,28,54,0.12)] xl:w-[58%] xl:min-w-[680px]" data-testid="follow-ups-workspace-canvas">
      <header className="relative shrink-0 border-b border-border bg-surface px-5 py-4 pr-16">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-[10px] border border-text bg-[var(--color-warning-tint)] text-warning shadow-[2px_2px_0_var(--btn-shadow-color)]"><Bell className="h-4 w-4" /></span>
          <div><h2 className="text-lg font-bold text-text">Relances et alertes</h2><p className="mt-0.5 text-xs text-text-muted">Échéances réelles liées aux emails, modifiables sans quitter le fil.</p></div>
        </div>
        <button type="button" onClick={onClose} aria-label="Fermer les relances" className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-[9px] border border-border bg-surface text-text-muted"><PanelRightClose className="h-4 w-4" /></button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-1.5">{FILTERS.map((entry) => <button key={entry.id} type="button" onClick={() => setFilter(entry.id)} className={`rounded-full border px-3 py-1.5 text-[10px] font-semibold ${filter === entry.id ? 'border-text bg-text text-white' : 'border-border bg-surface text-text-muted'}`}>{entry.label}</button>)}</div>
          <div className="flex gap-2"><button type="button" onClick={() => void refresh()} aria-label="Actualiser les relances" className="grid h-8 w-8 place-items-center rounded-[8px] border border-border bg-surface text-text-muted"><RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} /></button><button type="button" onClick={onOpenEmail} className="inline-flex items-center gap-1.5 rounded-[8px] bg-text px-3 py-2 text-xs font-semibold text-white"><Mail className="h-3.5 w-3.5" />Créer depuis un email</button></div>
        </div>

        {error && <div role="alert" className="mt-3 rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error"><AlertCircle className="mr-1 inline h-4 w-4" />{error}</div>}

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto">
          {loading ? <div className="grid min-h-56 place-items-center text-sm text-text-muted"><div><Loader2 className="mx-auto mb-2 h-5 w-5 animate-spin" />Chargement des relances…</div></div> : visibleItems.length === 0 ? <div className="grid min-h-56 place-items-center rounded-[12px] border border-dashed border-border bg-surface text-center text-sm text-text-muted"><div><CheckCircle2 className="mx-auto mb-2 h-8 w-8 opacity-50" />Aucune relance dans cette catégorie.</div></div> : <div className="space-y-2">{visibleItems.map((item) => {
            const busy = pendingId === item.id;
            const overdue = item.status === 'pending' && new Date(item.due_date).getTime() < Date.now();
            return <article key={item.id} className="rounded-[11px] border border-border bg-surface p-4" data-testid="follow-up-row">
              {editingId === item.id ? <div><div className="grid gap-3 sm:grid-cols-[180px_1fr]"><label className="text-xs font-semibold text-text">Nouvelle échéance<input aria-label="Nouvelle échéance" type="date" value={editingDate} onChange={(event) => setEditingDate(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border px-3 py-2 font-normal" /></label><label className="text-xs font-semibold text-text">Note<input aria-label="Note de relance" value={editingNote} onChange={(event) => setEditingNote(event.target.value)} className="mt-1.5 w-full rounded-[8px] border border-border px-3 py-2 font-normal" /></label></div><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setEditingId(null)} className="rounded-[7px] px-3 py-2 text-xs font-semibold text-text-muted">Annuler</button><button type="button" onClick={() => void saveEdit(item)} disabled={!editingDate || busy} className="rounded-[7px] bg-text px-3 py-2 text-xs font-semibold text-white">Enregistrer</button></div></div> : deleteConfirmation === item.id ? <div className="text-xs text-error"><strong>Supprimer définitivement cette relance ?</strong><div className="mt-3 flex justify-end gap-2"><button type="button" onClick={() => setDeleteConfirmation(null)} className="rounded-[7px] border border-border px-3 py-2 font-semibold">Annuler</button><button type="button" onClick={() => void confirmDelete(item.id)} disabled={busy} className="rounded-[7px] bg-[#A61B1B] px-3 py-2 font-semibold text-white">Confirmer</button></div></div> : <div className="flex items-start gap-3"><span className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-[9px] ${item.status === 'done' ? 'bg-[var(--color-success-tint)] text-success' : overdue ? 'bg-[var(--color-warning-tint)] text-warning' : 'bg-accent-tint text-accent'}`}>{item.status === 'done' ? <CheckCircle2 className="h-4 w-4" /> : <CalendarClock className="h-4 w-4" />}</span><div className="min-w-0 flex-1"><h3 className="truncate text-sm font-semibold text-text">{item.email_subject || 'Email sans objet'}</h3><p className="mt-0.5 text-[10px] text-text-muted">{item.contact_name || item.email_from || 'Expéditeur non disponible'}</p>{item.note && <p className="mt-2 text-xs leading-5 text-text-muted">{item.note}</p>}<div className={`mt-2 text-[10px] font-semibold ${overdue ? 'text-warning' : 'text-text-muted'}`}>{overdue ? 'En retard · ' : 'Échéance · '}{formatDueDate(item.due_date)}</div></div><div className="flex shrink-0 gap-1"><button type="button" aria-label={`Modifier ${item.email_subject || 'la relance'}`} onClick={() => { setEditingId(item.id); setEditingDate(dateInputValue(item.due_date)); setEditingNote(item.note || ''); }} className="grid h-8 w-8 place-items-center rounded-[8px] text-text-muted hover:bg-bg"><Pencil className="h-3.5 w-3.5" /></button>{item.status === 'pending' ? <button type="button" aria-label={`Terminer ${item.email_subject || 'la relance'}`} onClick={() => void mutate(item.id, () => updateFollowUp(item.id, { status: 'done' }))} disabled={busy} className="grid h-8 w-8 place-items-center rounded-[8px] text-success hover:bg-[var(--color-success-tint)]"><CheckCircle2 className="h-3.5 w-3.5" /></button> : <button type="button" aria-label={`Réouvrir ${item.email_subject || 'la relance'}`} onClick={() => void mutate(item.id, () => updateFollowUp(item.id, { status: 'pending' }))} disabled={busy} className="grid h-8 w-8 place-items-center rounded-[8px] text-accent hover:bg-accent-tint"><RefreshCw className="h-3.5 w-3.5" /></button>}<button type="button" aria-label={`Supprimer ${item.email_subject || 'la relance'}`} onClick={() => setDeleteConfirmation(item.id)} className="grid h-8 w-8 place-items-center rounded-[8px] text-error hover:bg-[var(--color-error-tint)]"><Trash2 className="h-3.5 w-3.5" /></button></div></div>}
            </article>;
          })}</div>}
        </div>
      </div>
    </aside>
  );
}
