// Modal Paramètres - Shell principal avec navigation sidebar
// Refonte v0.4.0 : 8 onglets → 6, sidebar verticale, UX simplifiée

import { useState, useEffect, useRef } from 'react';
import { X, User, Cpu, Layers, Wrench, SlidersHorizontal, Info, Zap, Shield, Accessibility } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { open } from '@tauri-apps/plugin-dialog';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';

// Composants des onglets
import { ProfileTab, ProfileFormData } from './ProfileTab';
import { LLMTab, PROVIDERS, IMAGE_PROVIDERS } from './LLMTab';
import { ServicesTab } from './ServicesTab';
import { ToolsPanel } from './ToolsPanel';
import { AdvancedTab } from './AdvancedTab';
import { AboutTab } from './AboutTab';
import { AccessibilityTab } from './AccessibilityTab';
import { AgentsTab } from './AgentsTab';
import { PrivacyTab } from './PrivacyTab';
import { resolveModelForProvider } from './modelResolution';
import { Z_LAYER } from '../../styles/z-layers';
import { useUXMode } from '../../hooks/useUXMode';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { useBillingProfileStore } from '../../stores/billingProfileStore';
import { resolveSettingsTab, type SettingsTab } from '../../lib/deepLinks';
import { Spinner } from '../ui/Spinner';
import { Alerte } from '../ui/Alerte';
import { Squelette } from '../ui/Squelette';
import { AlertCircle } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  requestedTab?: SettingsTab | null;
}

type Tab = 'profile' | 'ai' | 'services' | 'accessibility' | 'tools' | 'agents' | 'privacy' | 'advanced' | 'about';

export const ALL_TABS: { id: Tab; label: string; icon: typeof User; contributeurOnly?: boolean }[] = [
  { id: 'profile', label: 'Profil', icon: User },
  { id: 'ai', label: 'Service d’IA', icon: Cpu },
  { id: 'services', label: 'Services et connecteurs', icon: Layers },
  { id: 'accessibility', label: 'Accessibilité et affichage', icon: Accessibility },
  { id: 'tools', label: 'Outils', icon: Wrench, contributeurOnly: true },
  { id: 'agents', label: 'Agents', icon: Zap, contributeurOnly: true },
  { id: 'privacy', label: 'Sécurité et confidentialité', icon: Shield },
  { id: 'advanced', label: 'Avancé', icon: SlidersHorizontal, contributeurOnly: true },
  { id: 'about', label: 'À propos et mise à jour', icon: Info },
];

async function loadSetting<T>(label: string, request: Promise<T>, fallback: T) {
  try {
    return { value: await request, unavailable: null as string | null };
  } catch {
    return { value: fallback, unavailable: label };
  }
}

export function SettingsModal({ isOpen, onClose, requestedTab }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>(
    () => requestedTab ?? resolveSettingsTab(window.location.search) ?? 'profile',
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  /** Cible de repli du focus : le tabpanel est déjà focalisable (tabIndex 0). */
  const panneauRef = useRef<HTMLDivElement>(null);
  const [error, setErrorBrut] = useState<string | null>(null);
  /**
   * Lot 9 : `cleInvalide` distingue un REFUS DE CLÉ de toute autre erreur.
   * Lui seul pose `aria-invalid` sur le champ et déporte l'alerte dans la
   * carte du service (la coque se tait alors : une erreur ne s'annonce qu'une
   * fois). Il retombe à chaque `setError(null)` -- saisie du champ, changement
   * d'onglet, succès -- sans qu'aucun des trente-cinq sites d'appel ait à le
   * savoir. UN chemin ne passe pas par `setError(null)` et doit donc le
   * remettre à zéro lui-même : `handleSelectProvider`, dont le `setError(null)`
   * vit dans le bloc conditionné au modèle par défaut, vide sur un Ollama
   * joignable et sans modèle. La revue du diff l'a trouvé ; on ne prétend plus
   * ici que la seule source suffit.
   */
  const [cleInvalide, setCleInvalide] = useState(false);
  function setError(message: string | null) {
    setErrorBrut(message);
    if (message === null) setCleInvalide(false);
  }
  const [loading, setLoading] = useState(true);
  const [loadWarnings, setLoadWarnings] = useState<string[]>([]);
  const [operationStatus, setOperationStatus] = useState<string | null>(null);
  const [retryOperation, setRetryOperation] = useState<(() => void) | null>(null);
  const { isContributeur, setUXMode } = useUXMode();
  const visibleTabs = ALL_TABS.filter(
    (tab) => !tab.contributeurOnly || isContributeur || tab.id === activeTab,
  );
  // BUG-159 : nommer ce que le mode standard met de côté (le testeur cherchait
  // le chemin du dépôt des agents et croyait la rubrique supprimée).
  const hiddenTabLabels = ALL_TABS.filter((tab) => !visibleTabs.includes(tab)).map((tab) => tab.label);

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la cascade de la coque (ConversationCanvasPrototype) via le store.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen, isolateBackground: true });

  // Configuration LLM
  const [selectedProvider, setSelectedProvider] = useState<api.LLMProvider>('anthropic');
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-6');
  // B-225 : ce que l'utilisateur a réellement choisi, fournisseur par
  // fournisseur. Une ref et non un état : `handleSelectProvider` est asynchrone
  // et lirait une valeur périmée dans sa fermeture.
  const modelesParFournisseur = useRef<Partial<Record<api.LLMProvider, string>>>({});
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [corruptedKeys, setCorruptedKeys] = useState<string[]>([]);
  const [apiKeyInput, setApiKeyInput] = useState('');
  // B-526 : un interrupteur de visibilité PAR champ de clé, jamais un seul drapeau partagé.
  const [clesVisibles, setClesVisibles] = useState<Record<string, boolean>>({});

  // Ollama
  const [ollamaStatus, setOllamaStatus] = useState<api.OllamaStatus | null>(null);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [systemResources, setSystemResources] = useState<api.SystemResources | null>(null);
  const [retestingOllama, setRetestingOllama] = useState(false);

  // Groq (transcription vocale)
  const [hasGroqKey, setHasGroqKey] = useState(false);
  const [groqKeyInput, setGroqKeyInput] = useState('');
  const [groqSaving, setGroqSaving] = useState(false);
  const [groqSaved, setGroqSaved] = useState(false);

  // Génération d'images
  const [selectedImageProvider, setSelectedImageProvider] = useState('gpt-image-2');
  const [imageKeyInputs, setImageKeyInputs] = useState<Record<string, string>>({});
  const [imageKeySaving, setImageKeySaving] = useState<string | null>(null);
  const [imageKeySaved, setImageKeySaved] = useState<string | null>(null);

  // Recherche web
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);
  const [webSearchLoading, setWebSearchLoading] = useState(false);

  // Brave Search
  const [hasBraveKey, setHasBraveKey] = useState(false);
  const [braveKeyInput, setBraveKeyInput] = useState('');
  const [braveSaving, setBraveSaving] = useState(false);
  const [braveSaved, setBraveSaved] = useState(false);

  // Préférences mémoire
  const [autoExtractEntities, setAutoExtractEntities] = useState(true);

  // Profil utilisateur
  const [profile, setProfile] = useState<api.UserProfile | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileFormData>({
    name: '',
    nickname: '',
    company: '',
    role: '',
    email: '',
    location: '',
    address: '',
    siren: '',
    tva_intra: '',
    siret: '',
    code_ape: '',
    nda: '',
    context: '',
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);

  // Dossier de travail
  const [workingDir, setWorkingDir] = useState<string | null>(null);

  // Statistiques
  const [stats, setStats] = useState<api.Stats | null>(null);

  // Chargement des paramètres à l'ouverture
  useEffect(() => {
    if (isOpen && requestedTab) setActiveTab(requestedTab);
  }, [isOpen, requestedTab]);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  async function refreshStats() {
    setError(null);
    setRetryOperation(null);
    try {
      const statsData = await api.getStats();
      setStats(statsData);
      setOperationStatus('Statistiques actualisées.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible d’actualiser les statistiques.');
      setRetryOperation(() => () => void refreshStats());
    }
  }

  /**
   * Rend la liste des réglages qui n'ont PAS pu être lus, pour que l'appelant
   * sache si le bandeau disparaît (et donc si le focus va être perdu).
   *
   * `loadWarnings` n'est plus vidé au début : tant que la relecture court,
   * l'écran continue d'annoncer l'état connu et le bouton « Réessayer le
   * chargement » ne se démonte pas sous le doigt qui vient de le cliquer.
   * La liste est de toute façon remplacée à chaque retour de lecture.
   */
  async function loadSettings(): Promise<string[]> {
    setLoading(true);
    const [keysState, llmState, preferencesState, statsState, profileState, workingDirState, ollamaState, resourcesState, groqState, webSearchState] = await Promise.all([
      loadSetting('clés API', api.getApiKeysWithCorrupted(), { keys: {} as Record<string, boolean>, corrupted: [], sources: {} as Record<string, string> }),
      loadSetting('configuration IA', api.getLLMConfig(), { provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [] }),
      loadSetting('préférences', api.getPreferences(), {}),
      loadSetting('statistiques', api.getStats(), null),
      loadSetting('profil', api.getProfile(), null),
      loadSetting('dossier de travail', api.getWorkingDirectory(), { path: null, exists: false }),
      loadSetting('statut Ollama', api.getOllamaStatus(), null),
      loadSetting('ressources système', api.getSystemResources(), null),
      loadSetting('clé Groq', api.hasGroqKey(), false),
      loadSetting('recherche web', api.getWebSearchStatus(), {
        enabled: true,
        providers: { gemini: 'indisponible', others: 'indisponible' },
        description: 'Valeur de secours',
      }),
    ]);

    const unavailable = [keysState, llmState, preferencesState, statsState, profileState, workingDirState, ollamaState, resourcesState, groqState, webSearchState]
      .map((state) => state.unavailable)
      .filter((label): label is string => Boolean(label));
    setLoadWarnings(unavailable);
    // `restants` suit ce qui est RÉELLEMENT posé : le catch ci-dessous ajoute
    // « données de configuration » après coup, et rendre `unavailable` tel quel
    // annoncerait une liste vide alors que le bandeau reste à l'écran.
    let restants = unavailable;

    const keysResult = keysState.value;
    const llmConfig = llmState.value;
    const preferences = preferencesState.value;
    const statsData = statsState.value;
    const profileData = profileState.value;
    const workingDirData = workingDirState.value;
    const ollamaStatusData = ollamaState.value;
    const systemResourcesData = resourcesState.value;
    const groqKeyStatus = groqState.value;
    const webSearchStatus = webSearchState.value;

    try {
      const keys = keysResult.keys;
      setApiKeys(keys);
      setCorruptedKeys(keysResult.corrupted);

      const loadedProvider = llmConfig.provider as api.LLMProvider;
      const resolvedModel = resolveModelForProvider(
        loadedProvider,
        llmConfig.model,
        ollamaStatusData,
        llmConfig.available_models || [],
      );

      setSelectedProvider(loadedProvider);
      setSelectedModel(resolvedModel);
      modelesParFournisseur.current[loadedProvider] = resolvedModel;
      setStats(statsData);
      setProfile(profileData);
      setWorkingDir(workingDirData?.path || null);
      setHasGroqKey(groqKeyStatus);
      setHasBraveKey(!!keys.brave);
      setWebSearchEnabled(webSearchStatus.enabled);
      setSystemResources(systemResourcesData);

      if (ollamaStatusData) {
        setOllamaStatus(ollamaStatusData);
        if (ollamaStatusData.available && ollamaStatusData.models.length > 0) {
          setOllamaModels(ollamaStatusData.models.map(m => m.name));
        }
      }

      if (profileData) {
        setProfileForm({
          name: profileData.name || '',
          nickname: profileData.nickname || '',
          company: profileData.company || '',
          role: profileData.role || '',
          email: profileData.email || '',
          location: profileData.location || '',
          address: profileData.address || '',
          siren: profileData.siren || '',
          tva_intra: profileData.tva_intra || '',
          siret: profileData.siret || '',
          code_ape: profileData.code_ape || '',
          nda: profileData.nda || '',
          context: profileData.context || '',
        });
      }

      if (preferences && typeof preferences === 'object') {
        const prefs = preferences as Record<string, unknown>;
        // B-252 : `getPreferences` rend l'enveloppe du serveur
        // (`{ auto_extract_entities: { value, category, updated_at } }`), pas la
        // valeur. Le test portait donc sur un OBJET, toujours faux : l'interrupteur
        // reprenait son défaut à chaque ouverture, même quand la préférence
        // enregistrée disait l'inverse.
        const extractionAuto = (prefs.auto_extract_entities as { value?: unknown } | undefined)?.value;
        if (typeof extractionAuto === 'boolean') {
          setAutoExtractEntities(extractionAuto);
        }
      }
    } catch (err) {
      restants = [...new Set([...restants, 'données de configuration'])];
      setLoadWarnings(restants);
      // Les deux setters natifs plutôt que `setError` : une lecture qui échoue
      // n'est JAMAIS un refus de clé, et `setError(message)` ne remet pas
      // `cleInvalide` à faux quand `message` est non nul -- un refus de clé
      // antérieur survivrait donc à cette erreur-ci et déporterait son alerte
      // dans la carte du service. Le couple écrit ici dit les deux choses en
      // même temps. (La raison affichée jusqu'ici -- une dépendance que
      // l'effet d'ouverture ne pourrait pas prendre -- était fausse : cet
      // effet ne liste pas `loadSettings`, et `setError` ne ferme sur aucune
      // valeur changeante.)
      setErrorBrut(err instanceof Error ? err.message : 'La configuration chargée est inutilisable.');
      setCleInvalide(false);
    } finally {
      setLoading(false);
    }

    return restants;
  }

  async function retestOllama() {
    setRetestingOllama(true);
    setError(null);
    setRetryOperation(null);
    try {
      const statusData = await api.getOllamaStatus();
      if (statusData) {
        setOllamaStatus(statusData);
        if (statusData.available && statusData.models.length > 0) {
          setOllamaModels(statusData.models.map((m: { name: string }) => m.name));
        }
      }
      setOperationStatus('Statut Ollama actualisé.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible d’actualiser le statut Ollama.');
      setRetryOperation(() => () => void retestOllama());
    } finally {
      setRetestingOllama(false);
    }
  }

  async function handleSaveApiKey() {
    if (!apiKeyInput.trim()) {
      setError('Entre une clé API');
      setCleInvalide(true);
      return;
    }

    const providerConfig = PROVIDERS.find(p => p.id === selectedProvider);
    if (providerConfig?.keyPrefix && !apiKeyInput.startsWith(providerConfig.keyPrefix)) {
      setError(`La clé API doit commencer par "${providerConfig.keyPrefix}"`);
      setCleInvalide(true);
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await api.setApiKey(selectedProvider, apiKeyInput);
      setSaved(true);
      setApiKeys(prev => ({ ...prev, [selectedProvider]: true }));
      setCorruptedKeys(prev => prev.filter(k => k !== selectedProvider));
      setApiKeyInput('');
      window.dispatchEvent(new Event('therese:llm-config-changed'));
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
      setCleInvalide(true);
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveGroqKey() {
    if (!groqKeyInput.trim()) {
      setError('Entre une clé API Groq');
      return;
    }
    if (!groqKeyInput.startsWith('gsk_')) {
      setError('La clé API Groq doit commencer par "gsk_"');
      return;
    }

    setGroqSaving(true);
    setError(null);

    try {
      await api.setApiKey('groq', groqKeyInput);
      setGroqSaved(true);
      setHasGroqKey(true);
      setGroqKeyInput('');
      setTimeout(() => setGroqSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setGroqSaving(false);
    }
  }

  async function handleSaveBraveKey() {
    if (!braveKeyInput.trim()) {
      setError('Entre une clé API Brave Search');
      return;
    }

    setBraveSaving(true);
    setError(null);

    try {
      await api.setApiKey('brave', braveKeyInput);
      setBraveSaved(true);
      setHasBraveKey(true);
      setBraveKeyInput('');
      setTimeout(() => setBraveSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setBraveSaving(false);
    }
  }

  async function handleSaveImageKey(apiKeyId: 'openai_image' | 'gemini_image' | 'fal') {
    const keyInput = imageKeyInputs[apiKeyId] || '';
    if (!keyInput.trim()) {
      setError('Entre une clé API');
      return;
    }

    const provider = IMAGE_PROVIDERS.find(p => p.apiKeyId === apiKeyId);
    if (provider && provider.keyPrefix && !keyInput.startsWith(provider.keyPrefix)) {
      setError(`La clé API doit commencer par "${provider.keyPrefix}"`);
      return;
    }

    setImageKeySaving(apiKeyId);
    setError(null);

    try {
      await api.setApiKey(apiKeyId, keyInput);
      setImageKeySaved(apiKeyId);
      setApiKeys(prev => ({ ...prev, [apiKeyId]: true }));
      setImageKeyInputs(prev => ({ ...prev, [apiKeyId]: '' }));
      setTimeout(() => setImageKeySaved(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setImageKeySaving(null);
    }
  }

  async function handleToggleWebSearch() {
    const newValue = !webSearchEnabled;
    setWebSearchLoading(true);
    setError(null);
    setOperationStatus('Enregistrement de la recherche web…');
    setRetryOperation(null);
    try {
      await api.setWebSearchEnabled(newValue);
      setWebSearchEnabled(newValue);
      setOperationStatus('Recherche web enregistrée.');
    } catch (err) {
      setOperationStatus(null);
      setError(err instanceof Error ? err.message : 'La recherche web n’a pas pu être enregistrée.');
      setRetryOperation(() => () => void handleToggleWebSearch());
    } finally {
      setWebSearchLoading(false);
    }
  }

  async function handleSelectProvider(provider: api.LLMProvider) {
    const previousProvider = selectedProvider;
    const previousModel = selectedModel;
    setSelectedProvider(provider);
    // Hors du `if (defaultModel)` plus bas, et avant tout le reste : changer
    // de fournisseur n'est jamais un refus de clé. `defaultModel` est vide
    // pour le seul fournisseur à catalogue vide, Ollama, quand `ollamaModels`
    // l'est aussi (service joignable, aucun modèle tiré) ; le bloc était donc
    // sauté, `cleInvalide` restait vrai et `needsApiKey` devenait faux : la
    // carte du service ne montait plus son alerte, la coque se taisait, et
    // l'erreur n'était rendue NULLE PART. On ne touche pas à `error` : la
    // coque la reprend.
    setCleInvalide(false);

    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    if (provider === 'ollama' && ollamaModels.length > 0) {
      defaultModel = ollamaModels[0];
    }

    // B-225 : revenir sur un fournisseur déjà configuré doit rendre le modèle
    // qui y avait été enregistré, pas le premier du catalogue. Sans cette
    // mémoire, inspecter un fournisseur réécrivait la configuration active en
    // silence : mistral-medium-latest devenait mistral-large-latest au retour.
    const dejaChoisi = modelesParFournisseur.current[provider];
    // Un modèle Ollama peut avoir disparu de la machine entre-temps ; les
    // catalogues cloud, eux, ne bougent pas d'un clic à l'autre.
    const toujoursPropose = provider !== 'ollama' || ollamaModels.includes(dejaChoisi ?? '');
    if (dejaChoisi && toujoursPropose) {
      defaultModel = dejaChoisi;
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
      setError(null);
      setOperationStatus('Enregistrement du fournisseur IA…');
      setRetryOperation(null);
      try {
        await api.setLLMConfig(provider, defaultModel);
        modelesParFournisseur.current[provider] = defaultModel;
        window.dispatchEvent(new Event('therese:llm-config-changed'));
        setOperationStatus('Fournisseur IA enregistré.');
      } catch (err) {
        setSelectedProvider(previousProvider);
        setSelectedModel(previousModel);
        setOperationStatus(null);
        setError(err instanceof Error ? err.message : 'Le fournisseur IA n’a pas pu être enregistré.');
        setRetryOperation(() => () => void handleSelectProvider(provider));
      }
    }
  }

  async function handleSelectModel(modelId: string) {
    const previousModel = selectedModel;
    setSelectedModel(modelId);
    setError(null);
    setOperationStatus('Enregistrement du modèle IA…');
    setRetryOperation(null);
    try {
      await api.setLLMConfig(selectedProvider, modelId);
      modelesParFournisseur.current[selectedProvider] = modelId;
      window.dispatchEvent(new Event('therese:llm-config-changed'));
      setOperationStatus('Modèle IA enregistré.');
    } catch (err) {
      setSelectedModel(previousModel);
      setOperationStatus(null);
      setError(err instanceof Error ? err.message : 'Le modèle IA n’a pas pu être enregistré.');
      setRetryOperation(() => () => void handleSelectModel(modelId));
    }
  }

  async function handleToggleAutoExtract() {
    const newValue = !autoExtractEntities;
    setAutoExtractEntities(newValue);
    setError(null);
    setOperationStatus('Enregistrement de l’extraction automatique…');
    setRetryOperation(null);
    try {
      await api.setPreference('auto_extract_entities', newValue, 'memory');
      setOperationStatus('Extraction automatique enregistrée.');
    } catch (err) {
      setAutoExtractEntities(!newValue);
      setOperationStatus(null);
      setError(err instanceof Error ? err.message : 'La préférence n’a pas pu être enregistrée.');
      setRetryOperation(() => () => void handleToggleAutoExtract());
    }
  }

  async function handleSaveProfile() {
    if (!profileForm.name.trim()) {
      setError('Le nom est obligatoire');
      return;
    }

    setProfileSaving(true);
    setError(null);

    try {
      const savedProfile = await api.setProfile({
        name: profileForm.name,
        nickname: profileForm.nickname,
        company: profileForm.company,
        role: profileForm.role,
        email: profileForm.email,
        location: profileForm.location,
        address: profileForm.address,
        siren: profileForm.siren,
        tva_intra: profileForm.tva_intra,
        siret: profileForm.siret,
        code_ape: profileForm.code_ape,
        nda: profileForm.nda,
        context: profileForm.context,
      });
      setProfile(savedProfile);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
      // Le formulaire de facture peut être resté ouvert derrière les Réglages
      // (deux modales indépendantes) : rafraîchir le garde-fou P0-PROD-2 pour
      // qu'il reflète immédiatement le profil qu'on vient de compléter.
      void useBillingProfileStore.getState().refresh();
      // Revue Soso 27/07 (F6) : la coque ne lit le profil qu'au montage. Sans
      // ce signal, ses initiales et sa salutation gardaient l'ancien nom
      // jusqu'au redémarrage de l'application.
      window.dispatchEvent(new CustomEvent('therese:profile-updated'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleImportClaudeMd() {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Markdown', extensions: ['md'] }],
      });

      if (selected && typeof selected === 'string') {
        setProfileSaving(true);
        const importedProfile = await api.importClaudeMd(selected);
        setProfile(importedProfile);
        setProfileForm({
          name: importedProfile.name || '',
          nickname: importedProfile.nickname || '',
          company: importedProfile.company || '',
          role: importedProfile.role || '',
          email: importedProfile.email || '',
          location: importedProfile.location || '',
          address: importedProfile.address || '',
          siren: importedProfile.siren || '',
          tva_intra: importedProfile.tva_intra || '',
          siret: importedProfile.siret || '',
          code_ape: importedProfile.code_ape || '',
          nda: importedProfile.nda || '',
          context: importedProfile.context || '',
        });
        setProfileSaved(true);
        setTimeout(() => setProfileSaved(false), 3000);
        void useBillingProfileStore.getState().refresh();
        // L'import modifie le profil autant qu'un enregistrement manuel : la
        // coque doit le relire (contre-vérification N4).
        window.dispatchEvent(new CustomEvent('therese:profile-updated'));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'import');
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleSelectWorkingDir() {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
      });

      if (selected && typeof selected === 'string') {
        setError(null);
        setOperationStatus('Enregistrement du dossier de travail…');
        setRetryOperation(null);
        const result = await api.setWorkingDirectory(selected);
        setWorkingDir(result.path);
        setOperationStatus('Dossier de travail enregistré.');
      }
    } catch (err) {
      setOperationStatus(null);
      setError(err instanceof Error ? err.message : 'Le dossier de travail n’a pas pu être enregistré.');
      setRetryOperation(() => () => void handleSelectWorkingDir());
    }
  }

  function renderContent() {
    if (loading) {
      // Trois rangées de deux : la forme de ce qui arrive, pas douze barres.
      // Les squelettes sont décoratifs (`aria-hidden` posé par la primitive),
      // c'est le `role="status"` qui annonce la lecture.
      return (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2.5">
            {Array.from({ length: 6 }, (_, i) => (
              <Squelette key={i} largeur="w-full" classeBarre="h-16 rounded-sm" />
            ))}
          </div>
          <p role="status" className="text-sm text-text-muted">Lecture des réglages…</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'profile':
        return (
          <ProfileTab
            profileForm={profileForm}
            setProfileForm={setProfileForm}
            profile={profile}
            saving={profileSaving}
            saved={profileSaved}
            setError={setError}
            onSave={handleSaveProfile}
            onImport={handleImportClaudeMd}
          />
        );
      case 'ai':
        return (
          <LLMTab
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            apiKeys={apiKeys}
            corruptedKeys={corruptedKeys}
            apiKeyInput={apiKeyInput}
            setApiKeyInput={setApiKeyInput}
            showApiKey={clesVisibles.llm ?? false}
            setShowApiKey={(v) => setClesVisibles((c) => ({ ...c, llm: v }))}
            ollamaStatus={ollamaStatus}
            ollamaModels={ollamaModels}
            systemResources={systemResources}
            saving={saving}
            saved={saved}
            error={error}
            cleInvalide={cleInvalide}
            setError={setError}
            onSelectProvider={handleSelectProvider}
            onSelectModel={handleSelectModel}
            onSaveApiKey={handleSaveApiKey}
            onRetestOllama={retestOllama}
            retestingOllama={retestingOllama}
          />
        );
      case 'services':
        return (
          <ServicesTab
            apiKeys={apiKeys}
            clesVisibles={clesVisibles}
            basculerCle={(id) => setClesVisibles((c) => ({ ...c, [id]: !c[id] }))}
            error={error}
            setError={setError}
            selectedImageProvider={selectedImageProvider}
            onSelectImageProvider={setSelectedImageProvider}
            imageKeyInputs={imageKeyInputs}
            setImageKeyInputs={setImageKeyInputs}
            imageKeySaving={imageKeySaving}
            imageKeySaved={imageKeySaved}
            onSaveImageKey={handleSaveImageKey}
            hasGroqKey={hasGroqKey}
            groqKeyInput={groqKeyInput}
            setGroqKeyInput={setGroqKeyInput}
            groqSaving={groqSaving}
            groqSaved={groqSaved}
            onSaveGroqKey={handleSaveGroqKey}
            webSearchEnabled={webSearchEnabled}
            webSearchLoading={webSearchLoading}
            onToggleWebSearch={handleToggleWebSearch}
            hasBraveKey={hasBraveKey}
            braveKeyInput={braveKeyInput}
            setBraveKeyInput={setBraveKeyInput}
            braveSaving={braveSaving}
            braveSaved={braveSaved}
            onSaveBraveKey={handleSaveBraveKey}
            autoExtractEntities={autoExtractEntities}
            onToggleAutoExtract={handleToggleAutoExtract}
          />
        );
      case 'accessibility':
        return <AccessibilityTab />;
      case 'tools':
        return <ToolsPanel onError={setError} />;
      case 'advanced':
        return (
          <AdvancedTab
            stats={stats}
            workingDir={workingDir}
            onSelectWorkingDir={handleSelectWorkingDir}
            onRefreshStats={refreshStats}
          />
        );
      case 'agents':
        return <AgentsTab />;
      case 'privacy':
        return <PrivacyTab />;
      case 'about':
        return <AboutTab />;
    }
  }

  function selectTab(tab: Tab) {
    setActiveTab(tab);
    setError(null);
  }

  function handleTabKeyDown(event: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    const previous = event.key === 'ArrowUp' || event.key === 'ArrowLeft';
    const next = event.key === 'ArrowDown' || event.key === 'ArrowRight';
    if (!previous && !next && event.key !== 'Home' && event.key !== 'End') return;
    event.preventDefault();
    const nextIndex = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? visibleTabs.length - 1
        : previous
          ? (index - 1 + visibleTabs.length) % visibleTabs.length
          : (index + 1) % visibleTabs.length;
    const tab = visibleTabs[nextIndex];
    selectTab(tab.id);
    requestAnimationFrame(() => {
      document.getElementById(`settings-tab-${tab.id}`)?.focus();
    });
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            data-dialog-backdrop
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className={`fixed inset-0 bg-black/60 backdrop-blur-sm ${Z_LAYER.MODAL}`}
            /* BUG-156 : plus de fermeture au clic sur le fond. Un clic à côté
               faisait perdre la saisie en cours (clés API, chemins) et l'onglet
               ouvert. La sortie passe par « Fermer » ou Échap. */
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            aria-label="Paramètres"
            data-testid="settings-modal"
            data-active-tab={activeTab}
            data-requested-tab={requestedTab ?? ''}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 flex max-h-[calc(100vh-1rem)] w-[calc(100%-1rem)] max-w-6xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-md border border-border bg-surface shadow-lg sm:max-h-[85vh] ${Z_LAYER.MODAL}`}
          >
            {/* En-tête */}
            <div className="flex shrink-0 items-center justify-between border-b border-border/50 px-4 py-3 sm:px-6 sm:py-4">
              {/* `@layer base` pose déjà la famille de titres : pas de
                  `font-editorial` ici, la maquette est un h1 sans `.editorial`. */}
              <h1 id="settings-title" className="text-lg font-semibold text-text">Paramètres</h1>
              <Button variant="ghost" size="icon" onClick={onClose} data-testid="settings-close-btn" aria-label="Fermer les paramètres">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Corps : sidebar + contenu */}
            {/* La césure passe de 640 à 1024 px : entre les deux, la nav est une
                grille de trois colonnes AU-DESSUS du panneau (maquette
                `.reglages{grid-template-columns:1fr}` sous 1024 px). Avec la
                bascule en ligne dès 640 px, elle occupait toute une rangée flex
                et le panneau tombait à zéro entre 640 et 1023 px. */}
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden min-[1024px]:flex-row">
              {/* Sidebar navigation */}
              <nav role="tablist" aria-label="Rubriques des paramètres" className="w-full shrink-0 gap-1 border-b border-border/30 bg-background/30 p-2 max-[1023px]:grid max-[1023px]:grid-cols-3 min-[1024px]:block min-[1024px]:w-60 min-[1024px]:overflow-y-auto min-[1024px]:border-b-0 min-[1024px]:border-r min-[1024px]:py-2">
                {/* Toggle Mode Contributeur */}
                <div className="mb-0 shrink-0 border-border/30 px-2 py-2 max-[1023px]:col-span-3 min-[1024px]:mb-2 min-[1024px]:border-b min-[1024px]:px-4 min-[1024px]:py-3">
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={isContributeur}
                        onChange={(e) => setUXMode(e.target.checked ? 'contributeur' : 'standard')}
                        className="sr-only peer"
                        data-testid="ux-mode-toggle"
                      />
                      {/* Piste 40 x 24, curseur 20, inset 2, course 16 :
                          2 + 20 + 16 = 38 pour 40, symétrique aux 2 px de départ. */}
                      <div className="w-10 h-6 bg-border/50 rounded-full peer-checked:bg-accent-cyan/60 transition-colors" />
                      <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-text rounded-full transition-transform peer-checked:translate-x-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium text-text block leading-tight">Mode Contributeur</span>
                    </div>
                  </label>
                  {/* Hors du `label` : la règle du lot bannit 12 px dans le
                      sous-arbre d'un interactif, et cette aide n'est pas le nom
                      de l'interrupteur. */}
                  <p className="text-xs text-text-muted leading-tight">Fonctions avancées</p>
                  {/* BUG-159 : en mode standard, les rubriques avancées
                      disparaissaient sans un mot. Le testeur, à la recherche du
                      chemin du dépôt des agents, a cru qu'elles n'existaient
                      plus. On les nomme au lieu de les escamoter. */}
                  {hiddenTabLabels.length > 0 && (
                    <p data-testid="settings-hidden-tabs" className="mt-2 text-xs leading-tight text-text-muted">
                      Masquées ici : {hiddenTabLabels.join(', ')}.
                    </p>
                  )}
                </div>
                {visibleTabs.map((tab, index) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      id={`settings-tab-${tab.id}`}
                      role="tab"
                      aria-selected={isActive}
                      aria-controls={`settings-panel-${tab.id}`}
                      tabIndex={isActive ? 0 : -1}
                      data-testid={`settings-tab-${tab.id}`}
                      onClick={() => selectTab(tab.id)}
                      onKeyDown={(event) => handleTabKeyDown(event, index)}
                      className={`flex min-h-9 shrink-0 items-center gap-2.5 rounded-sm px-3 py-2 text-left text-sm transition-colors min-[1024px]:w-full ${
                        isActive
                          ? 'bg-accent-tint text-accent font-semibold'
                          : 'text-text-muted hover:bg-surface-2 hover:text-text'
                      }`}
                    >
                      <Icon className="h-[18px] w-[18px] shrink-0" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </nav>

              {/* Contenu */}
              <div
                ref={panneauRef}
                id={`settings-panel-${activeTab}`}
                role="tabpanel"
                aria-labelledby={`settings-tab-${activeTab}`}
                tabIndex={0}
                className="min-w-0 flex-1 overflow-y-auto p-4 outline-none sm:p-6"
              >
                {/* Triage 26/07 : « Indisponible : clés API » se lisait comme
                    « il manque des clés » alors qu'il s'agit d'un échec de
                    LECTURE. Le testeur a cru à un défaut de configuration de la
                    génération d'images. */}
                {/* Le bandeau de lecture partielle survit au chargement : sinon
                    son bouton se démonte sous le doigt qui vient de le cliquer et
                    le focus retombe sur le `body`. D'où l'`aria-disabled` plutôt
                    qu'un `disabled`, et le repli du focus sur le tabpanel quand la
                    reprise réussit et que le bandeau disparaît pour de bon. */}
                {loadWarnings.length > 0 && (
                  <Alerte
                    ton="attention"
                    data-testid="settings-load-warning"
                    className="mb-4"
                    icone={<AlertCircle className="h-[18px] w-[18px]" />}
                    titre={`${loadWarnings.length > 1 ? 'Ces réglages n’ont pas pu être lus' : 'Ce réglage n’a pas pu être lu'} : ${loadWarnings.join(', ')}.`}
                    action={(
                      <Button
                        variant="secondary"
                        size="md"
                        aria-disabled={loading}
                        className="aria-disabled:opacity-50 aria-disabled:cursor-wait"
                        onClick={() => {
                          if (loading) return;
                          void (async () => {
                            const restants = await loadSettings();
                            if (restants.length === 0) panneauRef.current?.focus();
                          })();
                        }}
                      >
                        Réessayer le chargement
                      </Button>
                    )}
                  >
                    Les valeurs affichées ici sont des valeurs par défaut, pas ta configuration réelle.
                  </Alerte>
                )}
                {!loading && operationStatus && <p role="status" className="mb-4 px-4 py-3 text-sm text-info">{operationStatus}</p>}
                {/* B-454 : une erreur sans action de reprise (onglet Outils) n'atteignait jamais l'écran.
                    Lot 9 : un refus de clé n'a qu'UNE alerte, celle de la carte du
                    service. La condition reste `{error && (` : la garde de B-454
                    lit ce littéral. */}
                {error && (
                  loading || cleInvalide ? null : (
                    <Alerte
                      className="mb-4"
                      icone={<AlertCircle className="h-[18px] w-[18px]" />}
                      action={retryOperation ? (
                        <Button variant="ghost" size="md" onClick={retryOperation}>Réessayer</Button>
                      ) : undefined}
                    >
                      {error}
                    </Alerte>
                  )
                )}
                {renderContent()}
              </div>
            </div>

            {/* Pied de page */}
            <div className="flex shrink-0 justify-end gap-3 border-t border-border/50 px-4 py-3 sm:px-6 sm:py-4">
              <Button variant="ghost" size="md" onClick={onClose}>
                Fermer
              </Button>
              {activeTab === 'profile' && (
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleSaveProfile}
                  disabled={profileSaving || !profileForm.name.trim()}
                  data-testid="settings-save-btn"
                >
                  {profileSaving ? (
                    <>
                      <Spinner taille="bouton" className="mr-2" />
                      Enregistrement...
                    </>
                  ) : (
                    'Enregistrer'
                  )}
                </Button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
