/**
 * THÉRÈSE v2 - Éditeur de signature email
 *
 * Quick win testeur (Capov, Discord alpha) : la brique backend existait déjà
 * (signature_html par compte, GET/PUT, injection à l'envoi) mais n'était pas
 * exposée dans l'UI. Cette modale permet d'éditer la signature d'un compte.
 *
 * Sécurité : aperçu sanitisé via la politique partagée sanitizeEmailHtml (même
 * filtre que l'affichage des emails reçus, interdit style/script) ; le backend
 * re-sanitise via nh3 au PUT (double filet, source de vérité).
 *
 * Échap : la modale s'inscrit sur la pile Échap unifiée (escapeStack) pour se
 * fermer sans laisser cascade Échap de la coque éjecter la vue email (cf. KO revue produit).
 */
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { X, Mail, Check } from 'lucide-react';
import { getEmailSignature, updateEmailSignature } from '../../services/api/email';
import { sanitizeEmailHtml } from '../../lib/sanitizeEmailHtml';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';
import { FormField } from '../ui/FormField';
import { Textarea } from '../ui/Textarea';

interface SignatureEditorModalProps {
  accountId: string;
  accountEmail?: string;
  onClose: () => void;
}

export function SignatureEditorModal({ accountId, accountEmail, onClose }: SignatureEditorModalProps) {
  const [html, setHtml] = useState('');
  // B-408 : version chargée, pour savoir si la saisie a changé avant de fermer.
  const [htmlCharge, setHtmlCharge] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // B-396 : un chargement en échec bloque la saisie, sinon « Enregistrer »
  // envoyait une signature vide que le serveur écrasait sans condition.
  const [loadFailed, setLoadFailed] = useState(false);

  const dialogRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const savedTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  // Échap unifié : monte/démonte une seule fois (onClose stable via ref) pour
  // éviter le churn push/pop dû aux re-renders d'EmailPanel (polling reauth 3s).
  useEffect(() => pushEscapeHandler(() => onCloseRef.current()), []);

  // US-013 : focus initial + piège Tab + restauration via le hook mutualisé.
  // Pas d'onEscape : Échap reste géré par la pile unifiée (escapeStack) ci-dessus.
  useDialogFocusTrap(dialogRef, { active: true });

  // Nettoyage du timer du badge « Enregistré ».
  useEffect(() => {
    return () => {
      if (savedTimer.current) clearTimeout(savedTimer.current);
    };
  }, []);

  // Chargement de la signature courante.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await getEmailSignature(accountId);
        if (!cancelled) {
          setHtml(res.signature_html || '');
          setHtmlCharge(res.signature_html || '');
        }
      } catch {
        if (!cancelled) {
          setError('Impossible de charger la signature. Ferme et réessaie.');
          setLoadFailed(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accountId]);

  // Focus initial sur le textarea une fois le contenu chargé.
  useEffect(() => {
    if (!loading) textareaRef.current?.focus();
  }, [loading]);

  // B-408 : un clic sur le voile fermait et perdait la signature en cours.
  function fermerSiPropre() {
    if (html === htmlCharge) {
      onClose();
      return;
    }
    setError('Signature modifiée : enregistre-la, ou ferme avec le bouton Fermer pour abandonner.');
  }

  async function handleSave() {
    if (loadFailed) return;
    setSaving(true);
    setError(null);
    try {
      const res = await updateEmailSignature(accountId, html);
      // Le backend (nh3) peut retirer du contenu non autorisé : on le signale.
      // Heuristique sur la longueur pour éviter un faux positif quand nh3 AJOUTE
      // (ex. rel=noopener), auquel cas la sortie est plus longue, pas plus courte.
      const cleaned = res.signature_html.trim().length < html.trim().length;
      setHtml(res.signature_html); // version sanitisée = ce qui sera réellement envoyé
      setHtmlCharge(res.signature_html);
      setNotice(
        cleaned
          ? 'Enregistré. Des éléments non autorisés ont été retirés pour la sécurité.'
          : null
      );
      setSaved(true);
      if (savedTimer.current) clearTimeout(savedTimer.current);
      savedTimer.current = setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Échec de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  }

  const preview = sanitizeEmailHtml(html);

  return createPortal(
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL}`}
        onClick={fermerSiPropre}
      />
      <motion.div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Signature email"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 ${Z_LAYER.MODAL} w-full max-w-3xl`}
      >
        <Carte className="p-6">
          {/* En-tête */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-accent-tint p-2">
                <Mail className="h-5 w-5 text-accent" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-text">Signature email</h2>
                <p className="text-sm text-text-muted">
                  {accountEmail
                    ? `Ajoutée automatiquement à l'envoi depuis ${accountEmail}`
                    : "Ajoutée automatiquement à l'envoi"}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              aria-label="Fermer"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12 text-text-muted">
              <Spinner taille="zone" className="mr-2" /> Chargement...
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormField label="HTML" htmlFor="signature-html">
                  <Textarea
                    id="signature-html"
                    disabled={loading || loadFailed}
                    ref={textareaRef}
                    value={html}
                    onChange={(e) => setHtml(e.target.value)}
                    placeholder={'<p>Marie Exemple<br/>Exemple SARL</p>'}
                    className="h-64 resize-none font-mono"
                  />
                </FormField>
                <div>
                  <span id="signature-preview-label" className="block text-sm font-medium text-text mb-2">
                    Aperçu
                  </span>
                  <div
                    role="region"
                    aria-labelledby="signature-preview-label"
                    className="h-64 w-full overflow-auto rounded-sm border border-border bg-surface px-4 py-3 text-sm text-text [&_a]:text-accent-cyan-ink [&_a]:underline"
                    dangerouslySetInnerHTML={{ __html: preview }}
                  />
                </div>
              </div>

              {notice && <Alerte ton="attention" className="mt-3">{notice}</Alerte>}
              {error && <Alerte className="mt-3">{error}</Alerte>}

              <div className="mt-6 flex flex-wrap items-center justify-end gap-3 max-[840px]:justify-start">
                <Button
                  variant="ghost"
                  onClick={onClose}
                >
                  Annuler
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSave}
                  disabled={saving || loadFailed}
                >
                  {saving ? (
                    <Spinner taille="bouton" />
                  ) : saved ? (
                    <Check className="w-4 h-4" />
                  ) : null}
                  {saved ? 'Enregistré' : 'Enregistrer'}
                </Button>
              </div>
            </>
          )}
        </Carte>
      </motion.div>
    </>,
    document.body
  );
}
