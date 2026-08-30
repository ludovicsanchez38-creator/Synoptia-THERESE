import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Briefcase, Trash2, AlertCircle, Users, Upload, FileText, FileSpreadsheet, File } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { ProjectSyncSection } from './ProjectSyncSection';
import { Spinner } from '../ui/Spinner';

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
  { value: 'active', label: 'Actif', color: 'bg-success/20 text-success border-success/30' },
  { value: 'on_hold', label: 'En attente', color: 'bg-warning/20 text-warning border-warning/30' },
  { value: 'completed', label: 'Terminé', color: 'bg-info/20 text-info border-info/30' },
  { value: 'cancelled', label: 'Annulé', color: 'bg-error/20 text-error border-error/30' },
];

export function ProjectModal({ isOpen, onClose, onSaved, project }: ProjectModalProps) {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [contacts, setContacts] = useState<api.Contact[]>([]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  // Un fichier joint ne part plus au premier clic : on retient lequel est
  // visé, et l'appel réseau n'existe qu'au clic de confirmation. Bandeau EN
  // LIGNE, comme pour la suppression du projet juste en dessous : superposer
  // une boîte ferait fermer CETTE modale par Échap.
  const [fichierASupprimer, setFichierASupprimer] = useState<api.FileMetadata | null>(null);
  const boutonSuppressionRef = useRef<HTMLButtonElement | null>(null);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [projectFiles, setProjectFiles] = useState<api.FileMetadata[]>([]);
  const [uploadingFile, setUploadingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isEditing = !!project;

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la cascade de la coque, ou par l'escapeStack du parent.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen });

  // Load contacts for linking
  useEffect(() => {
    if (isOpen) {
      loadContacts();
      if (project) {
        loadProjectFiles(project.id);
      } else {
        setProjectFiles([]);
      }
    }
  }, [isOpen, project]);

  async function loadProjectFiles(projectId: string) {
    try {
      const files = await api.listProjectFiles(projectId);
      setProjectFiles(files);
    } catch (err) {
      console.error('Erreur chargement fichiers projet :', err);
    }
  }

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length || !project) return;

    setUploadingFile(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        await api.uploadProjectFile(file, project.id);
      }
      await loadProjectFiles(project.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'upload");
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }, [project]);

  async function confirmerSuppressionFichier() {
    const cible = fichierASupprimer;
    if (!cible) return;
    try {
      await api.deleteFile(cible.id);
      setProjectFiles((prev) => prev.filter((f) => f.id !== cible.id));
      setFichierASupprimer(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur suppression fichier');
    }
  }

  function renoncerSuppressionFichier() {
    setFichierASupprimer(null);
    // Le focus revient d'où il venait : sans cela, il retombe sur le corps de
    // la modale et l'on perd sa place dans la liste.
    boutonSuppressionRef.current?.focus();
  }

  function getFileIcon(ext: string) {
    if (['.md', '.txt', '.docx', '.pdf'].includes(ext)) return <FileText className="w-4 h-4 text-accent-cyan-ink" />;
    if (['.xlsx', '.csv'].includes(ext)) return <FileSpreadsheet className="w-4 h-4 text-agent-green" />;
    return <File className="w-4 h-4 text-text-muted" />;
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  }

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
        tags: Array.isArray(project.tags) ? project.tags.join(', ') : (project.tags || ''),
      });
    } else if (isOpen) {
      setFormData(initialFormData);
    }
    setError(null);
    setShowDeleteConfirm(false);
    // La cible d'une suppression ne survit PAS au changement de projet. Sans
    // cette ligne, viser un fichier dans le projet A sans confirmer, puis
    // ouvrir le projet B, y faisait réapparaître la question — et confirmer
    // supprimait alors un fichier de A depuis B. Une confirmation qui survit à
    // son contexte donne l'accord de l'utilisateur à autre chose que ce qu'il
    // a vu.
    setFichierASupprimer(null);
    boutonSuppressionRef.current = null;
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
        tags: formData.tags.trim()
          ? formData.tags.split(',').map(t => t.trim()).filter(Boolean)
          : null,
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
            className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={isEditing ? 'Modifier le projet' : 'Nouveau projet'}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-surface border border-border rounded-md shadow-2xl ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-sm bg-domaine-factures-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
                  <Briefcase className="w-5 h-5 text-accent-magenta-ink" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">
                    {isEditing ? 'Modifier le projet' : 'Nouveau projet'}
                  </h2>
                  <p className="text-xs text-text-muted">
                    {isEditing ? 'Modifie les informations du projet' : 'Crée un nouveau projet'}
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
                <label htmlFor="projectmodal-nom-du-projet" className="text-sm text-text-muted">
                  Nom du projet <span className="text-error">*</span>
                </label>
                <input id="projectmodal-nom-du-projet"
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Refonte site web"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <label htmlFor="projectmodal-description" className="text-sm text-text-muted">Description</label>
                <textarea id="projectmodal-description"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Description du projet..."
                  rows={3}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
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
                      className={`px-3 py-1.5 rounded-md text-sm font-medium border transition-all ${
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
                <label htmlFor="projectmodal-contact-associe" className="text-sm text-text-muted flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Contact associé
                </label>
                <select id="projectmodal-contact-associe"
                  value={formData.contact_id}
                  onChange={(e) => handleChange('contact_id', e.target.value)}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors"
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
                    <Spinner taille="ligne" />
                    Chargement des contacts...
                  </p>
                )}
              </div>

              {/* Budget */}
              <div className="space-y-2">
                <label htmlFor="projectmodal-budget" className="text-sm text-text-muted">Budget (€)</label>
                <input id="projectmodal-budget"
                  type="number"
                  value={formData.budget}
                  onChange={(e) => handleChange('budget', e.target.value)}
                  placeholder="5000"
                  min="0"
                  step="100"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <label htmlFor="projectmodal-notes" className="text-sm text-text-muted">Notes</label>
                <textarea id="projectmodal-notes"
                  value={formData.notes}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Notes internes sur le projet..."
                  rows={3}
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors resize-none"
                />
              </div>

              {/* Dossier synchronisé (0.45) - visible uniquement en édition */}
              {isEditing && project && (
                <ProjectSyncSection projectId={project.id} />
              )}

              {/* Fichiers du projet (visible uniquement en édition) */}
              {isEditing && project && (
                <div className="space-y-2">
                  <label className="text-sm text-text-muted flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    Fichiers du projet
                  </label>
                  {/* Liste des fichiers */}
                  {projectFiles.length > 0 && (
                    <div className="space-y-1">
                      {projectFiles.map((f) => (
                        <div
                          key={f.id}
                          className="flex items-center gap-2 px-3 py-2 bg-background/40 rounded-md border border-border/30"
                        >
                          {getFileIcon(f.extension)}
                          <span className="flex-1 text-sm text-text truncate">{f.name}</span>
                          <span className="text-xs text-text-muted">{formatFileSize(f.size)}</span>
                          <button
                            type="button"
                            onClick={(event) => {
                              boutonSuppressionRef.current = event.currentTarget;
                              setFichierASupprimer(f);
                            }}
                            className="p-1 rounded-sm hover:bg-error/10 text-text-muted hover:text-error transition-colors"
                            aria-label={`Supprimer le fichier ${f.name}`}
                            title={`Supprimer le fichier ${f.name}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Bouton d'upload */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".md,.txt,.csv,.xlsx,.pdf,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Button
                    variant="ghost"
                    className="w-full border border-dashed border-border/50 hover:border-accent-cyan/50"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadingFile}
                  >
                    {uploadingFile ? (
                      <><Spinner taille="bouton" className="mr-2" />Upload en cours...</>
                    ) : (
                      <><Upload className="w-4 h-4 mr-2" />Ajouter un fichier (.md, .xlsx, .pdf, .docx)</>
                    )}
                  </Button>
                </div>
              )}

              {/* Tags */}
              <div className="space-y-2">
                <label htmlFor="projectmodal-tags-separes-par-des-virgule" className="text-sm text-text-muted">Tags (séparés par des virgules)</label>
                <input id="projectmodal-tags-separes-par-des-virgule"
                  type="text"
                  value={formData.tags}
                  onChange={(e) => handleChange('tags', e.target.value)}
                  placeholder="web, design, urgent"
                  className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
              </div>

              {/* Error */}
              {error && (
                <div role="alert" className="flex items-center gap-2 px-3 py-2 bg-error/10 border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <span className="text-sm text-error">{error}</span>
                </div>
              )}

              {/* Suppression d'un fichier joint : confirmation en ligne */}
              {fichierASupprimer && (
                <div className="flex items-center gap-2 px-3 py-3 bg-[var(--color-error-tint)] border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-error font-medium">
                      Supprimer « {fichierASupprimer.name} » ?
                    </p>
                    <p className="text-xs text-error/70">Cette action est irréversible.</p>
                  </div>
                  <div className="flex gap-2">
                    {/* Pas « Annuler » : le formulaire en a déjà un, et deux
                        boutons du même nom à l'écran ne disent pas ce qu'ils
                        annulent - ni à l'œil, ni au lecteur d'écran. */}
                    <Button variant="ghost" size="sm" onClick={renoncerSuppressionFichier}>
                      Conserver le fichier
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={confirmerSuppressionFichier}
                    >
                      Supprimer définitivement
                    </Button>
                  </div>
                </div>
              )}

              {/* Delete confirmation */}
              {showDeleteConfirm && (
                <div className="flex items-center gap-2 px-3 py-3 bg-error/10 border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-error font-medium">Supprimer ce projet ?</p>
                    <p className="text-xs text-error/70">Cette action est irréversible.</p>
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
