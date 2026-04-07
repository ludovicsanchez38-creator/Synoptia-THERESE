/**
 * THÉRÈSE v2 - Email Compose
 *
 * Compose new email or draft.
 * Phase 1 Frontend - Email
 */

import { useState, useEffect } from 'react';
import { Send, X, Loader2, Paperclip, ChevronDown, ChevronUp } from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

export function EmailCompose() {
  const {
    currentAccountId,
    draftRecipients,
    draftCc,
    draftBcc,
    draftSubject,
    draftBody,
    draftIsHtml,
    setDraftSubject,
    setDraftBody,
    clearDraft,
    setIsComposing,
  } = useEmailStore();

  const [toInput, setToInput] = useState(draftRecipients.join(', '));
  const [ccInput, setCcInput] = useState(draftCc.join(', '));
  const [bccInput, setBccInput] = useState(draftBcc.join(', '));
  const [showCcBcc, setShowCcBcc] = useState(draftCc.length > 0 || draftBcc.length > 0);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  // Synchroniser toInput avec draftRecipients (au cas où le store change après le mount)
  useEffect(() => {
    if (draftRecipients.length > 0) {
      setToInput(draftRecipients.join(', '));
    }
  }, [draftRecipients]);

  function parseRecipients(input: string): string[] {
    return input.split(',').map((r) => r.trim()).filter((r) => r);
  }

  async function handleSend() {
    if (!currentAccountId) {
      setError('Aucun compte email configuré. Ajoute un compte dans les paramètres.');
      return;
    }

    const recipients = parseRecipients(toInput);
    const ccList = parseRecipients(ccInput);
    const bccList = parseRecipients(bccInput);

    if (recipients.length === 0) {
      setError('Ajoute au moins un destinataire');
      return;
    }

    // BUG-085 : validation email basique côté frontend (feedback immédiat)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const invalidRecipients = recipients.filter(r => !emailRegex.test(r));
    if (invalidRecipients.length > 0) {
      setError(`Adresse(s) invalide(s) : ${invalidRecipients.join(', ')}`);
      return;
    }

    if (!draftSubject.trim()) {
      setError('Ajoute un objet');
      return;
    }

    setSending(true);
    setError(null);

    try {
      // BUG-085 : timeout client (35s) pour ne pas bloquer le spinner
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('TIMEOUT')), 35000)
      );

      await Promise.race([
        api.sendEmail(currentAccountId, {
          to: recipients,
          cc: ccList.length > 0 ? ccList : undefined,
          bcc: bccList.length > 0 ? bccList : undefined,
          subject: draftSubject,
          body: draftBody,
          html: draftIsHtml,
        }),
        timeoutPromise,
      ]);

      clearDraft();
      setIsComposing(false);
    } catch (err) {
      console.error('Failed to send email:', err);
      if (err instanceof Error && err.message === 'TIMEOUT') {
        setError("L'envoi a expiré. Vérifie ta connexion et la configuration email.");
      } else {
        setError(err instanceof Error ? err.message : "Échec de l'envoi");
      }
    } finally {
      setSending(false);
    }
  }

  async function handleSaveDraft() {
    if (!currentAccountId) {
      setError('Aucun compte email configuré. Ajoute un compte dans les paramètres.');
      return;
    }

    const recipients = parseRecipients(toInput);
    const ccList = parseRecipients(ccInput);
    const bccList = parseRecipients(bccInput);

    if (recipients.length === 0 || !draftSubject.trim()) {
      setError('Remplis au moins le destinataire et l\'objet');
      return;
    }

    setSending(true);
    setError(null);

    try {
      await api.createDraft(currentAccountId, {
        to: recipients,
        cc: ccList.length > 0 ? ccList : undefined,
        bcc: bccList.length > 0 ? bccList : undefined,
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
    // Si le brouillon est vide, fermer directement sans confirmation
    if (!draftBody.trim() && !draftSubject.trim() && !toInput.trim()) {
      clearDraft();
      setIsComposing(false);
      return;
    }
    setShowCancelConfirm(true);
  }

  function confirmCancel() {
    setShowCancelConfirm(false);
    clearDraft();
    setIsComposing(false);
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
            <button
              onClick={() => setShowCcBcc(!showCcBcc)}
              className="text-xs text-text-muted hover:text-accent-cyan transition-colors flex items-center gap-1"
            >
              Cc/Cci
              {showCcBcc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* CC / BCC */}
        {showCcBcc && (
          <>
            <div className="px-6 py-3 border-b border-border/30">
              <div className="flex items-center gap-3">
                <label className="text-sm text-text-muted w-16">Cc</label>
                <input
                  type="text"
                  value={ccInput}
                  onChange={(e) => setCcInput(e.target.value)}
                  placeholder="copie@example.com, ..."
                  className="flex-1 px-3 py-2 bg-transparent text-sm text-text placeholder:text-text-muted/50 focus:outline-none"
                />
              </div>
            </div>
            <div className="px-6 py-3 border-b border-border/30">
              <div className="flex items-center gap-3">
                <label className="text-sm text-text-muted w-16">Cci</label>
                <input
                  type="text"
                  value={bccInput}
                  onChange={(e) => setBccInput(e.target.value)}
                  placeholder="copie cachée@example.com, ..."
                  className="flex-1 px-3 py-2 bg-transparent text-sm text-text placeholder:text-text-muted/50 focus:outline-none"
                />
              </div>
            </div>
          </>
        )}

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
            placeholder="Écris ton message..."
            className="w-full h-full px-6 py-4 bg-transparent text-sm text-text placeholder:text-text-muted/50 resize-none focus:outline-none"
          />
        </div>
      </div>

      {/* Confirmation d'abandon */}
      {showCancelConfirm && (
        <div className="px-6 py-3 bg-yellow-500/10 border-t border-yellow-500/20 flex items-center gap-3">
          <p className="text-sm text-yellow-200 flex-1">Abandonner ce brouillon ?</p>
          <button
            onClick={confirmCancel}
            className="px-3 py-1.5 text-sm bg-red-500/20 text-red-300 hover:bg-red-500/30 rounded-lg transition-colors"
          >
            Oui, abandonner
          </button>
          <button
            onClick={() => setShowCancelConfirm(false)}
            className="px-3 py-1.5 text-sm text-text-muted hover:text-text transition-colors"
          >
            Non, continuer
          </button>
        </div>
      )}

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
