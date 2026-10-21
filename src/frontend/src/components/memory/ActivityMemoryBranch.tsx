import { useEffect, useRef, useState } from 'react';
import { listActivities, correctActivity, deleteActivity, type ActivityResponse } from '../../services/api/crm-extended';
import { useDemoMask } from '../../hooks/useDemoMask';
import { gesteBloqueEnDemo } from '../../lib/gesteEnDemo';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { getProject } from '../../services/api/memory';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

const classe = 'rounded-sm border border-border bg-surface px-3 py-2 text-sm text-text';
const ISSUES: Record<string, string> = { confirmee: 'Confirmée, issue non reçue', annulee: 'Annulée avant exécution',
  reussie: 'Réussie', echouee: 'Échouée', envoyee: 'Envoyée avec accusé', indeterminee: 'Issue indéterminée', annotation: 'Correction par toi' };
function issue(trace: ActivityResponse) {
  try { return ISSUES[JSON.parse(trace.extra_data || '{}').outcome] || ''; } catch { return ''; }
}
function Effacement({ onCancel, onConfirm }: { onCancel: () => void; onConfirm: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: true, onEscape: onCancel });
  return <div className="fixed inset-0 z-50 grid place-items-center bg-surface/90">
    <div ref={ref} role="alertdialog" aria-modal="true" aria-label="Effacer cette trace ?" className="max-w-md space-y-3 rounded-md border border-border bg-surface-elevated p-5">
      <p>Effacer cette trace ?</p><p>Une ancienne sauvegarde peut rétablir cette trace.</p>
      <button className={classe} data-dialog-autofocus onClick={onCancel}>Annuler</button>{' '}
      <button className={classe} onClick={onConfirm}>Effacer définitivement</button>
    </div>
  </div>;
}
export function ActivityMemoryBranch({ notes = false }: { notes?: boolean }) {
  const [items, setItems] = useState<ActivityResponse[]>([]);
  const [revision, setRevision] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [edit, setEdit] = useState<string | null>(null);
  const [text, setText] = useState('');
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const retour = useRef<HTMLButtonElement | null>(null);
  const demo = useDemoMask();
  const afficher = (value: string) => demo.enabled ? 'Contenu masqué en démonstration' : demo.maskText(value);
  useEffect(() => {
    let actif = true; setLoading(true); setError('');
    listActivities({ type: notes ? 'note' : 'agent_action', skip: offset, limit: 50 })
      .then(data => { if (actif) setItems(data); })
      .catch(() => { if (actif) { setItems([]); setError('Impossible de lire tes traces. Réessaie.'); } })
      .finally(() => { if (actif) setLoading(false); });
    return () => { actif = false; };
  }, [notes, offset, revision]);
  async function muter(action: () => Promise<unknown>) {
    if (gesteBloqueEnDemo()) return;
    setBusy(true); setError('');
    try { await action(); setEdit(null); setConfirmation(null); setRevision(r => r + 1); }
    catch { setError('La modification a échoué. Réessaie.'); }
    finally { setBusy(false); }
  }
  return <section aria-label={notes ? 'Tes notes de rendez-vous' : 'Ton journal'} className="space-y-3">
    <p>{notes ? 'Tes notes restent liées à leur rendez-vous.' : 'Les actions confirmées et leur issue sont conservées ici. Sans accusé, un envoi reste indéterminé.'}</p>
    {error && <p role="alert">{error} <button className={classe} onClick={() => setRevision(r => r + 1)}>Réessayer</button></p>}
    {loading ? <p role="status">Lecture de tes traces…</p> : !error && items.length === 0 ? <p>Rien de noté pour le moment.</p> : <ul className="space-y-3">
      {items.map(t => <li key={t.id} className="space-y-2 rounded-md border border-border p-3">
        <h3>{afficher(t.title)}</h3><p>{issue(t)}</p>
        <p className="text-sm text-text-muted">{new Date(t.created_at).toLocaleString('fr-FR')}</p>
        {t.conversation_id && <button className={classe} disabled={demo.enabled} onClick={() => {
          const chat = useChatStore.getState();
          if (!chat.conversations.some(c => c.id === t.conversation_id)) chat.setConversations([...chat.conversations,
            { id: t.conversation_id!, title: 'Échange source', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: true }]);
          chat.loadConversation(t.conversation_id!); useNavigationStore.getState().setView('chat');
        }}>Voir l’échange source</button>}
        {t.project_id && <button className={classe} disabled={demo.enabled} onClick={() => {
          void getProject(t.project_id!).then(p => usePanelStore.getState().openEditProject(p)).catch(() => setError('Dossier supprimé ou indisponible.'));
        }}>Voir le dossier lié</button>}
        {t.description && <p className="whitespace-pre-wrap">{afficher(t.description)}</p>}
        {t.statut === 'annulee' && <p>Trace annulée{t.remplace_id ? ' et remplacée par une correction ci-dessus.' : '.'}</p>}
        {t.statut !== 'annulee' && <button className={classe} disabled={demo.enabled || busy} onClick={() => { if (!gesteBloqueEnDemo()) { setEdit(t.id); setText(''); } }}>Corriger cette trace</button>}{' '}
        <button className={classe} disabled={demo.enabled || busy} onClick={e => { if (!gesteBloqueEnDemo()) { retour.current = e.currentTarget; setConfirmation(t.id); } }}>Effacer cette trace</button>
        {edit === t.id && !demo.enabled && <form onSubmit={e => { e.preventDefault(); void muter(() => correctActivity(t.id, text)); }}>
          <label>Ta correction<textarea required maxLength={1200} className={classe} autoFocus value={text} onChange={e => setText(e.target.value)} /></label>
          <p>Le reçu original reste visible ; ta correction le remplace sans le réécrire.</p>
          <button className={classe} disabled={busy} type="submit">Enregistrer la correction</button>{' '}
          <button className={classe} type="button" onClick={() => setEdit(null)}>Annuler</button>
        </form>}
      </li>)}
    </ul>}
    <div className="flex gap-2"><button className={classe} disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - 50))}>Précédentes</button><button className={classe} disabled={items.length < 50} onClick={() => setOffset(o => o + 50)}>Suivantes</button></div>
    {confirmation && <Effacement onCancel={() => { setConfirmation(null); requestAnimationFrame(() => retour.current?.focus()); }} onConfirm={() => { if (!busy) void muter(() => deleteActivity(confirmation)); }} />}
  </section>;
}
