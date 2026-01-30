import { useState, useEffect } from 'react';
import { X, Briefcase, Loader2, Trash2, AlertCircle, Users } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
  project?: api.Project | null; // If provided, edit mode
}

interface FormData {
  name: string;
  description: string;
  contact_id: string;
  status: string;
  budget: string;
  notes: string;
  tags: string;
}

const initialFormData: FormData = {
  name: '',
  description: '',
  contact_id: '',
  status: 'active',
  budget: '',
  notes: '',
  tags: '',
};

const STATUS_OPTIONS = [
  { value: 'active', label: 'Actif', color: 'bg-green-500/20 text-green-400 border-green-500/30' },
  { value: 'pending', label: 'En attente', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  { value: 'completed', label: 'Terminé', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  { value: 'cancelled', label: 'Annulé', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
];

export function ProjectModal({ isOpen, onClose, onSaved, project }: ProjectModalProps) {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [contacts, setContacts] = useState<api.Contact[]>([]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [loadingContacts, setLoadingContacts] = useState(false);

  const isEditing = !!project;

  // Load contacts for linking
  useEffect(() => {
    if (isOpen) {
      loadContacts();
    }
  }, [isOpen]);

  async function loadContacts() {
    setLoadingContacts(true);
    try {
      const data = await api.listContacts();
      setContacts(data);
    } catch (err) {
      console.error('Failed to load contacts:', err);
    } finally {
      setLoadingContacts(false);
    }
  }

  // Load project data when editing
  useEffect(() => {
    if (isOpen && project) {
      setFormData({
        name: project.name || '',
        description: project.description || '',
        contact_id: project.contact_id || '',
        status: project.status || 'active',
        budget: project.budget?.toString() || '',
        notes: project.notes || '',
        tags: project.tags || '',
      });
    } else if (isOpen) {
      setFormData(initialFormData);
    }
    setError(null);
    setShowDeleteConfirm(false);
  }, [isOpen, project]);

  function handleChange(field: keyof FormData, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  }

  async function handleSave() {
    // Validation
    if (!formData.name.trim()) {
      setError('Le nom du projet est requis');
      return;
    }

    // Budget validation if provided
    if (formData.budget && isNaN(parseFloat(formData.budget))) {
      setError('Le budget doit être un nombre valide');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        contact_id: formData.contact_id || null,
        status: formData.status,
        budget: formData.budget ? parseFloat(formData.budget) : null,
        notes: formData.notes.trim() || null,
        tags: formData.tags.trim() || null,
      };

      if (isEditing && project) {
        await api.updateProject(project.id, payload);
      } else {
        await api.createProject(payload);
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
    if (!project) return;

    setDeleting(true);
    setError(null);

    try {
      await api.deleteProject(project.id);
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

  // Get contact display name
  function getContactDisplayName(contact: api.Contact): string {
    const parts = [contact.first_name, contact.last_name].filter(Boolean);
    const name = parts.length > 0 ? parts.join(' ') : 'Sans nom';
    return contact.company ? `${name} (${contact.company})` : name;
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
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-magenta/20 to-accent-cyan/20 flex items-center justify-center">
                  <Briefcase className="w-5 h-5 text-accent-magenta" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">
                    {isEditing ? 'Modifier le projet' : 'Nouveau projet'}
                  </h2>
                  <p className="text-xs text-text-muted">
                    {isEditing ? 'Modifiez les informations du projet' : 'Créez un nouveau projet'}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* Name */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">
                  Nom du projet <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Refonte site web"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Description du projet..."
                  rows={3}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
                />
              </div>

              {/* Status */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Statut</label>
                <div className="flex flex-wrap gap-2">
                  {STATUS_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => handleChange('status', option.value)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                        formData.status === option.value
                          ? option.color
                          : 'bg-background/40 text-text-muted border-border/50 hover:border-border'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Contact link */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Contact associé
                </label>
                <select
                  value={formData.contact_id}
                  onChange={(e) => handleChange('contact_id', e.target.value)}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  disabled={loadingContacts}
                >
                  <option value="">Aucun contact</option>
                  {contacts.map((contact) => (
                    <option key={contact.id} value={contact.id}>
                      {getContactDisplayName(contact)}
                    </option>
                  ))}
                </select>
                {loadingContacts && (
                  <p className="text-xs text-text-muted flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Chargement des contacts...
                  </p>
                )}
              </div>

              {/* Budget */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Budget (€)</label>
                <input
                  type="number"
                  value={formData.budget}
                  onChange={(e) => handleChange('budget', e.target.value)}
                  placeholder="5000"
                  min="0"
                  step="100"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <label className="text-sm text-text-muted">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Notes internes sur le projet..."
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
                  placeholder="web, design, urgent"
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
                    <p className="text-sm text-red-400 font-medium">Supprimer ce projet ?</p>
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
