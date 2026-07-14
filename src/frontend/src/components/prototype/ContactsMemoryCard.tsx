import { useMemo, useState } from 'react';
import {
  AlertCircle,
  ChevronRight,
  ExternalLink,
  Loader2,
  Mail,
  RefreshCw,
  Search,
  Users,
} from 'lucide-react';
import type { Contact } from '../../services/api/memory';
import { contactMatchesQuery } from '../../stores/contactsStore';
import {
  contactDisplayName,
  contactInitials,
  selectRecentContacts,
} from './prototypeReadModels';
import type { ReadResource } from './usePrototypeReadData';

const EMPTY_CONTACTS: Contact[] = [];

function ContactAvatar({ contact, className = '' }: { contact: Contact; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`grid shrink-0 place-items-center rounded-[10px] border border-accent-cyan/30 bg-accent-tint font-bold text-accent ${className}`}
    >
      {contactInitials(contact)}
    </span>
  );
}

function EmptyContacts({ onOpenClassic }: { onOpenClassic: () => void }) {
  return (
    <div className="flex min-h-44 items-center justify-center px-5 py-8 text-center" data-testid="contacts-memory-empty">
      <div>
        <Users className="mx-auto h-6 w-6 text-text-muted" />
        <p className="mt-2 text-sm font-semibold text-text">Aucun contact enregistré</p>
        <p className="mt-1 text-xs text-text-muted">La mémoire est prête, mais elle ne contient encore aucune personne.</p>
        <button
          type="button"
          onClick={onOpenClassic}
          className="mt-4 rounded-[9px] border border-text bg-text px-3 py-2 text-xs font-semibold text-white"
        >
          Ouvrir la mémoire
        </button>
      </div>
    </div>
  );
}

export function ContactsMemoryCard({
  resource,
  onRetry,
  onOpenContact,
  onOpenClassic,
}: {
  resource: ReadResource<Contact[]>;
  onRetry: () => void;
  onOpenContact: (contactId: string) => void;
  onOpenClassic: () => void;
}) {
  const recentContacts = resource.status === 'ready' ? selectRecentContacts(resource.data, 4) : [];

  return (
    <section
      aria-labelledby="contacts-memory-title"
      className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]"
      data-testid="contacts-memory-card"
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[9px] border border-text bg-[var(--k4bg)] text-[var(--k4)]">
            <Users className="h-4 w-4" />
          </span>
          <div>
            <h2 id="contacts-memory-title" className="text-sm font-semibold text-text">Contacts et mémoire</h2>
            <div className="text-[11px] text-text-muted">
              {resource.status === 'ready'
                ? `${resource.data.length} contact${resource.data.length > 1 ? 's' : ''} dans la mémoire locale`
                : 'Lecture de la mémoire locale'}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={onOpenClassic}
          className="rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text hover:bg-surface-2"
        >
          Vue complète
        </button>
      </div>

      {resource.status === 'loading' ? (
        <div className="flex min-h-44 items-center justify-center gap-2 px-5 py-8 text-sm text-text-muted" role="status">
          <Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" />
          Je consulte ta mémoire…
        </div>
      ) : resource.status === 'error' ? (
        <div className="flex min-h-44 items-center justify-center px-5 py-8 text-center" data-testid="contacts-memory-error">
          <div>
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">Mémoire indisponible</p>
            <p className="mt-1 text-xs text-text-muted">{resource.error}</p>
            <button
              type="button"
              onClick={onRetry}
              className="mt-4 inline-flex items-center gap-1.5 rounded-[9px] border border-text bg-text px-3 py-2 text-xs font-semibold text-white"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Réessayer
            </button>
          </div>
        </div>
      ) : recentContacts.length === 0 ? (
        <EmptyContacts onOpenClassic={onOpenClassic} />
      ) : (
        <div className="divide-y divide-[#EDF1F7]">
          {recentContacts.map((contact) => (
            <button
              key={contact.id}
              type="button"
              onClick={() => onOpenContact(contact.id)}
              className="flex w-full items-center gap-3 px-4 py-3.5 text-left hover:bg-surface-2"
            >
              <ContactAvatar contact={contact} className="h-9 w-9 text-[11px]" />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold text-text">{contactDisplayName(contact)}</span>
                <span className="mt-0.5 block truncate text-xs text-text-muted">
                  {[contact.company, contact.email, contact.stage].filter(Boolean).join(' · ') || 'Fiche locale'}
                </span>
              </span>
              <ChevronRight className="h-4 w-4 text-text-muted" />
            </button>
          ))}
        </div>
      )}

      {resource.status === 'ready' && resource.data.length > recentContacts.length && (
        <button
          type="button"
          onClick={onOpenClassic}
          className="w-full border-t border-border bg-surface-2 px-4 py-3 text-center text-xs font-semibold text-[var(--k4)] hover:bg-[#F3F0FB]"
        >
          Voir les {resource.data.length - recentContacts.length} autres contacts
        </button>
      )}
    </section>
  );
}

export function ContactsMemoryCanvas({
  resource,
  selectedContactId,
  onSelectContact,
  onRetry,
  onOpenClassic,
}: {
  resource: ReadResource<Contact[]>;
  selectedContactId: string | null;
  onSelectContact: (contactId: string) => void;
  onRetry: () => void;
  onOpenClassic: () => void;
}) {
  const [query, setQuery] = useState('');
  const contacts = resource.status === 'ready' ? resource.data : EMPTY_CONTACTS;
  const filteredContacts = useMemo(() => {
    const normalized = query.trim();
    return normalized ? contacts.filter((contact) => contactMatchesQuery(contact, normalized)) : contacts;
  }, [contacts, query]);
  const selectedContact = filteredContacts.find((contact) => contact.id === selectedContactId) ?? filteredContacts[0] ?? null;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted">
          <Users className="h-3.5 w-3.5" />
          Mémoire locale
        </div>
        <h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">Contacts et contexte</h2>
        <p className="mt-1 text-sm text-text-muted">Lecture seule des fiches réellement enregistrées dans Thérèse.</p>
      </div>

      {resource.status === 'loading' ? (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-text-muted">
          <Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" />
          Chargement de la mémoire…
        </div>
      ) : resource.status === 'error' ? (
        <div className="flex flex-1 items-center justify-center px-6 text-center">
          <div>
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">{resource.error}</p>
            <button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">
              Réessayer
            </button>
          </div>
        </div>
      ) : contacts.length === 0 ? (
        <EmptyContacts onOpenClassic={onOpenClassic} />
      ) : (
        <div className="grid min-h-0 flex-1 grid-cols-[210px_minmax(0,1fr)]">
          <aside className="min-h-0 border-r border-border bg-surface p-3">
            <div className="relative mb-3">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                aria-label="Rechercher un contact"
                placeholder="Rechercher…"
                className="w-full rounded-[9px] border border-border bg-surface-2 py-2 pl-8 pr-2 text-xs text-text outline-none focus:border-[var(--k4)]"
              />
            </div>
            <div className="h-[calc(100%-46px)] space-y-1 overflow-y-auto">
              {filteredContacts.map((contact) => (
                <button
                  key={contact.id}
                  type="button"
                  onClick={() => onSelectContact(contact.id)}
                  className={`flex w-full items-center gap-2 rounded-[9px] px-2 py-2 text-left ${
                    selectedContact?.id === contact.id ? 'bg-[var(--k4bg)]' : 'hover:bg-surface-2'
                  }`}
                >
                  <ContactAvatar contact={contact} className="h-7 w-7 text-[9px]" />
                  <span className="min-w-0 flex-1 truncate text-xs font-semibold text-text">{contactDisplayName(contact)}</span>
                </button>
              ))}
              {filteredContacts.length === 0 && (
                <p className="px-2 py-4 text-center text-xs text-text-muted">Aucun contact trouvé.</p>
              )}
            </div>
          </aside>

          <div className="min-h-0 overflow-y-auto p-5">
            {selectedContact && (
              <div>
                <div className="flex items-start gap-3">
                  <ContactAvatar contact={selectedContact} className="h-12 w-12 text-sm" />
                  <div className="min-w-0 flex-1">
                    <h3 className="text-lg font-bold text-text">{contactDisplayName(selectedContact)}</h3>
                    <p className="mt-0.5 text-xs text-text-muted">
                      {[selectedContact.company, selectedContact.stage].filter(Boolean).join(' · ') || 'Contact local'}
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid gap-2">
                  {selectedContact.email && (
                    <div className="flex items-center gap-2 rounded-[10px] border border-border bg-surface px-3 py-2.5 text-xs text-text">
                      <Mail className="h-3.5 w-3.5 text-[var(--k4)]" />
                      {selectedContact.email}
                    </div>
                  )}
                  {selectedContact.phone && (
                    <div className="rounded-[10px] border border-border bg-surface px-3 py-2.5 text-xs text-text">
                      {selectedContact.phone}
                    </div>
                  )}
                </div>

                <div className="mt-5">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-text-muted">Notes mémorisées</div>
                  <div className="mt-2 min-h-24 whitespace-pre-wrap rounded-[12px] border border-border bg-surface p-3 text-sm leading-6 text-text">
                    {selectedContact.notes || 'Aucune note enregistrée pour ce contact.'}
                  </div>
                </div>

                {selectedContact.tags && selectedContact.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {selectedContact.tags.map((tag) => (
                      <span key={tag} className="rounded-full bg-[var(--k4bg)] px-2 py-1 text-[10px] font-semibold text-[var(--k4)]">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="border-t border-border bg-surface p-4">
        <button
          type="button"
          onClick={onOpenClassic}
          className="flex w-full items-center justify-center gap-2 rounded-[10px] border border-text bg-text px-4 py-3 text-sm font-semibold text-white"
        >
          <ExternalLink className="h-4 w-4" />
          Ouvrir la mémoire complète
        </button>
      </div>
    </div>
  );
}
