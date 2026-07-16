/**
 * THERESE v2 - Profile Step
 *
 * Second step of the onboarding wizard - Configure user profile.
 */

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { User, Upload, AlertCircle, Loader2 } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import * as api from '../../services/api';
import { Button } from '../ui/Button';

interface ProfileStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function ProfileStep({ onNext, onBack }: ProfileStepProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const savingRef = useRef(false);
  const continueTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [profileForm, setProfileForm] = useState({
    name: '',
    nickname: '',
    company: '',
    role: '',
    email: '',
    location: '',
    context: '',
  });

  useEffect(() => () => {
    if (continueTimerRef.current) clearTimeout(continueTimerRef.current);
  }, []);

  async function handleImportClaudeMd() {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Markdown', extensions: ['md'] }],
      });

      if (selected && typeof selected === 'string') {
        setLoading(true);
        setError(null);
        const importedProfile = await api.importClaudeMd(selected);
        setProfileForm({
          name: importedProfile.name || '',
          nickname: importedProfile.nickname || '',
          company: importedProfile.company || '',
          role: importedProfile.role || '',
          email: importedProfile.email || '',
          location: importedProfile.location || '',
          context: importedProfile.context || '',
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'import");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveAndContinue() {
    if (savingRef.current) return;
    if (!profileForm.name.trim()) {
      setError('Le nom est obligatoire');
      setSaveState('error');
      return;
    }

    savingRef.current = true;
    setLoading(true);
    setError(null);
    setSaveState('saving');
    let saved = false;

    try {
      await api.setProfile({
        name: profileForm.name,
        nickname: profileForm.nickname,
        company: profileForm.company,
        role: profileForm.role,
        email: profileForm.email,
        location: profileForm.location,
        context: profileForm.context,
      });
      saved = true;
      setSaveState('success');
      continueTimerRef.current = setTimeout(onNext, 650);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
      setSaveState('error');
    } finally {
      setLoading(false);
      if (!saved) savingRef.current = false;
    }
  }

  function handleSkip() {
    onNext();
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col px-8 py-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
            <User className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-text">Ton profil</h2>
            <p className="text-sm text-text-muted">THÉRÈSE utilisera ces infos pour mieux te répondre</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={handleImportClaudeMd} disabled={loading}>
          <Upload className="w-4 h-4 mr-2" />
          Importer THÉRÈSE.md
        </Button>
      </div>

      {/* Info stockage */}
      <p className="text-xs text-text-muted mb-4 px-1">
        Ces informations sont stockées localement dans ~/.therese/ et ne quittent jamais ta machine.
      </p>

      {/* Form */}
      <div className="space-y-4 flex-1 overflow-y-auto">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="profile-name" className="text-xs text-text-muted mb-1 block">Nom complet *</label>
            <input
              id="profile-name"
              type="text"
              value={profileForm.name}
              onChange={(e) => {
                setProfileForm((prev) => ({ ...prev, name: e.target.value }));
                setError(null);
                setSaveState('idle');
              }}
              placeholder="Ton nom complet"
              className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="profile-nickname" className="text-xs text-text-muted mb-1 block">Surnom</label>
            <input
              id="profile-nickname"
              type="text"
              value={profileForm.nickname}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, nickname: e.target.value }))}
              placeholder="Ton surnom"
              className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="profile-company" className="text-xs text-text-muted mb-1 block">Entreprise</label>
            <input
              id="profile-company"
              type="text"
              value={profileForm.company}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="Ton entreprise"
              className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="profile-role" className="text-xs text-text-muted mb-1 block">Rôle</label>
            <input
              id="profile-role"
              type="text"
              value={profileForm.role}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, role: e.target.value }))}
              placeholder="Ton rôle"
              className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="profile-email" className="text-xs text-text-muted mb-1 block">Email</label>
            <input
              id="profile-email"
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="ton@email.com"
              className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
          <div>
            <label htmlFor="profile-location" className="text-xs text-text-muted mb-1 block">Localisation</label>
            <input
              id="profile-location"
              type="text"
              value={profileForm.location}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, location: e.target.value }))}
              placeholder="Ta ville"
              className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan"
            />
          </div>
        </div>

        <div>
          <label htmlFor="profile-context" className="text-xs text-text-muted mb-1 block">
            Contexte additionnel
          </label>
          <p className="text-xs text-text-muted mb-1.5">
            Ces informations sont injectées dans le contexte de l'IA pour personnaliser ses réponses.
          </p>
          <textarea
            id="profile-context"
            value={profileForm.context}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, context: e.target.value }))}
            placeholder="Ex : Je propose des formations IA pour TPE. Mon offre phare est FORGER (490 € HT, 2h30)..."
            rows={3}
            className="w-full px-3 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan resize-none"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-error-tint)] border border-error/40 rounded-lg" role="alert">
            <AlertCircle className="w-4 h-4 text-error" />
            <span className="text-sm text-error">{error}</span>
          </div>
        )}
        {saveState === 'success' && (
          <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-success-tint)] border border-success/40 rounded-lg" role="status">
            <span className="text-sm text-success">Profil enregistré. L’onboarding ne se relancera pas au prochain démarrage.</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-between mt-6 pt-4 border-t border-border/30">
        <Button variant="ghost" onClick={onBack} disabled={loading || saveState === 'success'} data-testid="onboarding-prev-btn">
          Retour
        </Button>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={handleSkip} disabled={loading || saveState === 'success'} data-testid="onboarding-skip-btn">
            Passer
          </Button>
          <Button
            variant="primary"
            onClick={handleSaveAndContinue}
            disabled={loading || saveState === 'success'}
            data-testid="onboarding-next-btn"
          >
            {saveState === 'success'
              ? 'Profil enregistré'
              : loading
                ? (<><Loader2 className="w-4 h-4 mr-2 animate-spin" />Enregistrement en cours...</>)
                : 'Continuer'}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
