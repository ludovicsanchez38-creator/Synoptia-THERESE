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
 * fermer sans laisser resolveEscape éjecter la vue email (cf. KO revue produit).
 */
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { X, Mail, Loader2, Check } from 'lucide-react';
import { getEmailSignature, updateEmailSignature } from '../../services/api/email';
import { sanitizeEmailHtml } from '../../lib/sanitizeEmailHtml';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

interface SignatureEditorModalProps {
  accountId: string;
  accountEmail?: string;
  onClose: () => void;
}

export function SignatureEditorModal({ accountId, accountEmail, onClose }: SignatureEditorModalProps) {
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        if (!cancelled) setHtml(res.signature_html || '');
      } catch {
        if (!cancelled) setError('Impossible de charger la signature.');
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

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const res = await updateEmailSignature(accountId, html);
      // Le backend (nh3) peut retirer du contenu non autorisé : on le signale.
      // Heuristique sur la longueur pour éviter un faux positif quand nh3 AJOUTE
      // (ex. rel=noopener), auquel cas la sortie est plus longue, pas plus courte.
      const cleaned = res.signature_html.trim().length < html.trim().length;
      setHtml(res.signature_html); // version sanitisée = ce qui sera réellement envoyé
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
        onClick={onClose}
      />
      <motion.div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Signature email"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 ${Z_LAYER.MODAL} w-full max-w-3xl`}
      >
        <div className="bg-surface border border-text-muted/20 rounded-xl shadow-2xl p-6">
          {/* En-tête */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-accent-cyan/10">
                <Mail className="w-5 h-5 text-accent-cyan" />
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
            <button
              onClick={onClose}
              className="text-text-muted hover:text-text transition-colors"
              aria-label="Fermer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12 text-text-muted">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Chargement...
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="signature-html" className="block text-sm font-medium text-text mb-2">
                    HTML
                  </label>
                  <textarea
                    id="signature-html"
                    ref={textareaRef}
                    value={html}
                    onChange={(e) => setHtml(e.target.value)}
                    placeholder={'<p>Ludovic Sanchez<br/>Synoptïa</p>'}
                    className="w-full h-64 px-4 py-3 bg-background border border-text-muted/20 rounded-lg text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan resize-none font-mono text-sm"
                  />
                </div>
                <div>
                  <span id="signature-preview-label" className="block text-sm font-medium text-text mb-2">
                    Aperçu
                  </span>
                  <div
                    role="region"
                    aria-labelledby="signature-preview-label"
                    className="w-full h-64 px-4 py-3 bg-background border border-text-muted/20 rounded-lg overflow-auto text-sm text-text [&_a]:text-accent-cyan [&_a]:underline"
                    dangerouslySetInnerHTML={{ __html: preview }}
                  />
                </div>
              </div>

              {notice && <p className="mt-3 text-sm text-yellow-300">{notice}</p>}
              {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

              <div className="flex items-center justify-end gap-3 mt-6">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-text-muted/10 hover:bg-text-muted/20 text-text rounded-lg transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-accent-cyan text-white rounded-lg hover:bg-accent-cyan/90 transition-colors disabled:opacity-50"
                >
                  {saving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : saved ? (
                    <Check className="w-4 h-4" />
                  ) : null}
                  {saved ? 'Enregistré' : 'Enregistrer'}
                </button>
              </div>
            </>
          )}
        </div>
      </motion.div>
    </>,
    document.body
  );
}
