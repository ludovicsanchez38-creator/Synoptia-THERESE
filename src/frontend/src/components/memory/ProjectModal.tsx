import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { contactDisplayName } from '../prototype/prototypeReadModels';
import { X, Briefcase, Trash2, AlertCircle, Upload, FileText, FileSpreadsheet, File } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { useQuestionDAbandonDeModale } from '../../hooks/useQuestionDAbandonDeModale';
import { useRendreLeFocusALaFermeture, useRevelerALApparition } from '../../hooks/useRevelerALApparition';
import { ProjectSyncSection } from './ProjectSyncSection';
import { ProjectDeliverablesSection } from './ProjectDeliverablesSection';
import { ProjectEnsembleSection } from './ProjectEnsembleSection';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Segments } from '../ui/Segments';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { useDemoMask } from '../../hooks/useDemoMask';
import { useDemoStore } from '../../stores/demoStore';
import { buildReplacementMap, maskText as appliquerMasque } from '../../lib/demoMask';
import { entreeValide } from '../../lib/entreeValide';
import { demanderLOuvertureDuTravail, type DestinationDuTravail } from '../../lib/destinationDuTravail';

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
  project?: api.Project | null; // If provided, edit mode
  /** B-1491 : montée hors du panelStore (vue Projets), la fenêtre ferme
   * elle-même une saisie intacte à Échap, au lieu de décliner. */
  fermerSiIntact?: boolean;
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
  { id: 'active', label: 'Actif' },
  { id: 'on_hold', label: 'En attente' },
  { id: 'completed', label: 'Terminé' },
  { id: 'cancelled', label: 'Annulé' },
];

export function ProjectModal({ isOpen, onClose, onSaved, project, fermerSiIntact = false }: ProjectModalProps) {
  const { enabled: demoEnabled, replacementMap, maskContact, maskProject } = useDemoMask();
  const [formData, setFormData] = useState<FormData>(initialFormData);
  // B-1392 : la saisie telle que chargée, pour savoir si elle a changé.
  const [reference, setReference] = useState<FormData>(initialFormData);
  const [contacts, setContacts] = useState<api.Contact[]>([]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  // B-1030 : le message et la confirmation vivent au bas du contenu défilant.
  const erreurRef = useRevelerALApparition(error);
  const confirmationRef = useRevelerALApparition(showDeleteConfirm, 'premier-bouton');
  // B-1061 : « Annuler » rend le focus au bouton « Supprimer ».
  const supprimerRef = useRef<HTMLButtonElement>(null);
  useRendreLeFocusALaFermeture(showDeleteConfirm, supprimerRef);
  // Un fichier joint ne part plus au premier clic : on retient lequel est
  // visé, et l'appel réseau n'existe qu'au clic de confirmation. Bandeau EN
  // LIGNE, comme pour la suppression du projet juste en dessous : superposer
  // une boîte ferait fermer CETTE modale par Échap.
  const [fichierASupprimer, setFichierASupprimer] = useState<api.FileMetadata | null>(null);
  // B-1060 : la confirmation du fichier joint est amenée dans la vue, focus sur « Conserver ».
  const confirmationFichierRef = useRevelerALApparition(fichierASupprimer?.id, 'premier-bouton');
  const boutonSuppressionRef = useRef<HTMLButtonElement | null>(null);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [contactsCharges, setContactsCharges] = useState(false);
  const [projectFiles, setProjectFiles] = useState<api.FileMetadata[]>([]);
  const [fichiersTronques, setFichiersTronques] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Une ouverture constitue un contexte distinct, même pour le même projet.
  const fichiersContexteRef = useRef(0);
  const fichiersRequeteRef = useRef(0);

  const masqueLocal = useMemo(() => new Map([
    ...replacementMap,
    ...buildReplacementMap(contacts, project ? [project] : []),
  ]), [replacementMap, contacts, project]);
  const maskText = useCallback((texte: string) => {
    if (!demoEnabled || !texte) return texte;
    // Une ouverture à froid ne peut pas attendre le masque global d'une autre
    // vue. Tant que les contacts sont inconnus, aucun texte libre n'est révélé.
    if (!contactsCharges) return 'Contenu masqué en mode démo';
    return appliquerMasque(texte, masqueLocal);
  }, [demoEnabled, contactsCharges, masqueLocal]);

  const isEditing = !!project;
  // P-148 : la fenêtre porte le nom du projet. En démonstration, le même
  // pseudonyme que le champ « Nom » (maskProject), jamais un second.
  const nomAffiche = project ? maskProject({ id: project.id, name: project.name }).name : '';

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la cascade de la coque, ou par l'escapeStack du parent.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen });

  // B-1392 : Échap, la croix, le fond et « Annuler » demandent avant de jeter
  // une saisie modifiée, comme Tâche et Rendez-vous.
  const modifie = !demoEnabled && (Object.keys(formData) as (keyof FormData)[]).some(
    (champ) => formData[champ] !== reference[champ],
  );
  const { abandonDemande, demanderFermeture, continuerSaisie, abandonner } = useQuestionDAbandonDeModale({
    actif: isOpen,
    modifie,
    fermer: onClose,
    fermerSiIntact,
  });

  // P-148, lot 3 : mener depuis la vue d'ensemble. Une saisie modifiée retient
  // la destination le temps de la question d'abandon (B-1392) ; la fenêtre ne
  // se ferme que si la coque a accepté l'ouverture.
  const [destinationEnAttente, setDestinationEnAttente] = useState<DestinationDuTravail | null>(null);
  const [navigationRetenue, setNavigationRetenue] = useState(false);
  const navigationRetenueRef = useRevelerALApparition(navigationRetenue);
  useEffect(() => {
    // La question refermée (Échap, « Continuer la saisie ») annule la
    // navigation qu'elle retenait.
    if (!abandonDemande) setDestinationEnAttente(null);
  }, [abandonDemande]);
  useEffect(() => {
    setNavigationRetenue(false);
  }, [isOpen, project]);

  function poursuivre(cible: DestinationDuTravail) {
    const refus = demanderLOuvertureDuTravail(cible);
    if (refus === null) {
      onClose();
      return;
    }
    // Constat 11 : un formulaire modifié sous la fenêtre a posé sa question,
    // invisible sous le voile. La fenêtre le dit. Une réponse en cours, la
    // coque l'annonce elle-même.
    if (refus === 'saisie-en-cours') setNavigationRetenue(true);
  }

  function mener(cible: DestinationDuTravail) {
    setNavigationRetenue(false);
    if (modifie) {
      setDestinationEnAttente(cible);
      demanderFermeture();
      return;
    }
    poursuivre(cible);
  }

  function abandonnerPuisMener() {
    const cible = destinationEnAttente;
    continuerSaisie();
    setDestinationEnAttente(null);
    if (cible) poursuivre(cible);
  }

  // La croix, le fond et « Annuler » demandent la fermeture : une navigation
  // retenue auparavant ne doit pas se glisser derrière cette question-là.
  function fermerLaFenetre() {
    setDestinationEnAttente(null);
    demanderFermeture();
  }

  const loadProjectFiles = useCallback(async (projectId: string, contexte: number) => {
    if (contexte !== fichiersContexteRef.current) return;
    const requete = ++fichiersRequeteRef.current;
    try {
      const { files, truncated } = await api.listProjectFiles(projectId);
      if (contexte !== fichiersContexteRef.current || requete !== fichiersRequeteRef.current) return;
      setProjectFiles(files);
      setFichiersTronques(truncated);
    } catch (err) {
      if (contexte === fichiersContexteRef.current && requete === fichiersRequeteRef.current) {
        console.error('Erreur chargement fichiers projet :', err);
      }
    }
  }, []);

  // Load contacts for linking
  useEffect(() => {
    if (isOpen) loadContacts();
  }, [isOpen]);

  const projectId = project?.id;
  useEffect(() => {
    const contexte = ++fichiersContexteRef.current;
    setProjectFiles([]);
    setFichiersTronques(false);
    setUploadingFile(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (isOpen && projectId) void loadProjectFiles(projectId, contexte);
    return () => { fichiersContexteRef.current += 1; };
  }, [isOpen, projectId, loadProjectFiles]);

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length || !project || useDemoStore.getState().enabled) return;

    const contexte = fichiersContexteRef.current;
    setUploadingFile(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        if (contexte !== fichiersContexteRef.current || useDemoStore.getState().enabled) return;
        await api.uploadProjectFile(file, project.id);
      }
      await loadProjectFiles(project.id, contexte);
    } catch (err) {
      if (contexte === fichiersContexteRef.current) {
        setError(err instanceof Error ? err.message : "Erreur lors de l'upload");
      }
    } finally {
      if (contexte === fichiersContexteRef.current) {
        setUploadingFile(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    }
  }, [project, loadProjectFiles]);

  async function confirmerSuppressionFichier() {
    const cible = fichierASupprimer;
    if (!cible || useDemoStore.getState().enabled) return;
    const contexte = fichiersContexteRef.current;
    try {
      await api.deleteFile(cible.id);
      if (contexte !== fichiersContexteRef.current) return;
      setProjectFiles((prev) => prev.filter((f) => f.id !== cible.id));
      setFichierASupprimer(null);
    } catch (err) {
      if (contexte === fichiersContexteRef.current) {
        setError(err instanceof Error ? err.message : 'Erreur suppression fichier');
      }
    }
  }

  function renoncerSuppressionFichier() {
    setFichierASupprimer(null);
    // Le focus revient d'où il venait : sans cela, il retombe sur le corps de
    // la modale et l'on perd sa place dans la liste.
    boutonSuppressionRef.current?.focus();
  }

  function getFileIcon(ext: string) {
    if (['.md', '.txt', '.docx', '.pdf'].includes(ext)) return <FileText className="w-4 h-4 text-accent" />;
    if (['.xlsx', '.csv'].includes(ext)) return <FileSpreadsheet className="w-4 h-4 text-agent-green" />;
    return <File className="w-4 h-4 text-text-muted" />;
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  }

  async function loadContacts() {
    setContactsCharges(false);
    setLoadingContacts(true);
    try {
      const data = await api.listContacts();
      setContacts(data);
      setContactsCharges(true);
    } catch (err) {
      console.error('Failed to load contacts:', err);
    } finally {
      setLoadingContacts(false);
    }
  }

  // Load project data when editing
  useEffect(() => {
    if (isOpen && project) {
      const charge = {
        name: project.name || '',
        description: project.description || '',
        contact_id: project.contact_id || '',
        status: project.status || 'active',
        budget: project.budget?.toString() || '',
        notes: project.notes || '',
        tags: Array.isArray(project.tags) ? project.tags.join(', ') : (project.tags || ''),
      };
      setFormData(charge);
      setReference(charge);
    } else if (isOpen) {
      setFormData(initialFormData);
      setReference(initialFormData);
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
    if (demoEnabled) return;
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  }

  async function handleSave() {
    if (useDemoStore.getState().enabled) return;
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
    if (!project || useDemoStore.getState().enabled) return;

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
    // B-1443 : sans prénom ni nom, l'entreprise est le nom (pas « Sans nom (SA) »).
    const parts = [contact.first_name, contact.last_name].filter(Boolean);
    if (parts.length === 0) return contactDisplayName(contact);
    const name = parts.join(' ');
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
            className={`fixed inset-0 bg-text/35 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            onClick={fermerLaFenetre}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={isEditing ? `Projet ${nomAffiche}` : 'Nouveau projet'}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[calc(100%-2rem)] max-w-lg bg-surface border border-border rounded-md ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex min-w-0 items-center gap-3">
                <div className="w-10 h-10 shrink-0 rounded-sm bg-accent-tint border border-accent flex items-center justify-center">
                  <Briefcase className="w-5 h-5 text-accent" />
                </div>
                <div className="min-w-0">
                  {/* P-148 : en édition, le focus initial est ici et non sur
                      « Nom » : l'ouverture ferait sinon défiler la fenêtre
                      jusqu'au formulaire et cacherait la vue d'ensemble.
                      « Consulter le projet » (démo) disparaît : le nom est le
                      titre, la lecture seule est dite juste dessous. */}
                  <h2
                    tabIndex={-1}
                    data-dialog-autofocus={isEditing ? true : undefined}
                    className="text-lg font-semibold text-text break-words outline-none"
                  >
                    {isEditing ? nomAffiche : 'Nouveau projet'}
                  </h2>
                  <p className="text-sm text-text-muted">
                    {demoEnabled ? 'Aperçu masqué en lecture seule' : isEditing ? 'Ce qu’il rassemble, puis ses informations' : 'Crée un nouveau projet'}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={fermerLaFenetre} aria-label="Fermer">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Content - Scrollable */}
            {/* B-1365 : Entrée dans un champ texte valide le formulaire. */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4" onKeyDown={entreeValide(() => void handleSave(), saving || demoEnabled)}>
              {demoEnabled && (
                <Alerte ton="attention" titre="Mode démo : lecture seule">
                  Désactive le mode démo dans les paramètres pour modifier ce projet.
                </Alerte>
              )}
              {/* P-148 : en édition, la fenêtre montre d'abord ce que le projet
                  rassemble, puis ses sections existantes, puis le formulaire. */}
              {isEditing && project && (
                <section aria-labelledby="projectmodal-ensemble-titre" className="space-y-4">
                  <h3 id="projectmodal-ensemble-titre" className="text-sm font-semibold text-text">Ce que rassemble ce projet</h3>
                  {navigationRetenue && (
                    <Alerte ref={navigationRetenueRef} ton="attention" icone={<AlertCircle className="w-4 h-4" />}>
                      Un formulaire modifié, sous cette fenêtre, attend ta réponse : ferme la fenêtre pour y répondre, puis rouvre le projet.
                    </Alerte>
                  )}
                  <ProjectEnsembleSection projectId={project.id} masquer={maskText} onMener={mener} />
                  {/* P-153 : les livrables du projet, ajoutables sans changer de vue. */}
                  <ProjectDeliverablesSection projectId={project.id} lectureSeule={demoEnabled} masquer={maskText} />

                  {/* Fichiers du projet (visible uniquement en édition) */}
                  <div className="space-y-2">
                    <label className="text-sm text-text-muted flex items-center gap-2">
                      <Upload className="w-4 h-4" />
                      Fichiers du projet
                    </label>
                    {/* Liste des fichiers */}
                    {fichiersTronques && (
                      <p role="alert" className="text-sm text-warning">
                        Liste incomplète : seuls les fichiers les plus récents sont affichés.
                      </p>
                    )}
                    {projectFiles.length > 0 && (
                      <div className="space-y-1">
                        {projectFiles.map((f) => (
                          <div
                            key={f.id}
                            className="flex items-center gap-2 px-3 py-2 bg-surface-2 rounded-md border border-border"
                          >
                            {getFileIcon(f.extension)}
                            <span className="flex-1 text-sm text-text truncate">{maskText(f.name)}</span>
                            <span className="text-xs text-text-muted">{formatFileSize(f.size)}</span>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              disabled={demoEnabled}
                              onClick={(event) => {
                                boutonSuppressionRef.current = event.currentTarget;
                                setFichierASupprimer(f);
                              }}
                              className="text-text-muted hover:text-error"
                              aria-label={`Supprimer le fichier ${maskText(f.name)}`}
                              title={`Supprimer le fichier ${maskText(f.name)}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
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
                      disabled={demoEnabled}
                    />
                    <Button
                      variant="ghost"
                      className="w-full border border-dashed border-border"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingFile || demoEnabled}
                    >
                      {uploadingFile ? (
                        <><Spinner taille="bouton" className="mr-2" />Upload en cours...</>
                      ) : (
                        <><Upload className="w-4 h-4 mr-2" />Ajouter un fichier (.md, .xlsx, .pdf, .docx)</>
                      )}
                    </Button>
                  </div>

                  {/* Dossier synchronisé (0.45) - visible uniquement en édition */}
                  <ProjectSyncSection projectId={project.id} maskDisplayText={maskText} />
                </section>
              )}

              {isEditing && (
                <h3 className="text-sm font-semibold text-text">Informations du projet</h3>
              )}
              {/* Name : le focus initial en création seulement (P-148). */}
              <FormField label="Nom du projet" htmlFor="projectmodal-nom-du-projet" required>
                <Input id="projectmodal-nom-du-projet" data-dialog-autofocus={isEditing ? undefined : true}
                  type="text"
                  value={demoEnabled && formData.name ? maskProject({ id: project?.id ?? '', name: formData.name }).name : formData.name}
                  readOnly={demoEnabled}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Refonte site web"
                />
              </FormField>

              {/* Description */}
              <FormField label="Description" htmlFor="projectmodal-description">
                <Textarea id="projectmodal-description"
                  value={maskText(formData.description)}
                  readOnly={demoEnabled}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Description du projet..."
                  rows={3}
                />
              </FormField>

              {/* Status */}
              <fieldset disabled={demoEnabled}>
                <Segments
                  label="Statut"
                  options={STATUS_OPTIONS}
                  valeur={formData.status}
                  onChange={(value) => handleChange('status', value)}
                />
              </fieldset>

              {/* Contact link */}
              <FormField label="Contact associé" htmlFor="projectmodal-contact-associe">
                <Select id="projectmodal-contact-associe"
                  value={formData.contact_id}
                  onChange={(e) => handleChange('contact_id', e.target.value)}
                  disabled={loadingContacts || demoEnabled}
                  options={[
                    { value: '', label: 'Aucun contact' },
                    ...contacts.map((contact) => ({ value: contact.id, label: getContactDisplayName(maskContact(contact)) })),
                  ]}
                />
                {loadingContacts && (
                  <p role="status" className="text-sm text-text-muted flex items-center gap-1">
                    <Spinner taille="ligne" />
                    Chargement des contacts...
                  </p>
                )}
              </FormField>

              {/* Budget */}
              <FormField label="Budget (€)" htmlFor="projectmodal-budget">
                <Input id="projectmodal-budget"
                  type="number"
                  value={formData.budget}
                  readOnly={demoEnabled}
                  onChange={(e) => handleChange('budget', e.target.value)}
                  placeholder="5000"
                  min="0"
                  step="100"
                />
              </FormField>

              {/* Notes */}
              <FormField label="Notes" htmlFor="projectmodal-notes">
                <Textarea id="projectmodal-notes"
                  value={maskText(formData.notes)}
                  readOnly={demoEnabled}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Notes internes sur le projet..."
                  rows={3}
                />
              </FormField>

              {/* Tags */}
              <FormField label="Tags (séparés par des virgules)" htmlFor="projectmodal-tags-separes-par-des-virgule">
                <Input id="projectmodal-tags-separes-par-des-virgule"
                  type="text"
                  value={maskText(formData.tags)}
                  readOnly={demoEnabled}
                  onChange={(e) => handleChange('tags', e.target.value)}
                  placeholder="web, design, urgent"
                />
              </FormField>

              {/* Error */}
              {error && (
                <div ref={erreurRef}>
                  <Alerte icone={<AlertCircle className="w-4 h-4" />}>{maskText(error)}</Alerte>
                </div>
              )}

              {/* Suppression d'un fichier joint : confirmation en ligne */}
              {fichierASupprimer && (
                <div ref={confirmationFichierRef} className="flex items-center gap-2 px-3 py-3 bg-[var(--color-error-tint)] border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-error font-medium">
                      Supprimer « {maskText(fichierASupprimer.name)} » ?
                    </p>
                    <p className="text-sm text-error">Cette action est irréversible.</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
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
                      disabled={demoEnabled}
                    >
                      Supprimer définitivement
                    </Button>
                  </div>
                </div>
              )}

              {/* Delete confirmation */}
              {showDeleteConfirm && (
                <div ref={confirmationRef} className="flex items-center gap-2 px-3 py-3 bg-error/10 border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-error font-medium">Supprimer ce projet ?</p>
                    <p className="text-sm text-error">Cette action est irréversible.</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
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
                      disabled={deleting || demoEnabled}
                    >
                      {deleting ? <Spinner taille="bouton" /> : 'Supprimer'}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-t border-border/50 shrink-0">
              <div>
                {isEditing && !showDeleteConfirm && (
                  <Button
                    ref={supprimerRef}
                    variant="ghost"
                    className="text-error hover:text-error hover:bg-error/10"
                    onClick={() => setShowDeleteConfirm(true)}
                    disabled={demoEnabled}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Supprimer
                  </Button>
                )}
              </div>
              {abandonDemande && (
                <div className="flex w-full flex-wrap items-center gap-2 rounded-sm border border-warning/40 bg-[var(--color-warning-tint)] px-3 py-2">
                  <p role="alert" className="flex-1 text-sm font-semibold text-text">Abandonner les modifications ?</p>
                  <Button variant="ghost" size="md" onClick={continuerSaisie}>Continuer la saisie</Button>
                  <Button variant="danger" size="md" onClick={destinationEnAttente ? abandonnerPuisMener : abandonner}>Abandonner</Button>
                </div>
              )}
              <div className="flex flex-wrap gap-3 max-[840px]:basis-full [&>button]:max-[840px]:flex-1">
                <Button variant="ghost" onClick={fermerLaFenetre}>
                  Annuler
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSave}
                  disabled={saving || demoEnabled}
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
