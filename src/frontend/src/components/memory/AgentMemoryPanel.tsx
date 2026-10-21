import { useCallback, useEffect, useRef, useState } from 'react';
import { getMemoryCards, getMemoryCard, getMemoryScopes, patchMemoryCard, deleteMemoryCard, releaseMemoryCard,
  listenMemoryChanges, notifyMemoryChange, type MemoryCard } from '../../services/api/memoryCards';
import { useAgentMemoryStore } from '../../stores/agentMemoryStore';
import { useChatStore } from '../../stores/chatStore';
import { useDemoMask } from '../../hooks/useDemoMask';
import { gesteBloqueEnDemo } from '../../lib/gesteEnDemo';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

import { MemoryMeetingNotesBranch } from './MemoryMeetingNotesBranch';
import { MemoryDraftsBranch } from './MemoryDraftsBranch';
import { MemoryProfileBranch } from './MemoryProfileBranch';
import { ActivityMemoryBranch } from './ActivityMemoryBranch';

const TYPES = { preference: 'Préférences', fait: 'Faits clients et dossiers', decision: 'Décisions et raisons', correction: 'Corrections' };
const BRANCHES = ['Profil et consignes', 'Fiches et index', 'Journal des actions confirmées et envois', 'Brouillons en cours', 'Notes de rendez-vous'];
const PAGE = 25;
const classe = 'rounded-sm border border-border bg-surface px-3 py-2 text-sm text-text';

function Confirmation({ titre, onConfirm, onCancel, busy }: { titre: string; onConfirm: () => void; onCancel: () => void; busy: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: true });
  return <div className="fixed inset-0 z-50 grid place-items-center bg-surface/90" onKeyDown={e => { if (e.key === 'Escape' && !busy) { e.stopPropagation(); onCancel(); } }}>
    <div ref={ref} role="alertdialog" aria-modal="true" aria-labelledby="memory-confirm-title" className="max-w-md rounded-md border border-border bg-surface-elevated p-5">
      <h3 id="memory-confirm-title">{titre}</h3>
      <p className="my-3 text-sm">La fiche sera retirée du contexte des prochains échanges. La conversation source garde son propre effacement. Une ancienne sauvegarde peut rétablir la fiche.</p>
      <button type="button" className={classe} data-dialog-autofocus onClick={onCancel} disabled={busy}>Annuler</button>{' '}
      <button type="button" className={classe} onClick={onConfirm} disabled={busy}>Effacer définitivement</button>
    </div>
  </div>;
}

export function AgentMemoryPanel() {
  const [branch, setBranch] = useState(1);
  const selectedId = useAgentMemoryStore(s => s.selectedId);
  const [items, setItems] = useState<MemoryCard[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('');
  const [state, setState] = useState('active');
  const [scope, setScope] = useState('');
  const [scopes, setScopes] = useState<Array<{ id: string; name: string }>>([]);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [card, setCard] = useState<MemoryCard | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ title: '', content: '', reason: '' });
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const retourFocus = useRef<HTMLButtonElement>(null);
  const demo = useDemoMask();
  const afficher = (texte: string) => demo.enabled ? 'Contenu masqué en démonstration' : demo.maskText(texte);
  useEffect(() => listenMemoryChanges(() => { setCard(null); setRevision(r => r + 1); }), []);
  useEffect(() => { getMemoryScopes().then(setScopes).catch(() => {}); }, []);
  useEffect(() => {
    let actif = true;
    setLoading(true); setError('');
    getMemoryCards({ query, state, offset, limit: PAGE, ...(kind ? { kind } : {}),
      ...(scope === 'global' ? { scope } : scope ? { scope_id: scope } : {}) })
      .then(page => { if (actif) { setItems(page.items); setTotal(page.total); } })
      .catch(() => { if (actif) { setItems([]); setError('Impossible de lire tes fiches. Réessaie.'); } })
      .finally(() => { if (actif) setLoading(false); });
    return () => { actif = false; };
  }, [query, kind, state, scope, offset, revision]);
  useEffect(() => {
    let actif = true;
    setEditing(false);
    if (!selectedId) { setCard(null); return; }
    getMemoryCard(selectedId).then(f => { if (actif) setCard(f); })
      .catch(() => { if (actif) { setCard(null); setError('Fiche effacée ou indisponible.'); } });
    return () => { actif = false; };
  }, [selectedId, revision]);

  const muter = useCallback(async (action: () => Promise<unknown>, efface = false) => {
    if (gesteBloqueEnDemo()) return;
    setBusy(true); setError('');
    try {
      const resultat = await action();
      setEditing(false); setConfirm(false);
      if (efface) { setCard(null); useAgentMemoryStore.setState({ selectedId: null }); }
      else if (resultat && typeof resultat === 'object' && 'id' in resultat) setCard(resultat as MemoryCard);
      notifyMemoryChange(); setRevision(r => r + 1);
    } catch (e) { setError(e instanceof Error ? e.message : 'La modification a échoué. Recharge la fiche avant de réessayer.'); }
    finally { setBusy(false); }
  }, []);
  const fermerConfirmation = () => { setConfirm(false); requestAnimationFrame(() => retourFocus.current?.focus()); };

  function ouvrirSource(f: MemoryCard) {
    if (!f.conversation_id || !f.message_id) return;
    const chat = useChatStore.getState();
    if (!chat.conversations.some(c => c.id === f.conversation_id)) chat.setConversations([...chat.conversations,
      { id: f.conversation_id, title: 'Échange source', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: true }]);
    useAgentMemoryStore.setState({ sourceMessageId: f.message_id, sourceConversationId: f.conversation_id });
    useChatStore.getState().loadConversation(f.conversation_id);
  }

  return <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-auto p-4 lg:flex-row">
    <nav aria-label="Arborescence de Mémoire" className="flex shrink-0 flex-col gap-2 lg:w-56">
      {BRANCHES.map((branche, i) => <button key={branche} type="button" className={classe} onClick={() => setBranch(i)} aria-current={i === branch ? 'page' : undefined}>
        {branche}
      </button>)}
    </nav>
    <div className="min-w-0 flex-1 space-y-4">
      {branch === 0 ? <MemoryProfileBranch /> : branch === 2 ? <ActivityMemoryBranch /> : branch === 3 ? <MemoryDraftsBranch /> : branch === 4 ? <MemoryMeetingNotesBranch /> : <>
      <p className="text-sm text-text-muted">Thérèse écrit tes fiches ; tu peux les corriger ou les effacer. Elles restent dans ta base chiffrée. Dans le chat, tes fiches mémoire utiles sont envoyées avec chaque échange où la mémoire est activée, avec ton accord pour un service en ligne.</p>
      <div className="flex flex-wrap gap-2">
        <label>Rechercher<input className={classe} value={query} onChange={e => { setQuery(e.target.value); setOffset(0); }} /></label>
        <label>Type<select className={classe} value={kind} onChange={e => { setKind(e.target.value); setOffset(0); }}><option value="">Tous les types</option>{Object.entries(TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label>État<select className={classe} value={state} onChange={e => { setState(e.target.value); setOffset(0); }}><option value="active">Actives</option><option value="archivee">Archivées</option></select></label>
        <label>Portée<select className={classe} value={scope} onChange={e => { setScope(e.target.value); setOffset(0); }}><option value="">Toutes les portées</option><option value="global">Général</option>{scopes.map(p => <option key={p.id} value={p.id}>{afficher(p.name)}</option>)}</select></label>
      </div>
      {error && <div role="alert">{error} <button className={classe} onClick={() => setRevision(r => r + 1)}>Réessayer</button></div>}
      {loading ? <p role="status">Lecture de tes fiches…</p> : items.length === 0 && !error ? <p>{query || kind || scope || state !== 'active' ? 'Aucune fiche ne correspond à ta recherche.' : 'Rien de noté pour le moment. Thérèse retiendra tes façons de travailler au fil de tes échanges.'}</p> : <ul className="space-y-2">
        {items.map(f => <li key={f.id} className="rounded-md border border-border p-3">
          <button type="button" className="font-semibold text-accent-cyan-ink underline" onClick={() => useAgentMemoryStore.setState({ selectedId: f.id })}>{demo.enabled ? 'Fiche de démonstration' : afficher(f.title)}</button>
          <p className="text-sm text-text-muted">{TYPES[f.kind]} · {afficher(f.scope_name)} · {new Date(f.updated_at).toLocaleDateString('fr-FR')}</p>
        </li>)}
      </ul>}
      {total > PAGE && <div className="flex gap-2"><button type="button" className={classe} disabled={offset === 0} onClick={() => setOffset(p => Math.max(0, p - PAGE))}>Précédentes</button><span>{offset + 1}–{Math.min(offset + PAGE, total)} sur {total}</span><button type="button" className={classe} disabled={offset + PAGE >= total} onClick={() => setOffset(p => p + PAGE)}>Suivantes</button></div>}
      {card && <article aria-label="Détail de la fiche" className="space-y-3 rounded-md border border-border p-4">
        <h3 className="font-semibold">{demo.enabled ? 'Fiche de démonstration' : afficher(card.title)}</h3>
        <p>{afficher(card.content)}</p>{card.reason && <p>{afficher(card.reason)}</p>}
        <p className="text-sm text-text-muted">{card.author === 'therese' ? 'Écrite par Thérèse' : 'Saisie par toi'} · {new Date(card.created_at).toLocaleString('fr-FR')} · {afficher(card.scope_name)}{card.contact_name && ` · ${afficher(card.contact_name)}`}</p>
        {card.last_author === 'utilisateur' && <p>Corrigée par toi</p>}
        <p className="text-sm">Mise à jour le {new Date(card.updated_at).toLocaleString('fr-FR')}</p>
        {card.source_deleted ? <p>Source supprimée</p> : card.conversation_id && card.message_id ? <button type="button" className={classe} onClick={() => ouvrirSource(card)}>Voir l’échange source</button> : <p>Sans source de conversation</p>}
        {card.protected && <p>Protégée par ta correction. Thérèse ne peut pas la réécrire.</p>}
        <div className="flex flex-wrap gap-2">
          <button type="button" className={classe} disabled={busy || demo.enabled} onClick={() => { if (gesteBloqueEnDemo()) return; setForm({ title: card.title, content: card.content, reason: card.reason }); setEditing(true); }}>Modifier</button>
          <button type="button" className={classe} disabled={busy || demo.enabled} onClick={() => void muter(() => patchMemoryCard(card.id, { version: card.version, state: card.state === 'active' ? 'archivee' : 'active' }))}>{card.state === 'active' ? 'Archiver' : 'Réactiver'}</button>
          {card.protected && <button type="button" className={classe} disabled={busy || demo.enabled} onClick={() => void muter(() => releaseMemoryCard(card.id, card.version))}>Rendre la main à Thérèse</button>}
          <button ref={retourFocus} type="button" className={classe} disabled={busy || demo.enabled} onClick={() => { if (!gesteBloqueEnDemo()) setConfirm(true); }}>Effacer</button>
        </div>
        {editing && !demo.enabled && <form className="space-y-2" onSubmit={e => { e.preventDefault(); void muter(() => patchMemoryCard(card.id, { ...form, version: card.version })); }}>
          <label className="block">Titre<input autoFocus required maxLength={120} className={classe} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></label>
          <label className="block">Contenu<textarea required maxLength={1200} className={classe} value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} /></label>
          <label className="block">Raison<textarea required={card.kind === 'decision'} maxLength={600} className={classe} value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })} /></label>
          <button type="submit" className={classe} disabled={busy}>Enregistrer</button>{' '}<button type="button" className={classe} disabled={busy} onClick={() => setEditing(false)}>Annuler</button>
        </form>}
        {confirm && <Confirmation titre="Effacer cette fiche ?" busy={busy} onCancel={fermerConfirmation} onConfirm={() => void muter(() => deleteMemoryCard(card.id, card.version), true)} />}
      </article>}
      </>}
    </div>
  </div>;
}
