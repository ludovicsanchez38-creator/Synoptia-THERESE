import { useState, useEffect, useRef } from 'react';
import { X, User, Trash2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import { useContactsStore } from '../../stores/contactsStore';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { Spinner } from '../ui/Spinner';

interface ContactModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
  contact?: api.Contact | null; // If provided, edit mode
}

interface FormData {
  first_name: string;
  last_name: string;
  company: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
  tags: string;
}

const initialFormData: FormData = {
  first_name: '',
  last_name: '',
  company: '',
  email: '',
  phone: '',
  address: '',
  notes: '',
  tags: '',
};

export function ContactModal({ isOpen, onClose, onSaved, contact }: ContactModalProps) {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isEditing = !!contact;

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la cascade de la coque (ConversationCanvasPrototype) via le store.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen });

  // Load contact data when editing
  useEffect(() => {
    if (isOpen && contact) {
      setFormData({
        first_name: contact.first_name || '',
        last_name: contact.last_name || '',
        company: contact.company || '',
        email: contact.email || '',
        phone: contact.phone || '',
        address: contact.address || '',
        notes: contact.notes || '',
        tags: Array.isArray(contact.tags) ? contact.tags.join(', ') : (contact.tags || ''),
      });
    } else if (isOpen) {
      setFormData(initialFormData);
    }
    setError(null);
    setShowDeleteConfirm(false);
  }, [isOpen, contact]);

  function handleChange(field: keyof FormData, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  }

  async function handleSave() {
    // Validation
    if (!formData.first_name.trim() && !formData.last_name.trim()) {
      setError('Le prénom ou le nom est requis');
      return;
    }

    // Email validation if provided
    if (formData.email && !isValidEmail(formData.email)) {
      setError('Format email invalide');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        first_name: formData.first_name.trim() || null,
        last_name: formData.last_name.trim() || null,
        company: formData.company.trim() || null,
        email: formData.email.trim() || null,
        phone: formData.phone.trim() || null,
        address: formData.address.trim() || null,
        notes: formData.notes.trim() || null,
        tags: formData.tags.trim()
          ? formData.tags.split(',').map(t => t.trim()).filter(Boolean)
          : null,
      };

      // Via le store unique : la création/édition se reflète aussitôt Mémoire ET CRM (P4).
      if (isEditing && contact) {
        await useContactsStore.getState().updateContact(contact.id, payload);
      } else {
        await useContactsStore.getState().createContact(payload);
      }

      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!contact) return;

    setDeleting(true);
    setError(null);

    try {
      await useContactsStore.getState().deleteContact(contact.id);
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la suppression');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={isEditing ? 'Modifier le contact' : 'Nouveau contact'}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-surface border border-border rounded-md shadow-2xl ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-sm bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
                  <User className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">
                    {isEditing ? 'Modifier le contact' : 'Nouveau contact'}
                  </h2>
                  <p className="text-xs text-text-muted">
                    {isEditing ? 'Modifie les informations du contact' : 'Ajoute un nouveau contact à ta mémoire'}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* Name row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="contactmodal-prenom" className="text-sm text-text-muted">Prénom</label>
                  <input id="contactmodal-prenom"
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                    placeholder="Jean"
                    className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="contactmodal-nom" className="text-sm text-text-muted">Nom</label>
                  <input id="contactmodal-nom"
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                    placeholder="Dupont"
                    className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  />
                </div>
              </div>

              {/* Company */}
              <div className="space-y-2">
                <label htmlFor="contactmodal-entreprise" className="text-sm text-text-muted">Entreprise</label>
                <input id="contactmodal-entreprise"
                  type="text"
                  value={formData.company}
                  onChange={(e) => handleChange('company', e.target.value)}
                  placeholder="Synoptïa"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <label htmlFor="contactmodal-email" className="text-sm text-text-muted">Email</label>
                <input id="contactmodal-email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="jean@example.com"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <label htmlFor="contactmodal-telephone" className="text-sm text-text-muted">Téléphone</label>
                <input id="contactmodal-telephone"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  placeholder="Numéro de téléphone"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Adresse — B2 : sans elle, un devis part avec un destinataire
                  vide. Le champ existait en base et n'était saisissable nulle
                  part. */}
              <div className="space-y-2">
                <label htmlFor="contactmodal-adresse" className="text-sm text-text-muted">Adresse</label>
                <input id="contactmodal-adresse"
                  type="text"
                  value={formData.address}
                  onChange={(e) => handleChange('address', e.target.value)}
                  placeholder="Numéro et rue, code postal, ville"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <label htmlFor="contactmodal-notes" className="text-sm text-text-muted">Notes</label>
                <textarea id="contactmodal-notes"
                  value={formData.notes}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Informations complémentaires..."
                  rows={3}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
                />
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <label htmlFor="contactmodal-tags-separes-par-des-virgule" className="text-sm text-text-muted">Tags (séparés par des virgules)</label>
                <input id="contactmodal-tags-separes-par-des-virgule"
                  type="text"
                  value={formData.tags}
                  onChange={(e) => handleChange('tags', e.target.value)}
                  placeholder="client, prospect, partenaire"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Error */}
              {error && (
                <div role="alert" className="flex items-center gap-2 px-3 py-2 bg-error/10 border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <span className="text-sm text-error">{error}</span>
                </div>
              )}

              {/* Delete confirmation */}
              {showDeleteConfirm && (
                <div className="flex items-center gap-2 px-3 py-3 bg-error/10 border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-error font-medium">Supprimer ce contact ?</p>
                    <p className="text-xs text-error">Cette action est irréversible.</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowDeleteConfirm(false)}
                    >
                      Annuler
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={handleDelete}
                      disabled={deleting}
                    >
                      {deleting ? <Spinner taille="bouton" /> : 'Supprimer'}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-border/50 shrink-0">
              <div>
                {isEditing && !showDeleteConfirm && (
                  <Button
                    variant="ghost"
                    className="text-error hover:text-error hover:bg-error/10"
                    onClick={() => setShowDeleteConfirm(true)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Supprimer
                  </Button>
                )}
              </div>
              <div className="flex gap-3">
                <Button variant="ghost" onClick={onClose}>
                  Annuler
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <Spinner taille="bouton" className="mr-2" />
                      Enregistrement...
                    </>
                  ) : isEditing ? (
                    'Mettre à jour'
                  ) : (
                    'Créer'
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
