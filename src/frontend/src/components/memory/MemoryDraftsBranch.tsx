import { useEffect, useState } from 'react';
import { listMemoryDrafts, getLocalEmailDraft, type MemoryDraft } from '../../services/api/memoryDrafts';
import { getInvoice, type Invoice } from '../../services/api/invoices';
import { InvoiceForm } from '../invoices/InvoiceForm';
import { DocumentWorkspace } from '../documents/DocumentWorkspace';
import { EmailCompose } from '../email/EmailCompose';
import { useEmailStore } from '../../stores/emailStore';
import { useDemoMask } from '../../hooks/useDemoMask';
import { gesteBloqueEnDemo } from '../../lib/gesteEnDemo';
const classe = 'rounded-sm border border-border px-3 py-2 text-sm';
const LIBELLES = { devis: 'Devis', facture: 'Facture', avoir: 'Avoir', document: 'Document', email: 'Mail sauvegardé' };
export function MemoryDraftsBranch() {
  const [items, setItems] = useState<MemoryDraft[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [mail, setMail] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);
  const composing = useEmailStore(s => s.isComposing);
  const temporary = useEmailStore(s => Boolean(s.draftBody || s.draftSubject || s.draftRecipients.length || s.isComposing));
  const demo = useDemoMask();
  useEffect(() => {
    let actif = true; setLoading(true); setError('');
    listMemoryDrafts(offset).then(page => { if (actif) { setItems(page.items); setTotal(page.total); } })
      .catch(() => { if (actif) { setItems([]); setError('Impossible de lire tes brouillons. Réessaie.'); } })
      .finally(() => { if (actif) setLoading(false); });
    return () => { actif = false; };
  }, [offset, revision]);
  async function ouvrir(item: MemoryDraft) {
    if (gesteBloqueEnDemo() || opening) return;
    setOpening(true); setError('');
    try {
      if (item.kind === 'document') setDocumentId(item.id);
      else if (item.kind === 'email') {
        if (temporary) return;
        const d = await getLocalEmailDraft(item.id);
        if (gesteBloqueEnDemo()) return;
        const store = useEmailStore.getState();
        // Une saisie apparue pendant la lecture n'est jamais écrasée.
        if (store.isComposing || store.draftBody || store.draftSubject || store.draftRecipients.length) return;
        store.setCurrentAccount(d.account_id);
        store.startComposing(d.to_emails, d.subject, d.body_plain || d.body_html || '');
        store.setDraftCc(d.cc_emails); store.setDraftBcc(d.bcc_emails); store.setDraftIsHtml(!d.body_plain && Boolean(d.body_html));
        useEmailStore.setState({ editingDraftId: d.id });
        setMail(d.id);
      } else {
        const piece = await getInvoice(item.id);
        if (piece.status !== 'draft') throw new Error('Ce brouillon a déjà changé de statut.');
        setInvoice(piece);
      }
    } catch { setError('Ce brouillon a changé ou ne peut pas être ouvert. Recharge la liste.'); }
    finally { setOpening(false); }
  }
  if (!demo.enabled && documentId) return <DocumentWorkspace documentId={documentId} onBack={() => { setDocumentId(null); setRevision(r => r + 1); }} />;
  return <section aria-label="Tes brouillons en cours" className="space-y-3">
    <p>Devis, factures, documents en cours et mails déjà sauvegardés. Cette liste ne déclenche aucune sauvegarde.</p>
    {temporary && <div><button className={classe} disabled={demo.enabled} onClick={() => { if (!gesteBloqueEnDemo()) { useEmailStore.getState().setIsComposing(true); setMail('temporaire'); } }}>En cours de saisie</button><p>Ce composeur reste temporaire jusqu’à ta sauvegarde. Termine ta saisie avant d’ouvrir un autre mail.</p></div>}
    {error && <p role="alert">{error} <button className={classe} onClick={() => setRevision(r => r + 1)}>Réessayer</button></p>}
    {loading ? <p role="status">Lecture de tes brouillons…</p> : !error && !items.length ? <p>Aucun brouillon sauvegardé pour le moment.</p> : <ul className="space-y-2">{items.map(d => <li key={`${d.kind}-${d.id}`} className="rounded-md border border-border p-3">
      <button className={classe} disabled={demo.enabled || opening || (d.kind === 'email' && temporary)} onClick={() => void ouvrir(d)}>{demo.enabled ? 'Brouillon masqué en démonstration' : demo.maskText(d.title)}</button>
      <p className="text-sm text-text-muted">{LIBELLES[d.kind]} · {d.kind === 'document' ? 'En cours' : 'Brouillon sauvegardé'}</p>
    </li>)}</ul>}
    {total > 50 && <div><button className={classe} disabled={!offset} onClick={() => setOffset(o => Math.max(0, o - 50))}>Précédents</button>{' '}<button className={classe} disabled={offset + 50 >= total} onClick={() => setOffset(o => o + 50)}>Suivants</button></div>}
    {invoice && !demo.enabled && <InvoiceForm invoice={invoice} onClose={() => setInvoice(null)} onSave={() => { setInvoice(null); setRevision(r => r + 1); }} />}
    {mail && composing && !demo.enabled && <EmailCompose draftId={useEmailStore.getState().editingDraftId || undefined} />}
  </section>;
}
