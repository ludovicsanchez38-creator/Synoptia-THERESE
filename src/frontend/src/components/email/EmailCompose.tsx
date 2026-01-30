/**
 * THÉRÈSE v2 - Email Compose
 *
 * Compose new email or draft.
 * Phase 1 Frontend - Email
 */

import { useState } from 'react';
import { Send, X, Loader2, Paperclip } from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function EmailCompose() {
  const {
    currentAccountId,
    draftRecipients,
    draftSubject,
    draftBody,
    draftIsHtml,
    setDraftRecipients,
    setDraftSubject,
    setDraftBody,
    clearDraft,
    setIsComposing,
  } = useEmailStore();

  const [toInput, setToInput] = useState(draftRecipients.join(', '));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!currentAccountId) return;

    const recipients = toInput
      .split(',')
      .map((r) => r.trim())
      .filter((r) => r);

    if (recipients.length === 0) {
      setError('Veuillez ajouter au moins un destinataire');
      return;
    }

    if (!draftSubject.trim()) {
      setError('Veuillez ajouter un objet');
      return;
    }

    setSending(true);
    setError(null);

    try {
      await api.sendEmail(currentAccountId, {
        to: recipients,
        subject: draftSubject,
        body: draftBody,
        html: draftIsHtml,
      });

      clearDraft();
      setIsComposing(false);
    } catch (err) {
      console.error('Failed to send email:', err);
      setError(err instanceof Error ? err.message : 'Échec de l\'envoi');
    } finally {
      setSending(false);
    }
  }

  async function handleSaveDraft() {
    if (!currentAccountId) return;

    const recipients = toInput
      .split(',')
      .map((r) => r.trim())
      .filter((r) => r);

    if (recipients.length === 0 || !draftSubject.trim()) {
      setError('Veuillez remplir au moins le destinataire et l\'objet');
      return;
    }

    setSending(true);
    setError(null);

    try {
      await api.createDraft(currentAccountId, {
        to: recipients,
        subject: draftSubject,
        body: draftBody,
        html: draftIsHtml,
      });

      clearDraft();
      setIsComposing(false);
    } catch (err) {
      console.error('Failed to save draft:', err);
      setError(err instanceof Error ? err.message : 'Échec de la sauvegarde');
    } finally {
      setSending(false);
    }
  }

  function handleCancel() {
    if (confirm('Abandonner ce brouillon ?')) {
      clearDraft();
      setIsComposing(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/30 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text">Nouveau message</h3>
        <button
          onClick={handleCancel}
          className="p-2 hover:bg-border/30 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-text-muted" />
        </button>
      </div>

      {/* Form */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Recipients */}
        <div className="px-6 py-3 border-b border-border/30">
          <div className="flex items-center gap-3">
            <label className="text-sm text-text-muted w-16">À</label>
            <input
              type="text"
              value={toInput}
              onChange={(e) => setToInput(e.target.value)}
              placeholder="destinataire@example.com, ..."
              className="flex-1 px-3 py-2 bg-transparent text-sm text-text placeholder:text-text-muted/50 focus:outline-none"
            />
          </div>
        </div>

        {/* Subject */}
        <div className="px-6 py-3 border-b border-border/30">
          <div className="flex items-center gap-3">
            <label className="text-sm text-text-muted w-16">Objet</label>
            <input
              type="text"
              value={draftSubject}
              onChange={(e) => setDraftSubject(e.target.value)}
              placeholder="Objet du message"
              className="flex-1 px-3 py-2 bg-transparent text-sm text-text placeholder:text-text-muted/50 focus:outline-none"
            />
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-hidden">
          <textarea
            value={draftBody}
            onChange={(e) => setDraftBody(e.target.value)}
            placeholder="Écrivez votre message..."
            className="w-full h-full px-6 py-4 bg-transparent text-sm text-text placeholder:text-text-muted/50 resize-none focus:outline-none"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 border-t border-border/30">
        {error && (
          <div className="mb-3 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="primary" size="sm" onClick={handleSend} disabled={sending}>
              {sending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Envoi...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Envoyer
                </>
              )}
            </Button>
            <Button variant="ghost" size="sm" onClick={handleSaveDraft} disabled={sending}>
              Sauvegarder brouillon
            </Button>
          </div>

          <Button variant="ghost" size="sm" disabled>
            <Paperclip className="w-4 h-4 mr-2" />
            Joindre
          </Button>
        </div>
      </div>
    </div>
  );
}
