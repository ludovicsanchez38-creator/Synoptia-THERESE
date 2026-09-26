import { useState, useEffect, useRef } from 'react';
import { X, User, Trash2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import { useContactsStore } from '../../stores/contactsStore';
import { useDemoStore } from '../../stores/demoStore';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { useQuestionDAbandonDeModale } from '../../hooks/useQuestionDAbandonDeModale';
import { useRendreLeFocusALaFermeture, useRevelerALApparition } from '../../hooks/useRevelerALApparition';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { entreeValide } from '../../lib/entreeValide';
import { gesteBloqueEnDemo } from '../../lib/gesteEnDemo';

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
  /** P-133 : AAAA-MM-JJ, vide sans relance. */
  next_follow_up: string;
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
  next_follow_up: '',
};

export function ContactModal({ isOpen, onClose, onSaved, contact }: ContactModalProps) {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  // B-1392 : la saisie telle que chargée, pour savoir si elle a changé.
  const [reference, setReference] = useState<FormData>(initialFormData);
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

  const isEditing = !!contact;
  // B-1080 : en démo, la liste passe la fiche déjà masquée. L'enregistrer
  // écrirait le persona fictif sur la vraie fiche : lecture seule, comme
  // ProjectModal (B-939). Adresse, notes et tags ne sont pas masqués par
  // maskContact, ils restent donc cachés.
  const demoEnabled = useDemoStore((s) => s.enabled);
  const MASQUE_DEMO = 'Masqué en démonstration';
  const affiche = (champ: 'address' | 'notes' | 'tags') =>
    demoEnabled && formData[champ] ? MASQUE_DEMO : formData[champ];

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la cascade de la coque (ConversationCanvasPrototype) via le store.
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
  });

  // Load contact data when editing
  useEffect(() => {
    if (isOpen && contact) {
      const chargee = {
        first_name: contact.first_name || '',
        last_name: contact.last_name || '',
        company: contact.company || '',
        email: contact.email || '',
        phone: contact.phone || '',
        address: contact.address || '',
        notes: contact.notes || '',
        tags: Array.isArray(contact.tags) ? contact.tags.join(', ') : (contact.tags || ''),
        // Le moteur rend le jour civil à 09:00 (echeance_de_relance) : on garde le jour.
        next_follow_up: /^\d{4}-\d{2}-\d{2}/.test(contact.next_follow_up ?? '') ? (contact.next_follow_up as string).slice(0, 10) : '',
      };
      setFormData(chargee);
      setReference(chargee);
    } else if (isOpen) {
      setFormData(initialFormData);
      setReference(initialFormData);
    }
    setError(null);
    setShowDeleteConfirm(false);
  }, [isOpen, contact]);

  function handleChange(field: keyof FormData, value: string) {
    if (demoEnabled) return;
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  }

  async function handleSave() {
    if (useDemoStore.getState().enabled) return;
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
        // P-133 : effacer la date efface la relance (null traverse le moteur).
        next_follow_up: formData.next_follow_up || null,
      };

      // Via le store unique : la création/édition se reflète aussitôt Mémoire ET CRM (P4).
      if (isEditing && contact) {
        // B-1391 : la version lue ; si la fiche a changé ailleurs (autre
        // onglet, chat), le moteur refuse au lieu d'écraser, et la saisie reste.
        await useContactsStore.getState().updateContact(contact.id, {
          ...payload,
          version_lue: contact.updated_at,
        });
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
    if (!contact || useDemoStore.getState().enabled) return;

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
            className={`fixed inset-0 bg-text/35 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            onClick={demanderFermeture}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={demoEnabled && isEditing ? 'Consulter le contact' : isEditing ? 'Modifier le contact' : 'Nouveau contact'}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[calc(100%-2rem)] max-w-lg bg-surface border border-border rounded-md ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-sm bg-accent-tint border border-accent flex items-center justify-center">
                  <User className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text">
                    {demoEnabled && isEditing ? 'Consulter le contact' : isEditing ? 'Modifier le contact' : 'Nouveau contact'}
                  </h2>
                  <p className="text-sm text-text-muted">
                    {demoEnabled && isEditing ? 'Aperçu masqué en lecture seule' : isEditing ? 'Modifie les informations du contact' : 'Ajoute un nouveau contact à ta mémoire'}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={demanderFermeture} aria-label="Fermer">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Content - Scrollable. */}
            {/* B-1365 : Entrée dans un champ texte valide le formulaire. */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4" onKeyDown={entreeValide(() => void handleSave(), saving || demoEnabled)}>
              {demoEnabled && (
                <Alerte ton="attention" titre="Mode démo : lecture seule">
                  Désactive le mode démo dans les paramètres pour {isEditing ? 'modifier ce contact' : 'créer un contact'}.
                </Alerte>
              )}
              {/* Name row */}
              <div className="grid grid-cols-2 gap-4">
                <FormField label="Prénom" htmlFor="contactmodal-prenom">
                  <Input id="contactmodal-prenom" readOnly={demoEnabled} data-dialog-autofocus
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => handleChange('first_name', e.target.value)}
                    placeholder="Jean"
                  />
                </FormField>
                <FormField label="Nom" htmlFor="contactmodal-nom">
                  <Input id="contactmodal-nom" readOnly={demoEnabled}
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => handleChange('last_name', e.target.value)}
                    placeholder="Dupont"
                  />
                </FormField>
              </div>

              {/* Company */}
              <FormField label="Entreprise" htmlFor="contactmodal-entreprise">
                <Input id="contactmodal-entreprise" readOnly={demoEnabled}
                  type="text"
                  value={formData.company}
                  onChange={(e) => handleChange('company', e.target.value)}
                  placeholder="Synoptïa"
                />
              </FormField>

              {/* Email */}
              <FormField label="Email" htmlFor="contactmodal-email">
                <Input id="contactmodal-email" readOnly={demoEnabled}
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  placeholder="jean@example.com"
                />
              </FormField>

              {/* Phone */}
              <FormField label="Téléphone" htmlFor="contactmodal-telephone">
                <Input id="contactmodal-telephone" readOnly={demoEnabled}
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange('phone', e.target.value)}
                  placeholder="Numéro de téléphone"
                />
              </FormField>

              {/* Adresse — B2 : sans elle, un devis part avec un destinataire
                  vide. Le champ existait en base et n'était saisissable nulle
                  part. */}
              <FormField label="Adresse" htmlFor="contactmodal-adresse">
                <Input id="contactmodal-adresse" readOnly={demoEnabled}
                  type="text"
                  value={affiche('address')}
                  onChange={(e) => handleChange('address', e.target.value)}
                  placeholder="Numéro et rue, code postal, ville"
                />
              </FormField>

              {/* Notes */}
              <FormField label="Notes" htmlFor="contactmodal-notes">
                <Textarea id="contactmodal-notes" readOnly={demoEnabled}
                  value={affiche('notes')}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Informations complémentaires..."
                  rows={3}
                />
              </FormField>

              {/* P-133 : la relance datée, lue par le brief de l'Accueil,
                  n'avait aucun champ ; seule une importation pouvait la poser. */}
              <FormField
                label="Prochaine relance"
                htmlFor="contactmodal-relance"
                description="Le jour venu, l’Accueil te propose de relancer cette personne."
              >
                <Input id="contactmodal-relance" readOnly={demoEnabled}
                  type="date"
                  value={formData.next_follow_up}
                  onChange={(e) => handleChange('next_follow_up', e.target.value)}
                />
              </FormField>

              {/* Tags */}
              <FormField label="Tags (séparés par des virgules)" htmlFor="contactmodal-tags-separes-par-des-virgule">
                <Input id="contactmodal-tags-separes-par-des-virgule" readOnly={demoEnabled}
                  type="text"
                  value={affiche('tags')}
                  onChange={(e) => handleChange('tags', e.target.value)}
                  placeholder="client, prospect, partenaire"
                />
              </FormField>

              {/* Error */}
              {error && (
                <div ref={erreurRef}>
                  <Alerte icone={<AlertCircle className="w-4 h-4" />}>{error}</Alerte>
                </div>
              )}

              {/* Delete confirmation */}
              {showDeleteConfirm && (
                <div ref={confirmationRef} className="flex items-center gap-2 px-3 py-3 bg-error/10 border border-error/20 rounded-md">
                  <AlertCircle className="w-4 h-4 text-error shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-error font-medium">Supprimer ce contact ?</p>
                    <p className="text-sm text-error">Cette action est irréversible.</p>
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
            <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-t border-border/50 shrink-0">
              <div>
                {isEditing && !showDeleteConfirm && (
                  <Button
                    ref={supprimerRef}
                    variant="ghost"
                    className="text-error hover:text-error hover:bg-error/10"
                    onClick={() => { if (!gesteBloqueEnDemo()) setShowDeleteConfirm(true); }}
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
                  <Button variant="danger" size="md" onClick={abandonner}>Abandonner</Button>
                </div>
              )}
              <div className="flex flex-wrap gap-3 max-[840px]:basis-full [&>button]:max-[840px]:flex-1">
                <Button variant="ghost" onClick={demanderFermeture}>
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

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
