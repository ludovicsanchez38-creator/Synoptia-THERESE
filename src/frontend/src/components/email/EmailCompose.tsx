/**
 * THÉRÈSE v2 - Email Compose
 *
 * Compose new email or draft.
 * Phase 1 Frontend - Email
 */

import { useState, useEffect } from 'react';
import { Send, X, Paperclip, ChevronDown, ChevronUp } from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { FormField } from '../ui/FormField';
import { Alerte } from '../ui/Alerte';
import { useExternalActionConfirmation } from '../app/useExternalActionConfirmation';
import * as api from '../../services/api';
import { Spinner } from '../ui/Spinner';

export function EmailCompose() {
  const requestExternalAction = useExternalActionConfirmation();
  const {
    accounts,
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

  function handleSend() {
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

    const email = {
      to: recipients,
      cc: ccList.length > 0 ? ccList : undefined,
      bcc: bccList.length > 0 ? bccList : undefined,
      subject: draftSubject,
      body: draftBody,
      html: draftIsHtml,
    };

    requestExternalAction({
      title: 'Confirmer l’envoi de l’email',
      description: 'Vérifie les destinataires et le contenu. L’envoi ne partira qu’après ta confirmation.',
      confirmLabel: 'Confirmer et envoyer',
      details: [
        { label: 'Compte d’envoi', value: accounts.find((a) => a.id === currentAccountId)?.email || currentAccountId },
        { label: 'À', value: recipients.join(', ') },
        { label: 'Cc', value: ccList.join(', ') },
        { label: 'Cci', value: bccList.join(', ') },
        { label: 'Objet', value: draftSubject },
        { label: 'Message', value: draftBody },
      ],
    }, async () => {
      setSending(true);
      setError(null);

      try {
        // BUG-085 : timeout client (35s) pour ne pas bloquer le spinner
        const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('TIMEOUT')), 35000)
        );

        await Promise.race([
          api.sendEmail(currentAccountId, email),
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
    });
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
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-6 py-4">
        <h3 className="text-lg font-semibold text-text">Nouveau message</h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleCancel}
          aria-label="Fermer la composition"
        >
          <X className="w-5 h-5 text-text-muted" />
        </Button>
      </div>

      {/* Form */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Recipients */}
        <div className="border-b border-border px-6 py-3">
          <div className="flex flex-wrap items-end gap-3">
            <FormField label="À" htmlFor="emailcompose-destinataire" className="min-w-0 flex-1">
            <Input id="emailcompose-destinataire" aria-label="Destinataire"
              type="text"
              value={toInput}
              onChange={(e) => setToInput(e.target.value)}
              placeholder="destinataire@example.com, ..."
            />
            </FormField>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowCcBcc(!showCcBcc)}
              aria-expanded={showCcBcc}
            >
              Cc/Cci
              {showCcBcc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </Button>
          </div>
        </div>

        {/* CC / BCC */}
        {showCcBcc && (
          <>
            <div className="border-b border-border px-6 py-3">
              <FormField label="Cc" htmlFor="emailcompose-cc">
                <Input id="emailcompose-cc"
                  type="text"
                  value={ccInput}
                  onChange={(e) => setCcInput(e.target.value)}
                  placeholder="copie@example.com, ..."
                />
              </FormField>
            </div>
            <div className="border-b border-border px-6 py-3">
              <FormField label="Cci" htmlFor="emailcompose-cci">
                <Input id="emailcompose-cci"
                  type="text"
                  value={bccInput}
                  onChange={(e) => setBccInput(e.target.value)}
                  placeholder="copie cachée@example.com, ..."
                />
              </FormField>
            </div>
          </>
        )}

        {/* Subject */}
        <div className="border-b border-border px-6 py-3">
          <FormField label="Objet" htmlFor="emailcompose-objet">
            <Input id="emailcompose-objet"
              type="text"
              value={draftSubject}
              onChange={(e) => setDraftSubject(e.target.value)}
              placeholder="Objet du message"
            />
          </FormField>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-hidden">
          <Textarea
            aria-label="Corps du message"
            value={draftBody}
            onChange={(e) => setDraftBody(e.target.value)}
            placeholder="Écris ton message..."
            className="h-full resize-none rounded-none border-0 px-6 py-4 focus:ring-inset"
          />
        </div>
      </div>

      {/* Confirmation d'abandon */}
      {showCancelConfirm && (
        <div className="flex flex-wrap items-center gap-3 border-t border-warning/30 bg-[var(--color-warning-tint)] px-6 py-3">
          <p className="min-w-0 flex-1 text-sm text-text">Abandonner ce brouillon ?</p>
          <Button
            variant="danger"
            size="sm"
            onClick={confirmCancel}
          >
            Oui, abandonner
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCancelConfirm(false)}
          >
            Non, continuer
          </Button>
        </div>
      )}

      {/* Actions */}
      <div className="px-6 py-4 border-t border-border/30">
        {error && (
          <Alerte className="mb-3">{error}</Alerte>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 max-[840px]:items-stretch">
          <div className="flex flex-wrap items-center gap-2 max-[840px]:basis-full">
            <Button variant="primary" size="sm" onClick={handleSend} disabled={sending}>
              {sending ? (
                <>
                  <Spinner taille="bouton" className="mr-2" />
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
