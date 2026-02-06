// Onglet Profil utilisateur - Paramètres THÉRÈSE
// Extraction depuis SettingsModal.tsx pour modularité

import { User, Upload, Check, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

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
  // Réservé pour usage futur (bouton Sauvegarder explicite)
  void _saving;
  void _onSave;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <User className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Ton profil</h3>
            <p className="text-xs text-text-muted">THÉRÈSE utilisera ces infos pour te répondre</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onImport}>
          <Upload className="w-4 h-4 mr-2" />
          Importer
        </Button>
      </div>

      {/* Statut du profil */}
      {profile ? (
        <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
          <Check className="w-4 h-4 text-green-400" />
          <span className="text-sm text-green-400">Profil configuré : {profile.display_name}</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <AlertCircle className="w-4 h-4 text-yellow-400" />
          <span className="text-sm text-yellow-400">Profil non configuré - Configure ton identité</span>
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

        <div>
          <label htmlFor="settings-profile-context" className="text-xs text-text-muted mb-1 block">Contexte additionnel</label>
          <textarea
            id="settings-profile-context"
            value={profileForm.context}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, context: e.target.value }))}
            placeholder="Infos supplémentaires sur ton activité, tes projets en cours..."
            rows={3}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan resize-none"
          />
        </div>
      </div>

      {/* Erreur */}
      {error && (
        <p className="text-sm text-red-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}

      {/* Succès */}
      {saved && (
        <p className="text-sm text-green-400 flex items-center gap-1">
          <Check className="w-3 h-3" />
          Profil enregistré
        </p>
      )}

      {/* Texte d'aide */}
      <p className="text-xs text-text-muted">
        Tu peux aussi importer ton profil depuis un fichier THERESE.md
      </p>
    </div>
  );
}
