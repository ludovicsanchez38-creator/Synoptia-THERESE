// Onglet Profil utilisateur - Paramètres THÉRÈSE
// Extraction depuis SettingsModal.tsx pour modularité

import { useState, useRef, useCallback } from 'react';
import { User, Upload, Check, AlertCircle, Eye, FileText, X, Save, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { useDemoStore } from '../../stores/demoStore';
import * as api from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

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
  error: string | null;
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
  error,
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

  // US-013 : la modale THERESE.md est en state local (invisible pour resolveEscape) :
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-[6px] bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
            <User className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-medium text-text">Ton profil</h3>
            <p className="text-xs text-text-muted">THÉRÈSE utilisera ces infos pour te répondre</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={openMdModal}>
            <FileText className="w-4 h-4 mr-2" />
            Voir THERESE.md
          </Button>
          <Button variant="ghost" size="sm" onClick={onImport}>
            <Upload className="w-4 h-4 mr-2" />
            Importer
          </Button>
        </div>
      </div>

      {/* Modal THERESE.md */}
      {mdModalOpen && (
        <div className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center bg-black/60`}>
          <div
            ref={mdDialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Aperçu THERESE.md"
            className="w-full max-w-2xl mx-4 bg-surface border border-border rounded-xl shadow-2xl flex flex-col max-h-[80vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border/50">
              <div>
                <h3 className="font-medium text-text flex items-center gap-2">
                  <FileText className="w-4 h-4 text-accent-cyan" />
                  THERESE.md
                </h3>
                {mdPath && (
                  <p className="text-xs text-text-muted mt-0.5">{mdPath}</p>
                )}
              </div>
              <button
                onClick={closeMdModal}
                className="p-1 rounded-lg hover:bg-border/30 text-text-muted hover:text-text transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Corps */}
            <div className="flex-1 overflow-y-auto p-5">
              {mdLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 text-accent-cyan animate-spin" />
                  <span className="ml-2 text-text-muted">Chargement...</span>
                </div>
              ) : (
                <textarea
                  value={mdContent}
                  onChange={(e) => {
                    setMdContent(e.target.value);
                    setMdSaved(false);
                  }}
                  className="w-full h-80 px-4 py-3 bg-background/80 border border-border/50 rounded-lg text-sm text-text font-mono resize-y focus:outline-none focus:ring-2 focus:ring-accent-cyan"
                  placeholder="# Mon contexte personnel&#10;&#10;Écris ici les informations que THÉRÈSE doit connaître sur toi..."
                />
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-border/50">
              <div className="flex items-center gap-2">
                {mdError && (
                  <span className="text-sm text-error flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {mdError}
                  </span>
                )}
                {mdSaved && (
                  <span className="text-sm text-success flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Sauvegardé
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={closeMdModal}>
                  Fermer
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={saveMdContent}
                  disabled={mdSaving || mdLoading}
                >
                  {mdSaving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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

      {/* Statut du profil */}
      {profile ? (
        <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-success-tint)] border border-success/40 rounded-lg">
          <Check className="w-4 h-4 text-success" />
          <span className="text-sm text-success">Profil configuré : {profile.display_name}</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-warning-tint)] border border-warning/40 rounded-lg">
          <AlertCircle className="w-4 h-4 text-warning" />
          <span className="text-sm text-warning">Profil non configuré - Configure ton identité</span>
        </div>
      )}

      {/* Champs du formulaire */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="settings-profile-name" className="text-xs text-text-muted mb-1 block">Nom complet *</label>
            <input
              id="settings-profile-name"
              type="text"
              value={profileForm.name}
              onChange={(e) => {
                setProfileForm((prev) => ({ ...prev, name: e.target.value }));
                setError(null);
              }}
              placeholder="Ludovic Sanchez"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="settings-profile-nickname" className="text-xs text-text-muted mb-1 block">Surnom</label>
            <input
              id="settings-profile-nickname"
              type="text"
              value={profileForm.nickname}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, nickname: e.target.value }))}
              placeholder="Ludo"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="settings-profile-company" className="text-xs text-text-muted mb-1 block">Entreprise</label>
            <input
              id="settings-profile-company"
              type="text"
              value={profileForm.company}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="Synoptïa"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="settings-profile-role" className="text-xs text-text-muted mb-1 block">Rôle</label>
            <input
              id="settings-profile-role"
              type="text"
              value={profileForm.role}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, role: e.target.value }))}
              placeholder="Entrepreneur IA"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="settings-profile-email" className="text-xs text-text-muted mb-1 block">Email</label>
            <input
              id="settings-profile-email"
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="ludo@synoptia.fr"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="settings-profile-location" className="text-xs text-text-muted mb-1 block">Localisation</label>
            <input
              id="settings-profile-location"
              type="text"
              value={profileForm.location}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, location: e.target.value }))}
              placeholder="Manosque, France"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>

        {/* Facturation */}
        <div>
          <label htmlFor="settings-profile-address" className="text-xs text-text-muted mb-1 block">Adresse (facturation)</label>
          <input
            id="settings-profile-address"
            type="text"
            value={profileForm.address}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, address: e.target.value }))}
            placeholder="294 Montée des Genêts, 04100 Manosque"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="settings-profile-siren" className="text-xs text-text-muted mb-1 block">SIREN</label>
            <input
              id="settings-profile-siren"
              type="text"
              value={profileForm.siren}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, siren: e.target.value }))}
              placeholder="991 606 781"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="settings-profile-tva" className="text-xs text-text-muted mb-1 block">TVA intracommunautaire</label>
            <input
              id="settings-profile-tva"
              type="text"
              value={profileForm.tva_intra}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, tva_intra: e.target.value }))}
              placeholder="FR 08 991 606 781"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
        </div>

        {/* P0-PROD-2 : identité émetteur (requise pour une facture conforme) */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="settings-profile-siret" className="text-xs text-text-muted mb-1 block">SIRET (requis pour facturer)</label>
            <input
              id="settings-profile-siret"
              type="text"
              value={profileForm.siret}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, siret: e.target.value }))}
              placeholder="991 606 781 00011"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="settings-profile-ape" className="text-xs text-text-muted mb-1 block">Code APE / NAF</label>
            <input
              id="settings-profile-ape"
              type="text"
              value={profileForm.code_ape}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, code_ape: e.target.value }))}
              placeholder="6202A"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
        </div>

        <div>
          <label htmlFor="settings-profile-nda" className="text-xs text-text-muted mb-1 block">N° de déclaration d'activité (organisme de formation)</label>
          <input
            id="settings-profile-nda"
            type="text"
            value={profileForm.nda}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, nda: e.target.value }))}
            placeholder="93 04 01236 04"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
          />
        </div>

        <div>
          <label htmlFor="settings-profile-context" className="text-xs text-text-muted mb-1 block">
            Contexte additionnel
          </label>
          <p className="text-xs text-text-muted/60 mb-1.5">
            Ces informations sont injectées dans le contexte de l'IA pour personnaliser ses réponses (offres, secteur, projets en cours...).
          </p>
          <textarea
            id="settings-profile-context"
            value={profileForm.context}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, context: e.target.value }))}
            placeholder="Ex : Je propose des formations IA pour TPE. Mon offre phare est FORGER (490 € HT, 2h30)..."
            rows={3}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan resize-none"
          />
        </div>
      </div>

      {/* Erreur */}
      {error && (
        <p className="text-sm text-error flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}

      {/* Succès */}
      {saved && (
        <p className="text-sm text-success flex items-center gap-1">
          <Check className="w-3 h-3" />
          Profil enregistré
        </p>
      )}

      {/* Texte d'aide */}
      <p className="text-xs text-text-muted">
        Tu peux aussi importer ton profil depuis un fichier THERESE.md
      </p>

      {/* Mode Démo */}
      <DemoModeSection />
    </div>
  );
}

// Section Mode Démo - masque les données réelles
function DemoModeSection() {
  const demoEnabled = useDemoStore((s) => s.enabled);
  const toggleDemo = useDemoStore((s) => s.toggle);
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  return (
    <div className="space-y-3 pt-4 border-t border-border/30">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-[6px] flex items-center justify-center bg-accent-tint border-[1.5px] border-[var(--btn-ink)]">
          <Eye className="w-5 h-5 text-accent-cyan" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-text">Mode Démo</h3>
          <p className="text-xs text-text-muted">
            Masque les noms et données clients par des personas fictifs
          </p>
        </div>
        <button
          onClick={toggleDemo}
          className={`relative w-11 h-6 rounded-full transition-colors ${
            demoEnabled ? 'bg-accent-cyan' : 'bg-border'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
              demoEnabled ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {demoEnabled && (
        <div className="p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
          <span className="text-sm text-accent-cyan">
            Mode démo actif - {isMac ? '⌘' : 'Ctrl'}⇧D pour basculer
          </span>
        </div>
      )}
    </div>
  );
}
