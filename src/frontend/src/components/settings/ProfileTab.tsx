// Onglet Profil utilisateur - Paramètres THÉRÈSE
// Extraction depuis SettingsModal.tsx pour modularité

import { useState, useRef, useCallback } from 'react';
import { User, Upload, Check, AlertCircle, Eye, FileText, X, Save } from 'lucide-react';
import { Button } from '../ui/Button';
import { Carte, CarteTete } from '../ui/Carte';
import { Etiquette } from '../ui/Etiquette';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { useDemoStore } from '../../stores/demoStore';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { Spinner } from '../ui/Spinner';

// Types des props du formulaire profil
export interface ProfileFormData {
  name: string;
  nickname: string;
  company: string;
  role: string;
  email: string;
  location: string;
  address: string;
  siren: string;
  tva_intra: string;
  siret: string;
  code_ape: string;
  nda: string;
  context: string;
}

export interface ProfileTabProps {
  profileForm: ProfileFormData;
  setProfileForm: (form: ProfileFormData | ((prev: ProfileFormData) => ProfileFormData)) => void;
  profile: api.UserProfile | null;
  saving: boolean;
  saved: boolean;
  /**
   * Lot 9 : plus de prop `error`. La coque rend l'erreur, et elle seule : la
   * passer ici la montait une seconde fois, en deux `role="alert"` pour un même
   * message. `setError` reste, elle sert aux remises à zéro.
   */
  setError: (e: string | null) => void;
  onSave: () => void;
  onImport: () => void;
}

export function ProfileTab({
  profileForm,
  setProfileForm,
  profile,
  saving: _saving,
  saved,
  setError,
  onSave: _onSave,
  onImport,
}: ProfileTabProps) {
  void _saving;
  void _onSave;

  // État modal THERESE.md
  const [mdModalOpen, setMdModalOpen] = useState(false);
  const [mdContent, setMdContent] = useState('');
  const [mdPath, setMdPath] = useState('');
  const [mdLoading, setMdLoading] = useState(false);
  const [mdSaving, setMdSaving] = useState(false);
  const [mdSaved, setMdSaved] = useState(false);
  const [mdError, setMdError] = useState<string | null>(null);

  // US-013 : la modale THERESE.md est en state local (invisible pour cascade Échap de la coque) :
  // piège de focus + Échap gérés ici. closeMdModal stable (useCallback) pour ne pas
  // réarmer le piège à chaque re-render de l'onglet (frappe dans le formulaire).
  const mdDialogRef = useRef<HTMLDivElement>(null);
  const closeMdModal = useCallback(() => setMdModalOpen(false), []);
  useDialogFocusTrap(mdDialogRef, { active: mdModalOpen, onEscape: closeMdModal });

  const openMdModal = async () => {
    setMdModalOpen(true);
    setMdLoading(true);
    setMdError(null);
    setMdSaved(false);
    try {
      const data = await api.getThereseMd();
      setMdContent(data.content);
      setMdPath(data.path);
    } catch (_err) {
      setMdError('Impossible de charger THERESE.md');
    } finally {
      setMdLoading(false);
    }
  };

  const saveMdContent = async () => {
    setMdSaving(true);
    setMdError(null);
    setMdSaved(false);
    try {
      await api.saveThereseMd(mdContent);
      setMdSaved(true);
    } catch (_err) {
      setMdError('Erreur lors de la sauvegarde');
    } finally {
      setMdSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Modal THERESE.md */}
      {mdModalOpen && (
        <div className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center bg-black/60`}>
          <div
            ref={mdDialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Aperçu THERESE.md"
            className="w-full max-w-2xl mx-4 bg-surface border border-border rounded-md shadow-2xl flex flex-col max-h-[80vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border/50">
              <div>
                <h3 className="font-medium text-text flex items-center gap-2">
                  <FileText className="w-4 h-4 text-accent-cyan-ink" />
                  THERESE.md
                </h3>
                {mdPath && (
                  <p className="text-xs text-text-muted mt-0.5">{mdPath}</p>
                )}
              </div>
              <button
                onClick={closeMdModal}
                className="p-1 rounded-md hover:bg-border/30 text-text-muted hover:text-text transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Corps */}
            <div className="flex-1 overflow-y-auto p-5">
              {mdLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Spinner taille="zone" className="text-accent-cyan-ink" />
                  <span className="ml-2 text-text-muted">Chargement...</span>
                </div>
              ) : (
                <textarea aria-label="Contenu du profil THERESE.md"
                  value={mdContent}
                  onChange={(e) => {
                    setMdContent(e.target.value);
                    setMdSaved(false);
                  }}
                  className="w-full h-80 px-4 py-3 bg-background/80 border border-border/50 rounded-md text-sm text-text font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="# Mon contexte personnel&#10;&#10;Écris ici les informations que THÉRÈSE doit connaître sur toi..."
                />
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-border/50">
              <div className="flex items-center gap-2">
                {mdError && (
                  <span role="alert" className="text-sm text-error flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {mdError}
                  </span>
                )}
                {mdSaved && (
                  <span role="status" className="text-sm text-success flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Sauvegardé
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="md" onClick={closeMdModal}>
                  Fermer
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={saveMdContent}
                  disabled={mdSaving || mdLoading}
                >
                  {mdSaving ? (
                    <Spinner taille="bouton" className="mr-2" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  Sauvegarder
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Carte identité. Le geste « Importer THERESE.md » est en tête, nommé :
          la phrase « Tu peux aussi importer ton profil depuis un fichier
          THERESE.md », posée en 12 px au pied de la rubrique, redisait ce que ce
          bouton dit déjà, en plus petit et plus loin. Elle est retirée. */}
      <Carte as="section" aria-labelledby="settings-profil-title">
        <CarteTete
          idTitre="settings-profil-title"
          icone={<User className="h-[18px] w-[18px]" />}
          titre="Profil"
          meta="Ce que Thérèse sait de toi pour te répondre juste. Modifiable à tout moment, exportable, effaçable."
          actions={(
            <>
              <Button variant="ghost" size="md" onClick={openMdModal}>
                <FileText className="mr-2 h-[18px] w-[18px]" />
                Voir THERESE.md
              </Button>
              <Button variant="secondary" size="md" onClick={onImport}>
                <Upload className="mr-2 h-[18px] w-[18px]" />
                Importer THERESE.md
              </Button>
            </>
          )}
        />

        {/* `whitespace-normal` : la pilule refuse le retour à la ligne par
            défaut, or ces deux chaînes sont longues (45 caractères pour l'une,
            un nom de longueur inconnue pour l'autre) et déborderaient en petite
            largeur ou en grande taille de police. */}
        <div className="px-4 pb-2">
          {profile ? (
            <Etiquette ton="succes" className="whitespace-normal">
              Profil configuré : {profile.display_name}
            </Etiquette>
          ) : (
            <Etiquette ton="attention" className="whitespace-normal">
              Profil non configuré - Configure ton identité
            </Etiquette>
          )}
        </div>

        {/* Deux colonnes à partir de 1024 px, comme `.grille-2` du socle. */}
        <div className="grid grid-cols-1 min-[1024px]:grid-cols-2 gap-x-4 px-4 pb-4">
          <FormField label="Nom complet" htmlFor="settings-profile-name" required>
            <Input
              id="settings-profile-name"
              type="text"
              value={profileForm.name}
              onChange={(e) => {
                setProfileForm((prev) => ({ ...prev, name: e.target.value }));
                setError(null);
              }}
              placeholder="Marie Exemple"
            />
          </FormField>
          <FormField label="Surnom" htmlFor="settings-profile-nickname">
            <Input
              id="settings-profile-nickname"
              type="text"
              value={profileForm.nickname}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, nickname: e.target.value }))}
              placeholder="Marie"
            />
          </FormField>
          <FormField label="Entreprise" htmlFor="settings-profile-company">
            <Input
              id="settings-profile-company"
              type="text"
              value={profileForm.company}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="Exemple SARL"
            />
          </FormField>
          <FormField label="Rôle" htmlFor="settings-profile-role">
            <Input
              id="settings-profile-role"
              type="text"
              value={profileForm.role}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, role: e.target.value }))}
              placeholder="Entrepreneur IA"
            />
          </FormField>
          <FormField label="Email" htmlFor="settings-profile-email">
            <Input
              id="settings-profile-email"
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="marie@exemple.fr"
            />
          </FormField>
          <FormField label="Localisation" htmlFor="settings-profile-location">
            <Input
              id="settings-profile-location"
              type="text"
              value={profileForm.location}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, location: e.target.value }))}
              placeholder="Manosque, France"
            />
          </FormField>
        </div>

        {/* Hors de la grille, en pleine largeur : sous 1024 px la grille n'a
            qu'une colonne, et un `col-span-2` y créerait une seconde colonne
            implicite qui casserait la mise en page. */}
        <div className="px-4 pb-4">
          <FormField
            label="Ce que Thérèse doit savoir"
            htmlFor="settings-profile-context"
            description="Ces informations sont injectées dans le contexte de l'IA pour personnaliser ses réponses (offres, secteur, projets en cours...)."
          >
            <Textarea
              id="settings-profile-context"
              value={profileForm.context}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, context: e.target.value }))}
              placeholder="Ex : Je propose des formations IA pour TPE. Mon offre phare est FORGER (490 € HT, 2h30)..."
              rows={3}
              className="resize-none"
            />
          </FormField>
        </div>

        {saved && (
          <p role="status" className="flex items-center gap-1 px-4 pb-4 text-sm text-success">
            <Check className="h-4 w-4" />
            Profil enregistré
          </p>
        )}
      </Carte>

      {/* Seule occurrence des champs de facturation, éditables. */}
      <Carte as="section" aria-labelledby="settings-emetteur-title">
        <CarteTete
          idTitre="settings-emetteur-title"
          icone={<FileText className="h-[18px] w-[18px]" />}
          titre="Profil émetteur des factures"
          meta="SIRET, TVA, adresse et mentions légales, utilisés sur chaque devis et facture."
        />

        <div className="px-4 pb-4">
          <FormField label="Adresse (facturation)" htmlFor="settings-profile-address">
            <Input
              id="settings-profile-address"
              type="text"
              value={profileForm.address}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, address: e.target.value }))}
              placeholder="12 rue de l'Exemple, 04100 Manosque"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 min-[1024px]:grid-cols-2 gap-x-4 px-4 pb-4">
          <FormField label="SIREN" htmlFor="settings-profile-siren">
            <Input
              id="settings-profile-siren"
              type="text"
              value={profileForm.siren}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, siren: e.target.value }))}
              placeholder="123 456 789"
            />
          </FormField>
          <FormField label="TVA intracommunautaire" htmlFor="settings-profile-tva">
            <Input
              id="settings-profile-tva"
              type="text"
              value={profileForm.tva_intra}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, tva_intra: e.target.value }))}
              placeholder="FR 00 123 456 789"
            />
          </FormField>
          <FormField label="SIRET (requis pour facturer)" htmlFor="settings-profile-siret">
            <Input
              id="settings-profile-siret"
              type="text"
              value={profileForm.siret}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, siret: e.target.value }))}
              placeholder="123 456 789 00010"
            />
          </FormField>
          <FormField label="Code APE / NAF" htmlFor="settings-profile-ape">
            <Input
              id="settings-profile-ape"
              type="text"
              value={profileForm.code_ape}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, code_ape: e.target.value }))}
              placeholder="0000Z"
            />
          </FormField>
        </div>

        <div className="px-4 pb-4">
          <FormField
            label="N° de déclaration d'activité (organisme de formation)"
            htmlFor="settings-profile-nda"
          >
            <Input
              id="settings-profile-nda"
              type="text"
              value={profileForm.nda}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, nda: e.target.value }))}
              placeholder="00 00 00000 00"
            />
          </FormField>
        </div>
      </Carte>

      {/* Mode Démo */}
      <DemoModeSection />
    </div>
  );
}

// Section Mode Démo - masque les données réelles
// Exporté pour que le test de périmètre (B-131) puisse lire ce que la section promet.
export function DemoModeSection() {
  const demoEnabled = useDemoStore((s) => s.enabled);
  const toggleDemo = useDemoStore((s) => s.toggle);
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  return (
    <div className="space-y-3 pt-4 border-t border-border/30" data-testid="mode-demo-section">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-sm flex items-center justify-center bg-accent-tint border-[1.5px] border-[var(--btn-ink)]">
          <Eye className="w-5 h-5 text-accent-cyan-ink" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-text">Mode Démo</h3>
          <p className="text-sm text-text-muted">
            Remplace par des personas fictifs les noms, sociétés et e-mails de tes fiches contacts
          </p>
        </div>
        {/* Sans `type`, ce bouton valait `submit` ; sans rôle ni nom, le
            lecteur d'écran annonçait « bouton », sans dire quoi ni dans quel
            état. Piste 40 x 24 et curseur 20, comme l'interrupteur du mode
            contributeur. */}
        <button
          type="button"
          role="switch"
          aria-checked={demoEnabled}
          aria-label="Mode démo"
          onClick={toggleDemo}
          className={`relative w-10 h-6 rounded-full transition-colors ${
            demoEnabled ? 'bg-accent' : 'bg-border'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-ink-on-fill rounded-full transition-transform ${
              demoEnabled ? 'translate-x-4' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {/* B-131 : le masque est bâti depuis les fiches contacts (et les projets
          quand une vue les a chargés). Un nom propre qu'aucune fiche ne porte
          lui est invisible, et l'utilisateur qui filme sa démonstration n'avait
          aucun moyen de le savoir : le réglage promettait « les données
          clients », sans dire où la promesse s'arrête. */}
      <p className="text-sm text-text-muted">
        Ce qui reste en clair : ce que tu as tapé toi-même ailleurs. Un nom de société
        écrit à la main dans le titre d'une tâche ou d'une conversation n'est dans aucune
        fiche contact, donc le masque ne le connaît pas. Relis l'écran avant de filmer.
      </p>

      {demoEnabled && (
        <p role="status" className="text-sm text-accent-cyan-ink">
          Mode démo actif - {isMac ? '⌘' : 'Ctrl'}⇧D pour basculer
        </p>
      )}
    </div>
  );
}
