import { useEffect, useState } from 'react';
import { getMemoryCard, listenMemoryChanges } from '../../services/api/memoryCards';
import { openMemoryCard } from '../../stores/agentMemoryStore';
import { useDemoMask } from '../../hooks/useDemoMask';

/** Le titre n'entre ni dans le reçu durable ni dans un cache persistant. */
export function MemoryReceipt({ id, used = false }: { id: string; used?: boolean }) {
  const [titre, setTitre] = useState<string | null>(null);
  const [etat, setEtat] = useState<'loading' | 'ready' | 'deleted' | 'error'>('loading');
  const [revision, setRevision] = useState(0);
  const demo = useDemoMask();
  useEffect(() => listenMemoryChanges(() => { setTitre(null); setRevision(r => r + 1); }), []);
  useEffect(() => {
    let actif = true;
    getMemoryCard(id).then(f => { if (actif) { setTitre(f.title); setEtat('ready'); } })
      .catch((e: { status?: number }) => { if (actif) { setTitre(null); setEtat(e.status === 404 ? 'deleted' : 'error'); } });
    return () => { actif = false; };
  }, [id, revision]);
  if (etat === 'deleted') return <span className="text-sm text-text-muted">Fiche effacée</span>;
  if (etat !== 'ready' || !titre) return <span className="text-sm text-text-muted">{etat === 'error' ? 'Fiche indisponible' : 'Lecture de la fiche…'}</span>;
  return <button type="button" className="text-sm text-accent-cyan-ink underline" onClick={() => openMemoryCard(id)}>
    {used ? 'Fiche utilisée : ' : 'Noté : '}{demo.enabled ? 'Fiche de démonstration' : demo.maskText(titre)}
  </button>;
}
