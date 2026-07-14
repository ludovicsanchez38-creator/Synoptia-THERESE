import { useEffect, useState, type ReactNode } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Inbox,
  Loader2,
  Mail,
  RefreshCw,
  Save,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import type { EmailMessage, SendEmailRequest } from '../../services/api/email';
import {
  emailSenderLabel,
  formatEmailDate,
  selectInboxMessages,
} from './emailReadModels';
import type {
  EmailInboxData,
  EmailLength,
  EmailTone,
} from './usePrototypeEmailData';
import type { ReadResource } from './usePrototypeReadData';

function EmailStateShell({ children }: { children: ReactNode }) {
  return <div className="flex min-h-44 items-center justify-center px-5 py-8">{children}</div>;
}

function priorityLabel(message: EmailMessage): string | null {
  if (message.priority === 'high') return 'Prioritaire';
  if (message.priority === 'medium') return 'À examiner';
  return null;
}

export function EmailInboxCard({
  resource,
  onRetry,
  onOpenMessage,
  onOpenClassic,
}: {
  resource: ReadResource<EmailInboxData>;
  onRetry: () => void;
  onOpenMessage: (messageId: string) => void;
  onOpenClassic: () => void;
}) {
  const visibleMessages = resource.status === 'ready'
    ? selectInboxMessages(resource.data.messages, 6)
    : [];
  const unreadCount = resource.status === 'ready'
    ? resource.data.messages.filter((message) => !message.is_read && !message.is_draft).length
    : 0;

  return (
    <section
      aria-labelledby="email-inbox-title"
      className="overflow-hidden rounded-[16px] border border-border bg-surface shadow-[0_12px_28px_-22px_rgba(16,28,54,0.45)]"
      data-testid="email-inbox-card"
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[9px] border border-text bg-[var(--k4bg)] text-[var(--k4)]">
            <Mail className="h-4 w-4" />
          </span>
          <div>
            <h2 id="email-inbox-title" className="text-sm font-semibold text-text">Messages à consulter</h2>
            <div className="text-[11px] text-text-muted">
              {resource.status === 'ready' && resource.data.currentAccount
                ? `${unreadCount} non lu${unreadCount > 1 ? 's' : ''} · ${resource.data.currentAccount.email}`
                : 'Lecture de la boîte connectée'}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={onOpenClassic}
          className="rounded-[8px] border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text hover:bg-surface-2"
        >
          Email complet
        </button>
      </div>

      {resource.status === 'loading' ? (
        <EmailStateShell>
          <div className="flex items-center gap-2 text-sm text-text-muted" role="status">
            <Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" />
            Je consulte tes messages…
          </div>
        </EmailStateShell>
      ) : resource.status === 'error' ? (
        <EmailStateShell>
          <div className="max-w-sm text-center" data-testid="email-inbox-error">
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">Boîte email indisponible</p>
            <p className="mt-1 text-xs leading-5 text-text-muted">{resource.error}</p>
            <div className="mt-4 flex justify-center gap-2">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 rounded-[9px] border border-text bg-text px-3 py-2 text-xs font-semibold text-white"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Réessayer
              </button>
              <button type="button" onClick={onOpenClassic} className="rounded-[9px] border border-border px-3 py-2 text-xs font-semibold text-text">
                Ouvrir Email
              </button>
            </div>
          </div>
        </EmailStateShell>
      ) : !resource.data.currentAccount ? (
        <EmailStateShell>
          <div className="text-center" data-testid="email-no-account">
            <Inbox className="mx-auto h-6 w-6 text-text-muted" />
            <p className="mt-2 text-sm font-semibold text-text">Aucun compte email connecté</p>
            <p className="mt-1 text-xs text-text-muted">Configure Gmail ou IMAP dans la vue Email complète.</p>
            <button type="button" onClick={onOpenClassic} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">
              Configurer Email
            </button>
          </div>
        </EmailStateShell>
      ) : visibleMessages.length === 0 ? (
        <EmailStateShell>
          <div className="text-center" data-testid="email-inbox-empty">
            <CheckCircle2 className="mx-auto h-6 w-6 text-success" />
            <p className="mt-2 text-sm font-semibold text-text">Aucun message dans la boîte de réception</p>
            <p className="mt-1 text-xs text-text-muted">La source est connectée et ne renvoie aucun message.</p>
          </div>
        </EmailStateShell>
      ) : (
        <div className="divide-y divide-[#EDF1F7]">
          {visibleMessages.map((message) => {
            const priority = priorityLabel(message);
            return (
              <button
                key={message.id}
                type="button"
                onClick={() => onOpenMessage(message.id)}
                className="flex w-full items-start gap-3 px-4 py-3.5 text-left hover:bg-surface-2"
              >
                <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${message.is_read ? 'bg-[#C8D2E0]' : 'bg-[#7C3AED]'}`} />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className={`truncate text-sm text-text ${message.is_read ? 'font-medium' : 'font-bold'}`}>
                      {emailSenderLabel(message)}
                    </span>
                    {priority && (
                      <span className="rounded-full bg-[var(--k3bg)] px-2 py-0.5 text-[10px] font-semibold text-[var(--k3)]">{priority}</span>
                    )}
                  </span>
                  <span className="mt-0.5 block truncate text-xs font-semibold text-text">{message.subject || '(Sans objet)'}</span>
                  <span className="mt-0.5 block truncate text-xs text-text-muted">{message.snippet || 'Aucun aperçu disponible.'}</span>
                </span>
                <span className="shrink-0 text-[10px] text-text-muted">{formatEmailDate(message.date)}</span>
                <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-text-muted" />
              </button>
            );
          })}
        </div>
      )}

      {resource.status === 'ready' && resource.data.failedMessages > 0 && (
        <div className="border-t border-border bg-[var(--color-warning-tint)] px-4 py-2 text-[10px] text-warning">
          {resource.data.failedMessages} message{resource.data.failedMessages > 1 ? 's' : ''} non chargé{resource.data.failedMessages > 1 ? 's' : ''} par le fournisseur.
        </div>
      )}
    </section>
  );
}

export function EmailMessageCanvas({
  resource,
  onRetry,
  onGenerateDraft,
  onSaveDraft,
  onOpenClassic,
}: {
  resource: ReadResource<EmailMessage> | null;
  onRetry: () => void;
  onGenerateDraft: (messageId: string, tone: EmailTone, length: EmailLength) => Promise<string>;
  onSaveDraft: (request: SendEmailRequest) => Promise<{ id: string }>;
  onOpenClassic: () => void;
}) {
  const messageId = resource?.status === 'ready' ? resource.data.id : null;
  const [tone, setTone] = useState<EmailTone>('formal');
  const [length, setLength] = useState<EmailLength>('medium');
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [draft, setDraft] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmSave, setConfirmSave] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedDraftId, setSavedDraftId] = useState<string | null>(null);

  useEffect(() => {
    if (resource?.status !== 'ready') return;
    setRecipient(resource.data.from_email || '');
    setSubject(`Re: ${resource.data.subject || ''}`);
    setDraft('');
    setError(null);
    setConfirmSave(false);
    setSavedDraftId(null);
  }, [messageId, resource]);

  async function handleGenerate() {
    if (resource?.status !== 'ready') return;
    setGenerating(true);
    setError(null);
    setSavedDraftId(null);
    try {
      setDraft(await onGenerateDraft(resource.data.id, tone, length));
    } catch {
      setError('La génération du brouillon a échoué. Tu peux écrire la réponse manuellement.');
    } finally {
      setGenerating(false);
    }
  }

  function validateDraft(): string | null {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient.trim())) return 'Le destinataire doit être une adresse email valide.';
    if (!subject.trim()) return 'L’objet est obligatoire.';
    if (!draft.trim()) return 'Le brouillon est vide.';
    return null;
  }

  function requestSave() {
    const validationError = validateDraft();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setConfirmSave(true);
  }

  async function confirmDraftSave() {
    setSaving(true);
    setError(null);
    try {
      const result = await onSaveDraft({
        to: [recipient.trim()],
        subject: subject.trim(),
        body: draft,
        html: false,
      });
      setSavedDraftId(result.id);
      setConfirmSave(false);
    } catch {
      setError('Impossible d’enregistrer le brouillon chez le fournisseur email.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-5 py-4 pr-16">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-text-muted">
          <Mail className="h-3.5 w-3.5" />
          Email connecté
        </div>
        <h2 className="mt-2 text-xl font-bold tracking-[-0.02em] text-text">Lecture et brouillon</h2>
        <p className="mt-1 text-sm text-text-muted">Le message reste en lecture seule. Enregistrer un brouillon ne l’envoie pas.</p>
      </div>

      {!resource || resource.status === 'loading' ? (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-text-muted" role="status">
          <Loader2 className="h-4 w-4 animate-spin text-[var(--k4)]" />
          Chargement du message…
        </div>
      ) : resource.status === 'error' ? (
        <div className="flex flex-1 items-center justify-center px-6 text-center" data-testid="email-message-error">
          <div>
            <AlertCircle className="mx-auto h-5 w-5 text-warning" />
            <p className="mt-2 text-sm font-semibold text-text">{resource.error}</p>
            <button type="button" onClick={onRetry} className="mt-4 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white">
              Réessayer
            </button>
          </div>
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto p-5">
          <article className="rounded-[13px] border border-border bg-surface p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-[15px] font-bold text-text">{resource.data.subject || '(Sans objet)'}</h3>
                <p className="mt-1 text-xs text-text-muted">
                  {emailSenderLabel(resource.data)} · {formatEmailDate(resource.data.date)}
                </p>
              </div>
              {!resource.data.is_read && (
                <span className="rounded-full bg-[var(--k4bg)] px-2 py-1 text-[10px] font-semibold text-[var(--k4)]">Non lu</span>
              )}
            </div>
            <div className="mt-4 max-h-52 overflow-y-auto whitespace-pre-wrap border-t border-border pt-4 text-sm leading-6 text-text">
              {resource.data.body_plain || resource.data.snippet || 'Aucun contenu texte disponible.'}
            </div>
          </article>

          <section className="mt-4 rounded-[13px] border border-border bg-surface p-4" aria-labelledby="email-draft-title">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 id="email-draft-title" className="flex items-center gap-2 text-sm font-bold text-text">
                  <Sparkles className="h-4 w-4 text-[var(--k4)]" />
                  Brouillon de réponse
                </h3>
                <p className="mt-1 text-[11px] text-text-muted">Modifiable avant toute sauvegarde.</p>
              </div>
              <div className="flex gap-2">
                <select
                  aria-label="Ton du brouillon"
                  value={tone}
                  onChange={(event) => setTone(event.target.value as EmailTone)}
                  className="rounded-[8px] border border-border bg-surface-2 px-2 py-1.5 text-[11px] text-text"
                >
                  <option value="formal">Formel</option>
                  <option value="friendly">Amical</option>
                  <option value="neutral">Neutre</option>
                </select>
                <select
                  aria-label="Longueur du brouillon"
                  value={length}
                  onChange={(event) => setLength(event.target.value as EmailLength)}
                  className="rounded-[8px] border border-border bg-surface-2 px-2 py-1.5 text-[11px] text-text"
                >
                  <option value="short">Court</option>
                  <option value="medium">Moyen</option>
                  <option value="detailed">Détaillé</option>
                </select>
              </div>
            </div>

            <div className="mt-4 grid gap-2">
              <label className="grid grid-cols-[72px_1fr] items-center gap-2 text-xs text-text-muted">
                À
                <input
                  aria-label="Destinataire du brouillon"
                  value={recipient}
                  onChange={(event) => setRecipient(event.target.value)}
                  className="rounded-[8px] border border-border px-2.5 py-2 text-xs text-text outline-none focus:border-[var(--k4)]"
                />
              </label>
              <label className="grid grid-cols-[72px_1fr] items-center gap-2 text-xs text-text-muted">
                Objet
                <input
                  aria-label="Objet du brouillon"
                  value={subject}
                  onChange={(event) => setSubject(event.target.value)}
                  className="rounded-[8px] border border-border px-2.5 py-2 text-xs text-text outline-none focus:border-[var(--k4)]"
                />
              </label>
            </div>

            <textarea
              aria-label="Corps du brouillon"
              value={draft}
              onChange={(event) => {
                setDraft(event.target.value);
                setSavedDraftId(null);
              }}
              placeholder="Écris ta réponse ou génère une proposition…"
              className="mt-3 h-40 w-full resize-y rounded-[10px] border border-border p-3 text-sm leading-6 text-text outline-none focus:border-[var(--k4)]"
            />

            {error && <p className="mt-2 text-xs font-medium text-error" role="alert">{error}</p>}
            {savedDraftId && (
              <div className="mt-3 flex items-start gap-2 rounded-[10px] border border-success/40 bg-[var(--color-success-tint)] p-3 text-xs text-success" data-testid="email-draft-saved">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span><strong>Brouillon enregistré.</strong> Aucun message n’a été envoyé.</span>
              </div>
            )}

            {confirmSave && (
              <div className="mt-3 rounded-[10px] border border-accent-cyan/30 bg-accent-tint p-3" data-testid="email-draft-confirmation">
                <div className="flex items-start gap-2 text-xs text-accent">
                  <ShieldCheck className="h-4 w-4 shrink-0 text-accent" />
                  <div>
                    <strong>Confirmer l’enregistrement chez le fournisseur email</strong>
                    <p className="mt-1">Destinataire : {recipient}</p>
                    <p>Objet : {subject}</p>
                    <p className="mt-1 font-semibold">Cette action crée un brouillon. Elle n’envoie rien.</p>
                  </div>
                </div>
                <div className="mt-3 flex justify-end gap-2">
                  <button type="button" onClick={() => setConfirmSave(false)} className="rounded-[8px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">
                    Annuler
                  </button>
                  <button type="button" onClick={() => void confirmDraftSave()} disabled={saving} className="rounded-[8px] bg-[#047857] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60">
                    {saving ? 'Enregistrement…' : 'Confirmer le brouillon'}
                  </button>
                </div>
              </div>
            )}

            <div className="mt-3 flex flex-wrap justify-between gap-2">
              <button
                type="button"
                onClick={() => void handleGenerate()}
                disabled={generating}
                className="inline-flex items-center gap-1.5 rounded-[9px] border border-[var(--k4)] bg-surface px-3 py-2 text-xs font-semibold text-[var(--k4)] disabled:opacity-60"
              >
                {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                {generating ? 'Génération…' : 'Générer une proposition'}
              </button>
              <button
                type="button"
                onClick={requestSave}
                disabled={saving}
                className="inline-flex items-center gap-1.5 rounded-[9px] bg-text px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
              >
                <Save className="h-3.5 w-3.5" />
                Enregistrer comme brouillon
              </button>
            </div>
          </section>
        </div>
      )}

      <div className="border-t border-border bg-surface p-4">
        <button
          type="button"
          onClick={onOpenClassic}
          className="flex w-full items-center justify-center gap-2 rounded-[10px] border border-text bg-text px-4 py-3 text-sm font-semibold text-white"
        >
          <ExternalLink className="h-4 w-4" />
          Ouvrir Email complet
        </button>
      </div>
    </div>
  );
}
