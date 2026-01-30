import { useState, useEffect } from 'react';
import { X, User, Loader2, Trash2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';

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
  notes: string;
  tags: string;
}

const initialFormData: FormData = {
  first_name: '',
  last_name: '',
  company: '',
  email: '',
  phone: '',
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

  // Load contact data when editing
  useEffect(() => {
    if (isOpen && contact) {
      setFormData({
        first_name: contact.first_name || '',
        last_name: contact.last_name || '',
        company: contact.company || '',
        email: contact.email || '',
        phone: contact.phone || '',
        notes: contact.notes || '',
        tags: contact.tags || '',
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
        notes: formData.notes.trim() || null,
        tags: formData.tags.trim() || null,
      };

      if (isEditing && contact) {
        await api.updateContact(contact.id, payload);
      } else {
        await api.createContact(payload);
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
      await api.deleteContact(contact.id);
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la suppression');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  // Handle escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && isOpen) {
        if (showDeleteConfirm) {
          setShowDeleteConfirm(false);
        } else {
          onClose();
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, showDeleteConfirm]);

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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-surface border border-border rounded-xl shadow-2xl z-50 max-h-[85vh] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
                  <User className="w-5 h-5 text-accent-cyan" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">
                    {isEditing ? 'Modifier le contact' : 'Nouveau contact'}
                  </h2>
                  <p className="text-xs text-text-muted">
                    {isEditing ? 'Modifiez les informations du contact' : 'Ajoutez un nouveau contact à votre mémoire'}
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
                  <label className="text-sm text-text-muted">Prénom</label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                    placeholder="Jean"
                    className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-text-muted">Nom</label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                    placeholder="Dupont"
                    className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  />
                </div>
              </div>

              {/* Company */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Entreprise</label>
                <input
                  type="text"
                  value={formData.company}
                  onChange={(e) => handleChange('company', e.target.value)}
                  placeholder="Synoptïa"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="jean@example.com"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Téléphone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  placeholder="+33 6 12 34 56 78"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Informations complémentaires..."
                  rows={3}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
                />
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Tags (séparés par des virgules)</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => handleChange('tags', e.target.value)}
                  placeholder="client, prospect, partenaire"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                  <span className="text-sm text-red-400">{error}</span>
                </div>
              )}

              {/* Delete confirmation */}
              {showDeleteConfirm && (
                <div className="flex items-center gap-2 px-3 py-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-red-400 font-medium">Supprimer ce contact ?</p>
                    <p className="text-xs text-red-400/70">Cette action est irréversible.</p>
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
                      {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Supprimer'}
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
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
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
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
