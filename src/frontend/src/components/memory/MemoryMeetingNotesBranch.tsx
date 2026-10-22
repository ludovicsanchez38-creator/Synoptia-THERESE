import { useEffect, useState } from 'react';
import { listMeetingEvents, createMeetingNote, type MeetingChoice } from '../../services/api/meetingNotes';
import { listContacts, type Contact } from '../../services/api/memory';
import { ActivityMemoryBranch } from './ActivityMemoryBranch';
import { useDemoMask } from '../../hooks/useDemoMask';
import { gesteBloqueEnDemo } from '../../lib/gesteEnDemo';
const classe = 'rounded-sm border border-border px-3 py-2 text-sm';
export function MemoryMeetingNotesBranch() {
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<MeetingChoice[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [query, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState('');
  const [contact, setContact] = useState('');
  const [contactOffset, setContactOffset] = useState(0);
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [revision, setRevision] = useState(0);
  const demo = useDemoMask();
  useEffect(() => {
    if (!open || demo.enabled) return;
    let actif = true; setLoading(true); setError('');
    Promise.all([listMeetingEvents(query, offset), listContacts(contactOffset, 200)])
      .then(([e, c]) => { if (actif) { setEvents(e); setContacts(c); } })
      .catch(() => { if (actif) { setEvents([]); setError('Impossible de lire les rendez-vous et contacts locaux. Réessaie.'); } })
      .finally(() => { if (actif) setLoading(false); });
    return () => { actif = false; };
  }, [open, demo.enabled, query, offset, contactOffset, revision]);
  useEffect(() => { setSelected(''); }, [query, offset]);
  async function enregistrer() {
    if (gesteBloqueEnDemo() || busy) return;
    const event = events.find(e => e.id === selected);
    if (!event || !description.trim()) return;
    setBusy(true); setError('');
    try {
      await createMeetingNote({ calendar_event_id: event.id, calendar_id: event.calendar_id,
        contact_id: contact || null, description });
      setOpen(false); setDescription(''); setRevision(r => r + 1);
    } catch { setError('La note n’a pas été enregistrée. Vérifie le rendez-vous et le caractère professionnel de la note.'); }
    finally { setBusy(false); }
  }
  return <section aria-label="Notes liées à tes rendez-vous" className="space-y-4">
    <button className={classe} disabled={demo.enabled} onClick={() => { if (!gesteBloqueEnDemo()) setOpen(true); }}>Ajouter une note de rendez-vous</button>
    {error && <p role="alert">{error} <button className={classe} onClick={() => setRevision(r => r + 1)}>Réessayer</button></p>}
    {open && !demo.enabled && <form className="space-y-3" onSubmit={e => { e.preventDefault(); void enregistrer(); }}>
      <label className="block">Rechercher un rendez-vous<input className={classe} value={query} onChange={e => { setQuery(e.target.value); setOffset(0); }} /></label>
      <label className="block">Rendez-vous<select className={classe} required value={selected} onChange={e => setSelected(e.target.value)}><option value="">Choisis le rendez-vous</option>{events.map(e => <option key={e.id} value={e.id}>{demo.maskText(e.summary)}{e.date ? ` · ${new Date(e.date).toLocaleDateString('fr-FR')}` : ''}</option>)}</select></label>
      {loading && <p role="status">Lecture des rendez-vous locaux…</p>}
      <div><button className={classe} type="button" disabled={!offset} onClick={() => setOffset(o => Math.max(0, o - 50))}>Rendez-vous précédents</button>{' '}<button className={classe} type="button" disabled={events.length < 50} onClick={() => setOffset(o => o + 50)}>Autres rendez-vous</button></div>
      <label className="block">Contact facultatif<select className={classe} value={contact} onChange={e => setContact(e.target.value)}><option value="">Sans contact</option>{contacts.map(c => <option key={c.id} value={c.id}>{demo.maskText([c.first_name, c.last_name].filter(Boolean).join(' ') || c.company || 'Contact')}</option>)}</select></label>
      {(contacts.length === 200 || contactOffset > 0) && <div>
        <button className={classe} type="button" disabled={!contactOffset} onClick={() => { setContact(''); setContactOffset(o => Math.max(0, o - 200)); }}>Contacts précédents</button>{' '}
        <button className={classe} type="button" disabled={contacts.length < 200} onClick={() => { setContact(''); setContactOffset(o => o + 200); }}>Contacts suivants</button>
      </div>}
      <label className="block">Ta note<textarea className={classe} required maxLength={1200} value={description} onChange={e => setDescription(e.target.value)} /></label>
      <p>Le dossier du rendez-vous est repris automatiquement. La note reste dans ta base chiffrée.</p>
      <button className={classe} disabled={busy || loading || !selected || !description.trim()}>Enregistrer la note</button>{' '}<button className={classe} type="button" disabled={busy} onClick={() => setOpen(false)}>Annuler</button>
    </form>}
    <ActivityMemoryBranch key={revision} notes />
  </section>;
}
