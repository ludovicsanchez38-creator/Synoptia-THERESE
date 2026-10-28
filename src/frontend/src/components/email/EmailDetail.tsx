/**
 * THÉRÈSE v2 - Email Detail
 *
 * Detailed view of an email message.
 * Phase 1 Frontend - Email
 */

import { useState, useEffect } from 'react';
import {
  Reply,
  ReplyAll,
  Forward,
  Star,
  Trash2,
  Mail,
  ChevronLeft,
  Sparkles,
  Bell,
  CalendarClock,
} from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';
import { ResponseGeneratorModal } from './ResponseGeneratorModal';
import { EmailPriorityBadge } from './EmailPriorityBadge';
import { sanitizeEmailHtml } from '../../lib/sanitizeEmailHtml';
import { useExternalActionConfirmation } from '../app/useExternalActionConfirmation';
import { Spinner } from '../ui/Spinner';
import { texteDuCorps } from '../../lib/texteDuCorpsEmail';
import { Alerte } from '../ui/Alerte';
import { EtatVide } from '../ui/EtatVide';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';

interface EmailDetailProps {
  accountId: string;
  messageId: string;
}


export function EmailDetail({ accountId, messageId }: EmailDetailProps) {
  const requestExternalAction = useExternalActionConfirmation();
  const { messages, accounts = [], setCurrentMessage, updateMessage, removeMessage, startComposing, setNeedsReauth } = useEmailStore();
  const [_loading, _setLoading] = useState(false);
  const [bodyLoading, setBodyLoading] = useState(false);
  const [bodyError, setBodyError] = useState(false);
  // BUG-151 : opt-in PAR MESSAGE pour charger les images distantes (pixels de
  // traçage) - jamais persisté. F3 revue : l'état est DÉRIVÉ (un reset en
  // useEffect s'exécutait APRÈS le commit DOM : le mail B s'affichait un
  // rendu avec images avant le reset - pixel déjà parti). Clé COMPOSITE
  // compte+message : les UID IMAP sont locaux à un compte, deux comptes
  // peuvent porter le même messageId.
  const [imagesAllowedFor, setImagesAllowedFor] = useState<string | null>(null);
  const showRemoteImages = imagesAllowedFor === `${accountId}:${messageId}`;
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [trashError, setTrashError] = useState<string | null>(null);
  const [showFollowUpForm, setShowFollowUpForm] = useState(false);
  const [followUpDate, setFollowUpDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() + 2);
    return date.toISOString().slice(0, 10);
  });
  const [followUpNote, setFollowUpNote] = useState('');
  const [followUpSaving, setFollowUpSaving] = useState(false);
  const [followUpFeedback, setFollowUpFeedback] = useState<string | null>(null);

  const message = messages.find((m) => m.id === messageId);

  // Mark as read when opened
  useEffect(() => {
    if (message && !message.is_read) {
      markAsRead();
    }
  }, [messageId]);

  // BUG-102 : la liste ne charge que les métadonnées (snippet), pas le corps.
  // On récupère le message complet à l'ouverture si le corps est absent, sinon
  // le mail s'affiche vide et la réponse ne peut rien citer de l'original.
  useEffect(() => {
    if (!message) return;
    if ((message.body_html || message.body_plain) && message.reply_to_emails != null) return;
    let cancelled = false;
    setBodyLoading(true);
    setBodyError(false);
    api
      .getEmailMessage(accountId, messageId)
      .then((full) => {
        if (cancelled) return;
        updateMessage(messageId, {
          body_html: full.body_html,
          body_plain: full.body_plain,
          snippet: full.snippet ?? message.snippet,
          reply_to_emails: full.reply_to_emails ?? [],
          cc_emails: full.cc_emails ?? message.cc_emails,
        });
      })
      .catch((err) => {
        console.error('Failed to load full email body:', err);
        if (!cancelled) setBodyError(true);
      })
      .finally(() => {
        if (!cancelled) setBodyLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messageId, accountId]);

  async function markAsRead() {
    try {
      await api.modifyEmailMessage(accountId, messageId, {
        removeLabelIds: ['UNREAD'],
      });
      updateMessage(messageId, { is_read: true });
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  }

  async function toggleStar() {
    if (!message) return;

    try {
      if (message.is_starred) {
        await api.modifyEmailMessage(accountId, messageId, {
          removeLabelIds: ['STARRED'],
        });
        updateMessage(messageId, { is_starred: false });
      } else {
        await api.modifyEmailMessage(accountId, messageId, {
          addLabelIds: ['STARRED'],
        });
        updateMessage(messageId, { is_starred: true });
      }
    } catch (err) {
      console.error('Failed to toggle star:', err);
    }
  }

  function handleTrash() {
    if (!message) return;
    setTrashError(null);

    requestExternalAction({
      title: 'Confirmer la mise à la corbeille',
      description: 'Vérifie le message. Il ne sera déplacé qu’après ta confirmation.',
      confirmLabel: 'Mettre à la corbeille',
      details: [
        { label: 'Expéditeur', value: message.from_name || message.from_email },
        { label: 'Objet', value: message.subject || '(Sans objet)' },
      ],
    }, async () => {
      try {
        await api.deleteEmailMessage(accountId, messageId, false);
        removeMessage(messageId);
        setCurrentMessage(null);
      } catch (err: any) {
        console.error('Failed to trash message:', err);
        const msg = err?.message || '';
        if (msg.includes('expired') || msg.includes('revoked') || msg.includes('401') || msg.includes('Token')) {
          setTrashError('Connexion Gmail expirée. Reconnecte-toi via la bannière en haut.');
          setNeedsReauth(true);
        } else {
          // B-533 : sans confirmation du serveur, le message reste à l'écran.
          setTrashError('La suppression n’a pas été confirmée par le serveur. Le message est conservé.');
        }
      }
    });
  }

  function handleUseResponse(response: string) {
    // Un seul set() atomique pour éviter les problèmes de timing
    // entre le démontage d'EmailDetail et le montage d'EmailCompose
    if (!message || message.reply_to_emails == null) return;
    const recipients = adressesDeReponse();
    const subject = message ? `Re: ${message.subject || ''}` : '';
    setShowResponseModal(false);
    startComposing(recipients, subject, response, message.reply_to_emails);
  }

  // BUG-102 : construit une réponse citant le message d'origine (comme un vrai
  // client mail), au lieu d'un corps vide.
  function buildQuotedReply(): string {
    if (!message) return '';
    const original = texteDuCorps(message);
    if (!original.trim()) return '';
    const quoted = original
      .split('\n')
      .map((line) => `> ${line}`)
      .join('\n');
    return `\n\n\nLe ${formatDate(message.date)}, ${message.from_name || message.from_email} a écrit :\n${quoted}`;
  }

  function adressesDeReponse() {
    return message?.reply_to_emails?.length ? message.reply_to_emails : message ? [message.from_email] : [];
  }

  function handleReply() {
    if (!message || message.reply_to_emails == null) return;
    startComposing(adressesDeReponse(), `Re: ${message.subject || ''}`, buildQuotedReply(), message.reply_to_emails);
  }

  function handleReplyAll() {
    if (!message || message.reply_to_emails == null) return;
    const moi = accounts.find((a) => a.id === accountId)?.email.toLowerCase();
    const vus = new Set<string>();
    const allRecipients = [...adressesDeReponse(), ...message.to_emails, ...(message.cc_emails || [])].filter((email) => {
      const cle = email.toLowerCase();
      if (cle === moi || vus.has(cle)) return false;
      vus.add(cle);
      return true;
    });
    startComposing(allRecipients, `Re: ${message.subject || ''}`, buildQuotedReply(), message.reply_to_emails);
  }

  function handleForward() {
    if (!message) return;
    const forwardBody = `\n\n---------- Message transféré ----------\nDe : ${message.from_name || message.from_email} <${message.from_email}>\nDate : ${formatDate(message.date)}\nObjet : ${message.subject || '(Sans objet)'}\nÀ : ${message.to_emails.join(', ')}\n\n${texteDuCorps(message)}`;
    startComposing([], `Fwd: ${message.subject || ''}`, forwardBody);
  }

  async function handleCreateFollowUp() {
    if (!followUpDate || followUpSaving) return;
    setFollowUpSaving(true);
    setFollowUpFeedback(null);
    try {
      await api.createFollowUp({
        email_message_id: messageId,
        due_date: `${followUpDate}T09:00:00`,
        note: followUpNote.trim() || undefined,
      });
      setFollowUpFeedback('Relance créée. Elle apparaît dans Relances et alertes.');
      setFollowUpNote('');
      setShowFollowUpForm(false);
    } catch (err) {
      setFollowUpFeedback(err instanceof Error ? err.message : 'Impossible de créer la relance.');
    } finally {
      setFollowUpSaving(false);
    }
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  if (_loading) {
    return (
      <div className="flex-1 min-w-0 overflow-hidden flex items-center justify-center">
        <Spinner taille="zone" className="text-accent-cyan-ink" />
      </div>
    );
  }

  if (!message) {
    return (
      <div className="flex-1 min-w-0 overflow-hidden flex items-center justify-center">
        <EtatVide titre="Message introuvable">Sélectionne un autre message dans la liste.</EtatVide>
      </div>
    );
  }

  return (
    <div className="flex-1 min-w-0 overflow-hidden flex flex-col bg-background/20">

      {/* Header */}
      <div className="px-6 py-4 border-b border-border/30">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCurrentMessage(null)}
            aria-label="Revenir à la liste des messages"
          >
            <ChevronLeft className="w-5 h-5 text-text-muted" />
          </Button>

          <div className="flex flex-wrap items-center gap-2 max-[840px]:basis-full">
            <Button variant="ghost" size="sm" onClick={toggleStar}>
              <Star
                className={`w-4 h-4 ${message.is_starred ? 'fill-yellow-400 text-warning' : ''}`}
              />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleTrash}
              aria-label="Mettre à la corbeille"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Subject */}
        <div className="flex items-center gap-3 mb-3">
          {message.priority && (
            <EmailPriorityBadge
              priority={message.priority}
              score={message.priority_score || undefined}
              showText
            />
          )}
          <h3 className="text-xl font-semibold text-text flex-1">{message.subject || '(Sans objet)'}</h3>
        </div>

        {/* From/To */}
        <div className="space-y-2">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-tint border border-border flex items-center justify-center shrink-0">
              <Mail className="w-5 h-5 text-accent-cyan-ink" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-text">
                {message.from_name || message.from_email}
              </p>
              <p className="text-xs text-text-muted">{message.from_email}</p>
              <p className="text-xs text-text-muted mt-1">{formatDate(message.date)}</p>
            </div>
          </div>

          {message.to_emails.length > 0 && (
            <div className="text-xs text-text-muted pl-13">
              À : {message.to_emails.join(', ')}
            </div>
          )}
          {!!message.reply_to_emails?.length && <p className="text-xs text-text-muted">Adresse de réponse : {message.reply_to_emails.join(', ')}</p>}
          {bodyError && message.reply_to_emails == null && <p role="alert" className="text-xs text-warning">Impossible de vérifier l’adresse de réponse. Rouvre ce message une fois la connexion rétablie.</p>}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {bodyLoading ? (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-text-muted">
            <Spinner taille="zone" className="text-accent-cyan-ink" /> Chargement du message…
          </div>
        ) : message.body_html ? (
          (() => {
            const sanitized = sanitizeEmailHtml(message.body_html, {
              allowRemoteImages: showRemoteImages,
            });
            const hasBlockedImages = !showRemoteImages && sanitized.includes('data-remote-blocked');
            return (
              <>
                {hasBlockedImages && (
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text-muted">
                    <span>Les images distantes sont bloquées pour protéger ta vie privée.</span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setImagesAllowedFor(`${accountId}:${messageId}`)}
                    >
                      Afficher les images
                    </Button>
                  </div>
                )}
                <div
                  className="prose prose-invert max-w-none [&_*]:!text-text [&_a]:!text-accent-cyan-ink [&_a]:hover:!text-accent-cyan-ink [&_*]:!bg-transparent"
                  dangerouslySetInnerHTML={{ __html: sanitized }}
                />
              </>
            );
          })()
        ) : message.body_plain ? (
          <pre className="whitespace-pre-wrap text-sm text-text font-sans">{message.body_plain}</pre>
        ) : (
          <div className="text-sm text-text-muted">
            {bodyError && (
              <p className="mb-2 text-warning">
                Impossible de charger le message complet. Aperçu seulement :
              </p>
            )}
            <p className="italic">{message.snippet || 'Aucun contenu à afficher.'}</p>
          </div>
        )}
      </div>

      {/* Erreur suppression */}
      {trashError && (
        <Alerte className="mx-6 mb-2 shrink-0">{trashError}</Alerte>
      )}

      {followUpFeedback && (
        <div role="status" className="mx-6 mb-2 shrink-0 rounded-md border border-accent-cyan/20 bg-accent-cyan/5 px-3 py-2">
          <p className="text-xs text-text-muted">{followUpFeedback}</p>
        </div>
      )}

      {/* Actions — shrink-0 : la barre ne doit jamais être compressée ni poussée
          hors du cadre par le corps du mail (sinon « Générer une réponse » se
          retrouve coupé en bas). flex-wrap : sur un volet étroit, les boutons
          passent à la ligne au lieu d'être rognés (BUG-105). */}
      <div className="px-6 py-4 border-t border-border/30 flex flex-wrap items-center gap-2 shrink-0">
        <Button variant="primary" size="sm" onClick={() => setShowResponseModal(true)}>
          <Sparkles className="w-4 h-4 mr-2" />
          Générer une réponse
        </Button>
        <Button variant="ghost" size="sm" onClick={handleReply} disabled={message.reply_to_emails == null}>
          <Reply className="w-4 h-4 mr-2" />
          Répondre
        </Button>
        <Button variant="ghost" size="sm" onClick={handleReplyAll} disabled={message.reply_to_emails == null}>
          <ReplyAll className="w-4 h-4 mr-2" />
          Répondre à tous
        </Button>
        <Button variant="ghost" size="sm" onClick={handleForward}>
          <Forward className="w-4 h-4 mr-2" />
          Transférer
        </Button>
        <Button variant="ghost" size="sm" onClick={() => { setShowFollowUpForm((open) => !open); setFollowUpFeedback(null); }}>
          <Bell className="w-4 h-4 mr-2" />
          Créer une relance
        </Button>
      </div>

      {/* B-286 : le formulaire est rendu APRÈS la barre qui l'ouvre. Placé
          avant, il mettait le champ d'échéance en 3e position de tabulation
          et le déclencheur en dernière : depuis « Créer une relance », Tab
          sortait du volet au lieu d'entrer dans le formulaire (RULES-DESIGN
          §9.2, WCAG 2.4.3). */}
      {showFollowUpForm && (
        <div className="mx-6 mb-3 mt-1 shrink-0 rounded-md border border-border bg-surface p-3" data-testid="email-follow-up-form">
          <div className="grid gap-3 sm:grid-cols-[180px_1fr]">
            <FormField label="Échéance" htmlFor="email-follow-up-date">
              <Input id="email-follow-up-date" aria-label="Échéance de la relance" type="date" value={followUpDate} onChange={(event) => setFollowUpDate(event.target.value)} />
            </FormField>
            <FormField label="Note" htmlFor="email-follow-up-note">
              <Input id="email-follow-up-note" aria-label="Note de la relance" value={followUpNote} onChange={(event) => setFollowUpNote(event.target.value)} placeholder="Ce qu’il faudra vérifier ou demander…" />
            </FormField>
          </div>
          <div className="mt-3 flex flex-wrap justify-end gap-2 max-[840px]:justify-start"><Button variant="ghost" size="sm" onClick={() => setShowFollowUpForm(false)}>Annuler</Button><Button variant="primary" size="sm" onClick={() => void handleCreateFollowUp()} disabled={!followUpDate || followUpSaving}>{followUpSaving ? <Spinner taille="ligne" className="mr-1.5" /> : <CalendarClock className="mr-1.5 h-3.5 w-3.5" />}Créer la relance</Button></div>
        </div>
      )}

      {/* Response Generator Modal */}
      <ResponseGeneratorModal
        isOpen={showResponseModal}
        onClose={() => setShowResponseModal(false)}
        messageId={messageId}
        accountId={accountId}
        onUseResponse={handleUseResponse}
      />
    </div>
  );
}
