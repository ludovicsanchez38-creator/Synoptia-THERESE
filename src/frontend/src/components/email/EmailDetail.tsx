/**
 * THÉRÈSE v2 - Email Detail
 *
 * Detailed view of an email message.
 * Phase 1 Frontend - Email
 */

import { useState, useEffect } from 'react';
import DOMPurify from 'dompurify';
import {
  Reply,
  ReplyAll,
  Forward,
  Star,
  Trash2,
  Mail,
  ChevronLeft,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';
import { ResponseGeneratorModal } from './ResponseGeneratorModal';
import { EmailPriorityBadge } from './EmailPriorityBadge';

/**
 * Sanitise le HTML d'un email :
 * 1. DOMPurify neutralise les scripts, event handlers, et vecteurs XSS
 * 2. Supprime les <style>/<link stylesheet> pour éviter les fuites CSS
 */
function sanitizeEmailHtml(html: string): string {
  const purified = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'div', 'span',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'dl', 'dt', 'dd',
      'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
      'img', 'blockquote', 'pre', 'code', 'hr', 'sup', 'sub', 'small',
      'figure', 'figcaption', 'abbr', 'address', 'details', 'summary',
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'class', 'id', 'width', 'height',
      'colspan', 'rowspan', 'cellpadding', 'cellspacing', 'border',
      'align', 'valign', 'target', 'rel',
    ],
    ALLOW_DATA_ATTR: false,
    ADD_ATTR: ['target'],
    FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea', 'select', 'button'],
  });
  // Supprimer les <link stylesheet> résiduels
  return purified.replace(/<link[^>]*rel=["']stylesheet["'][^>]*\/?>/gi, '');
}

interface EmailDetailProps {
  accountId: string;
  messageId: string;
}

export function EmailDetail({ accountId, messageId }: EmailDetailProps) {
  const { messages, setCurrentMessage, updateMessage, removeMessage, setIsComposing, setDraftRecipients, setDraftSubject, setDraftBody, setNeedsReauth } = useEmailStore();
  const [_loading, _setLoading] = useState(false);
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [trashError, setTrashError] = useState<string | null>(null);

  const message = messages.find((m) => m.id === messageId);

  // Mark as read when opened
  useEffect(() => {
    if (message && !message.is_read) {
      markAsRead();
    }
  }, [messageId]);

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

  async function handleTrash() {
    if (!message) return;
    setTrashError(null);

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
        setTrashError('Impossible de supprimer ce message.');
      }
    }
  }

  function handleUseResponse(response: string) {
    // Si le message n'est plus disponible dans le store (race condition, navigation rapide),
    // on ouvre quand même le compositeur avec le texte généré
    // plutôt que de silencieusement ne rien faire (BUG-026)
    if (message) {
      setDraftRecipients([message.from_email]);
      setDraftSubject(`Re: ${message.subject || ''}`);
    }
    setDraftBody(response);
    setIsComposing(true);
    setShowResponseModal(false);
  }

  function handleReply() {
    if (!message) return;
    setDraftRecipients([message.from_email]);
    setDraftSubject(`Re: ${message.subject || ''}`);
    setDraftBody('');
    setIsComposing(true);
  }

  function handleReplyAll() {
    if (!message) return;
    const allRecipients = [message.from_email, ...message.to_emails].filter(
      (email, index, self) => self.indexOf(email) === index
    );
    setDraftRecipients(allRecipients);
    setDraftSubject(`Re: ${message.subject || ''}`);
    setDraftBody('');
    setIsComposing(true);
  }

  function handleForward() {
    if (!message) return;
    setDraftRecipients([]);
    setDraftSubject(`Fwd: ${message.subject || ''}`);
    const forwardBody = `\n\n---------- Message transféré ----------\nDe : ${message.from_name || message.from_email} <${message.from_email}>\nDate : ${formatDate(message.date)}\nObjet : ${message.subject || '(Sans objet)'}\nÀ : ${message.to_emails.join(', ')}\n\n${message.body_plain || ''}`;
    setDraftBody(forwardBody);
    setIsComposing(true);
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
        <Loader2 className="w-8 h-8 animate-spin text-accent-cyan" />
      </div>
    );
  }

  if (!message) {
    return (
      <div className="flex-1 min-w-0 overflow-hidden flex items-center justify-center">
        <p className="text-text-muted">Message introuvable</p>
      </div>
    );
  }

  return (
    <div className="flex-1 min-w-0 overflow-hidden flex flex-col bg-background/20">

      {/* Header */}
      <div className="px-6 py-4 border-b border-border/30">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setCurrentMessage(null)}
            className="p-2 hover:bg-border/30 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-text-muted" />
          </button>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={toggleStar}>
              <Star
                className={`w-4 h-4 ${message.is_starred ? 'fill-yellow-400 text-yellow-400' : ''}`}
              />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleTrash}>
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
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center shrink-0">
              <Mail className="w-5 h-5 text-accent-cyan" />
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
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {message.body_html ? (
          <div
            className="prose prose-invert max-w-none [&_*]:!text-text [&_a]:!text-accent-cyan [&_a]:hover:!text-accent-cyan/80 [&_*]:!bg-transparent"
            dangerouslySetInnerHTML={{ __html: sanitizeEmailHtml(message.body_html) }}
          />
        ) : (
          <pre className="whitespace-pre-wrap text-sm text-text font-sans">{message.body_plain}</pre>
        )}
      </div>

      {/* Erreur suppression */}
      {trashError && (
        <div className="mx-6 mb-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-xs text-red-300">{trashError}</p>
        </div>
      )}

      {/* Actions */}
      <div className="px-6 py-4 border-t border-border/30 flex items-center gap-2">
        <Button variant="primary" size="sm" onClick={() => setShowResponseModal(true)}>
          <Sparkles className="w-4 h-4 mr-2" />
          Générer une réponse
        </Button>
        <Button variant="ghost" size="sm" onClick={handleReply}>
          <Reply className="w-4 h-4 mr-2" />
          Répondre
        </Button>
        <Button variant="ghost" size="sm" onClick={handleReplyAll}>
          <ReplyAll className="w-4 h-4 mr-2" />
          Répondre à tous
        </Button>
        <Button variant="ghost" size="sm" onClick={handleForward}>
          <Forward className="w-4 h-4 mr-2" />
          Transférer
        </Button>
      </div>

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
