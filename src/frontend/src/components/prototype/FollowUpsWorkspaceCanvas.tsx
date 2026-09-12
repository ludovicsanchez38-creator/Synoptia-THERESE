import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  Bell,
  CalendarClock,
  CheckCircle2,
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
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { usePanneauCouvrant } from '../../hooks/usePanneauCouvrant';
import { parisDateKey } from '../../lib/civilDate';
import { handleRovingFocus } from '../../lib/rovingFocus';
import { Alerte, Button, Carte, EtatVide, Input } from '../ui';
import { Spinner } from '../ui/Spinner';

const FILTERS: Array<{ id: 'all' | FollowUpStatus; label: string }> = [
  { id: 'all', label: 'Toutes' },
  { id: 'pending', label: 'À traiter' },
  { id: 'done', label: 'Terminées' },
  { id: 'cancelled', label: 'Annulées' },
];

/**
 * B-062 : une echeance de relance est un JOUR CIVIL, jamais un instant.
 *
 * `timeStyle: 'short'` affichait la constante de remplissage `T09:00:00`
 * (civil_time.HEURE_DE_RELANCE) comme si l'utilisateur l'avait choisie. Il n'y
 * a pas d'heure a montrer : l'ecran ne collecte qu'une date.
 */
function formatDueDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('fr-FR', { dateStyle: 'medium' });
}

/**
 * Une relance est-elle en retard ? Comparaison de JOURS CIVILS de Paris,
 * comme `list_due_follow_ups` cote serveur (follow_ups.py:133, qui tronque a
 * dix caracteres apres `date_civile_paris`). Comparer des instants faisait
 * basculer l'echeance du jour meme a 09 h 01.
 */
function estEnRetard(dueDate: string, maintenant: Date): boolean {
  return parisDateKey(dueDate) < parisDateKey(maintenant.toISOString());
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

  async function mutate(id: string, operation: () => Promise<EmailFollowUp>): Promise<boolean> {
    setPendingId(id);
    setError(null);
    try {
      const updated = await operation();
      setItems((current) => current.map((item) => item.id === id ? updated : item));
      return true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'La relance n’a pas pu être modifiée.');
      return false;
    } finally {
      setPendingId(null);
    }
  }

  async function saveEdit(item: EmailFollowUp) {
    if (!editingDate) return;
    const saved = await mutate(item.id, () => updateFollowUp(item.id, {
      due_date: `${editingDate}T09:00:00`,
      note: editingNote.trim(),
    }));
    if (saved) setEditingId(null);
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
    <aside ref={dialogRef} role="region" aria-labelledby="follow-ups-workspace-title" tabIndex={-1} className="absolute inset-y-0 right-0 z-20 flex h-full w-full flex-col border-l border-border bg-surface-2 shadow-lg sm:w-[calc(100%-48px)] xl:relative xl:w-[58%] xl:min-w-[680px] xl:shadow-none" data-testid="follow-ups-workspace-canvas">
      <header className="relative shrink-0 border-b border-border bg-surface px-5 py-4 pr-16">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-md border border-border bg-[var(--color-warning-tint)] text-warning shadow-sm"><Bell className="h-4 w-4" /></span>
          <div><h2 id="follow-ups-workspace-title" data-dialog-autofocus tabIndex={-1} className="text-lg font-bold text-text outline-none">Relances et alertes</h2><p className="mt-0.5 text-xs text-text-muted">Échéances réelles liées aux emails, modifiables sans quitter le fil.</p></div>
        </div>
        <Button type="button" variant="secondary" size="icon" onClick={onClose} aria-label="Fermer les relances" className="absolute right-4 top-4 text-text-muted"><PanelRightClose className="h-[18px] w-[18px]" /></Button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div role="toolbar" aria-label="Filtrer les relances" className="flex flex-wrap gap-1.5 rounded-md border border-border bg-surface p-1">{FILTERS.map((entry) => <button key={entry.id} data-follow-up-filter type="button" aria-pressed={filter === entry.id} tabIndex={filter === entry.id ? 0 : -1} onKeyDown={(event) => handleRovingFocus(event, '[data-follow-up-filter]', 'horizontal')} onClick={() => setFilter(entry.id)} className={`min-h-9 rounded-sm px-3 py-2 text-sm font-semibold transition-colors ${filter === entry.id ? 'bg-accent-tint text-accent' : 'text-text-muted hover:bg-surface-2 hover:text-text'}`}>{entry.label}</button>)}</div>
          <div className="flex flex-wrap gap-2 max-[840px]:basis-full"><Button type="button" variant="secondary" size="icon" onClick={() => void refresh()} aria-label="Actualiser les relances"><RefreshCw className={`h-[18px] w-[18px] ${loading ? 'animate-spin' : ''}`} /></Button><Button type="button" onClick={onOpenEmail}><Mail className="h-[18px] w-[18px]" />Créer depuis un email</Button></div>
        </div>

        {error && (
          <Alerte id="follow-ups-error" className="mt-3" titre="Relances indisponibles" icone={<AlertCircle className="h-4 w-4" />} action={<Button type="button" variant="secondary" onClick={() => void refresh()}>Réessayer</Button>}>{error}</Alerte>
        )}

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto">
          {loading ? <div className="grid min-h-56 place-items-center text-sm text-text-muted" role="status"><div><Spinner taille="zone" className="mx-auto mb-2" />Chargement des relances…</div></div> : visibleItems.length === 0 ? <EtatVide className="grid min-h-56 place-items-center rounded-md border border-dashed border-border bg-surface" titre="Aucune relance dans cette catégorie"><CheckCircle2 className="mx-auto mb-2 h-8 w-8 opacity-50" />Les prochaines échéances apparaîtront ici.</EtatVide> : <div className="space-y-2">{visibleItems.map((item) => {
            const busy = pendingId === item.id;
            const overdue = item.status === 'pending' && estEnRetard(item.due_date, new Date());
            return <Carte key={item.id} className="p-4" data-testid="follow-up-row">
              {editingId === item.id ? <div><div className="grid gap-3 sm:grid-cols-[180px_1fr]"><label className="text-sm font-semibold text-text">Nouvelle échéance<Input aria-label="Nouvelle échéance" error={Boolean(error)} aria-describedby={error ? "follow-ups-error" : undefined} type="date" value={editingDate} onChange={(event) => setEditingDate(event.target.value)} className="mt-1.5 font-normal" /></label><label className="text-sm font-semibold text-text">Note<Input aria-label="Note de relance" error={Boolean(error)} aria-describedby={error ? "follow-ups-error" : undefined} value={editingNote} onChange={(event) => setEditingNote(event.target.value)} className="mt-1.5 font-normal" /></label></div><div className="mt-3 flex flex-wrap justify-end gap-2"><Button type="button" variant="ghost" onClick={() => setEditingId(null)}>Annuler</Button><Button type="button" onClick={() => void saveEdit(item)} disabled={!editingDate || busy}>Enregistrer</Button></div></div> : deleteConfirmation === item.id ? <div className="text-sm text-error"><strong>Supprimer définitivement cette relance ?</strong><div className="mt-3 flex flex-wrap justify-end gap-2"><Button type="button" variant="secondary" onClick={() => setDeleteConfirmation(null)}>Annuler</Button><Button type="button" variant="danger" onClick={() => void confirmDelete(item.id)} disabled={busy}>Confirmer</Button></div></div> : <div className="flex flex-wrap items-start gap-3"><span className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md ${item.status === 'done' ? 'bg-[var(--color-success-tint)] text-success' : overdue ? 'bg-[var(--color-warning-tint)] text-warning' : 'bg-accent-tint text-accent'}`}>{item.status === 'done' ? <CheckCircle2 className="h-4 w-4" /> : <CalendarClock className="h-4 w-4" />}</span><div className="min-w-0 flex-1"><h3 className="truncate text-sm font-semibold text-text">{item.email_subject || 'Email sans objet'}</h3><p className="mt-0.5 text-sm text-text-muted">{item.contact_name || item.email_from || 'Expéditeur non disponible'}</p>{item.note && <p className="mt-2 text-sm leading-5 text-text-muted">{item.note}</p>}<div className={`mt-2 text-sm font-semibold ${overdue ? 'text-warning' : 'text-text-muted'}`}>{overdue ? 'En retard · ' : 'Échéance · '}{formatDueDate(item.due_date)}</div></div><div className="flex shrink-0 gap-1 max-[840px]:basis-full max-[840px]:justify-end"><Button type="button" variant="ghost" size="icon" aria-label={`Modifier ${item.email_subject || 'la relance'}`} onClick={() => { setError(null); setEditingId(item.id); setEditingDate(dateInputValue(item.due_date)); setEditingNote(item.note || ''); }}><Pencil className="h-[18px] w-[18px]" /></Button>{item.status === 'pending' ? <Button type="button" variant="ghost" size="icon" aria-label={`Terminer ${item.email_subject || 'la relance'}`} onClick={() => void mutate(item.id, () => updateFollowUp(item.id, { status: 'done' }))} disabled={busy} className="text-success hover:bg-[var(--color-success-tint)]"><CheckCircle2 className="h-[18px] w-[18px]" /></Button> : <Button type="button" variant="ghost" size="icon" aria-label={`Réouvrir ${item.email_subject || 'la relance'}`} onClick={() => void mutate(item.id, () => updateFollowUp(item.id, { status: 'pending' }))} disabled={busy}><RefreshCw className="h-[18px] w-[18px]" /></Button>}<Button type="button" variant="ghost" size="icon" aria-label={`Supprimer ${item.email_subject || 'la relance'}`} onClick={() => setDeleteConfirmation(item.id)} className="text-error hover:bg-[var(--color-error-tint)]"><Trash2 className="h-[18px] w-[18px]" /></Button></div></div>}
            </Carte>;
          })}</div>}
        </div>
      </div>
    </aside>
  );
}
