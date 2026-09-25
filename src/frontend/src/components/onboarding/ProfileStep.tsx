/**
 * THERESE v2 - Profile Step
 *
 * Second step of the onboarding wizard - Configure user profile.
 */

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { User, Upload, AlertCircle, ChevronDown, Receipt } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import * as api from '../../services/api';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';

interface ProfileStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function ProfileStep({ onNext, onBack }: ProfileStepProps) {
  const [loading, setLoading] = useState(false);
  // B-611 : le chemin était écrit en dur (« ~/.therese/ ») alors que le
  // moteur peut écrire ailleurs (THERESE_DATA_DIR).
  const [dossierDeDonnees, setDossierDeDonnees] = useState<string | null>(null);
  useEffect(() => {
    let vivant = true;
    // Un module d'API partiellement simulé (tests) peut ne pas exposer cet appel.
    try {
      const lecture = api.getConfigStats();
      if (lecture && typeof lecture.then === 'function') {
        lecture.then((stats) => { if (vivant && stats?.data_dir) setDossierDeDonnees(stats.data_dir); }).catch(() => undefined);
      }
    } catch {
      /* dossier non affiché */
    }
    return () => { vivant = false; };
  }, []);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  // B-198 : distinct de `error`, qui porte aussi les échecs d'enregistrement.
  // Un champ ne se déclare pas en faute parce que le serveur a refusé.
  const [nomEnFaute, setNomEnFaute] = useState(false);
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
    address: '',
    siret: '',
    tva_intra: '',
  });
  // P-112 : la facturation se réglait ensuite, par une carte de l'Accueil puis
  // un défilement dans Paramètres. Volet facultatif, replié par défaut.
  const [factureAvecTherese, setFactureAvecTherese] = useState(false);

  useEffect(() => () => {
    if (continueTimerRef.current) clearTimeout(continueTimerRef.current);
  }, []);

  async function handleImportClaudeMd() {
    let selected: string | string[] | null;
    try {
      selected = await open({
        multiple: false,
        filters: [{ name: 'Markdown', extensions: ['md'] }],
      });
    } catch (err) {
      // B-773 : le pont natif n'a pas répondu. Son exception (« Cannot read
      // properties of undefined (reading 'invoke') ») n'est pas un message d'écran.
      console.error('Ouverture du sélecteur de fichier impossible:', err);
      setNomEnFaute(false);
      setError('La fenêtre de choix du fichier ne s’est pas ouverte. Redémarre THÉRÈSE, puis réessaie.');
      return;
    }
    try {
      if (selected && typeof selected === 'string') {
        setLoading(true);
        setError(null);
        const importedProfile = await api.importClaudeMd(selected);
        setProfileForm((prev) => ({
          name: importedProfile.name || '',
          nickname: importedProfile.nickname || '',
          company: importedProfile.company || '',
          role: importedProfile.role || '',
          email: importedProfile.email || '',
          location: importedProfile.location || '',
          context: importedProfile.context || '',
          address: importedProfile.address || prev.address,
          siret: importedProfile.siret || prev.siret,
          tva_intra: importedProfile.tva_intra || prev.tva_intra,
        }));
      }
    } catch (err) {
      // Le bandeau est partagé : un message qui ne parle pas du nom ne doit pas
      // rester désigné par le champ du nom (le sélecteur de fichier peut échouer
      // avant même que l'import commence).
      setNomEnFaute(false);
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
      setNomEnFaute(true);
      return;
    }
    setNomEnFaute(false);

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
        address: profileForm.address.trim(),
        siret: profileForm.siret.trim(),
        tva_intra: profileForm.tva_intra.trim(),
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
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent-tint">
            <User className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-text">Ton profil</h2>
            <p className="text-sm text-text-muted">THÉRÈSE utilisera ces infos pour mieux te répondre</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={handleImportClaudeMd} disabled={loading} className="max-[840px]:basis-full max-[840px]:justify-start">
          <Upload className="w-4 h-4 mr-2" />
          Importer un profil (THÉRÈSE.md)
        </Button>
      </div>

      {/* Info stockage. B-1345 : « ne quittent jamais ta machine » était faux
          avec un service en ligne (le profil accompagne chaque demande), et
          écrit en 12 px. */}
      <p className="text-sm text-text-muted mb-4 px-1">
        Ces informations sont stockées localement{dossierDeDonnees ? ` dans ${dossierDeDonnees}` : ''}. Avec un modèle local, elles restent sur ta machine ; avec un service en ligne, elles accompagnent tes demandes.
      </p>

      {/* Form */}
      <div className="space-y-4 flex-1 overflow-y-auto">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Nom complet" htmlFor="profile-name" required error={nomEnFaute && error ? error : undefined}>
            <Input
              id="profile-name"
              type="text"
              aria-label="Nom complet *"
              aria-required="true"
              value={profileForm.name}
              onChange={(e) => {
                setProfileForm((prev) => ({ ...prev, name: e.target.value }));
                setError(null);
                setSaveState('idle');
              }}
              placeholder="Ton nom complet"
              error={nomEnFaute && Boolean(error)}
            />
          </FormField>
          <FormField label="Surnom" htmlFor="profile-nickname">
            <Input
              id="profile-nickname"
              type="text"
              value={profileForm.nickname}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, nickname: e.target.value }))}
              placeholder="Ton surnom"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Entreprise" htmlFor="profile-company">
            <Input
              id="profile-company"
              type="text"
              value={profileForm.company}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="Ton entreprise"
            />
          </FormField>
          <FormField label="Rôle" htmlFor="profile-role">
            <Input
              id="profile-role"
              type="text"
              value={profileForm.role}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, role: e.target.value }))}
              placeholder="Ton rôle"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Email" htmlFor="profile-email">
            <Input
              id="profile-email"
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="ton@email.com"
            />
          </FormField>
          <FormField label="Localisation" htmlFor="profile-location">
            <Input
              id="profile-location"
              type="text"
              value={profileForm.location}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, location: e.target.value }))}
              placeholder="Ta ville"
            />
          </FormField>
        </div>

        <FormField
          label="Contexte additionnel"
          htmlFor="profile-context"
          description="Ces informations sont injectées dans le contexte de l'IA pour personnaliser ses réponses."
        >
          <Textarea
            id="profile-context"
            value={profileForm.context}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, context: e.target.value }))}
            placeholder="Ex : Je propose des formations IA pour TPE. Mon offre phare est FORGER (490 € HT, 2h30)..."
            rows={3}
            className="resize-none"
          />
        </FormField>

        <div className="rounded-md border border-border">
          <button
            type="button"
            aria-expanded={factureAvecTherese}
            aria-controls="profile-facturation"
            onClick={() => setFactureAvecTherese((ouvert) => !ouvert)}
            className="flex min-h-9 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium text-text hover:bg-surface-2 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <Receipt className="h-4 w-4 text-text-muted" aria-hidden="true" />
            <span className="flex-1">Je facture avec THÉRÈSE <span className="font-normal text-text-muted">(facultatif)</span></span>
            <ChevronDown className={`h-4 w-4 text-text-muted transition-transform ${factureAvecTherese ? 'rotate-180' : ''}`} aria-hidden="true" />
          </button>
          {factureAvecTherese && (
            <div id="profile-facturation" className="space-y-4 border-t border-border px-3 py-3">
              <p className="text-sm text-text-muted">
                Ces mentions s’impriment sur tes devis et factures. Tu pourras les modifier dans Paramètres, rubrique Profil.
              </p>
              <FormField label="Adresse (facturation)" htmlFor="profile-address">
                <Input
                  id="profile-address"
                  type="text"
                  value={profileForm.address}
                  onChange={(e) => setProfileForm((prev) => ({ ...prev, address: e.target.value }))}
                  placeholder="Numéro, rue, code postal, ville"
                />
              </FormField>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormField label="SIRET (requis pour facturer)" htmlFor="profile-siret">
                  <Input
                    id="profile-siret"
                    type="text"
                    inputMode="numeric"
                    value={profileForm.siret}
                    onChange={(e) => setProfileForm((prev) => ({ ...prev, siret: e.target.value }))}
                    placeholder="14 chiffres"
                  />
                </FormField>
                <FormField label="TVA intracommunautaire" htmlFor="profile-tva">
                  <Input
                    id="profile-tva"
                    type="text"
                    value={profileForm.tva_intra}
                    onChange={(e) => setProfileForm((prev) => ({ ...prev, tva_intra: e.target.value }))}
                    placeholder="Facultatif"
                  />
                </FormField>
              </div>
            </div>
          )}
        </div>

        {/* Error */}
        {error && !nomEnFaute && <Alerte id="profile-step-erreur" icone={<AlertCircle className="h-4 w-4 text-error" />}>{error}</Alerte>}
        {saveState === 'success' && (
          <div className="flex items-center gap-2 rounded-md border border-success/30 bg-[var(--color-success-tint)] px-3 py-2" role="status">
            <span className="text-sm text-success">Profil enregistré. L’onboarding ne se relancera pas au prochain démarrage.</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-6 flex flex-wrap justify-between gap-3 border-t border-border pt-4">
        <Button variant="ghost" onClick={onBack} disabled={loading || saveState === 'success'} data-testid="onboarding-prev-btn">
          Retour
        </Button>
        <div className="flex flex-wrap gap-3 max-[840px]:basis-full">
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
                ? (<><Spinner taille="bouton" className="mr-2" />Enregistrement en cours...</>)
                : 'Continuer'}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
