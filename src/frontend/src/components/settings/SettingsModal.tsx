// Modal Paramètres - Shell principal avec navigation sidebar
// Refonte v0.4.0 : 8 onglets → 6, sidebar verticale, UX simplifiée

import { useState, useEffect, useRef } from 'react';
import { X, User, Cpu, Layers, Wrench, SlidersHorizontal, Info, Loader2, Zap, Shield, Accessibility } from 'lucide-react';
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
import { resolveClassicSettingsTab, type ClassicSettingsTab } from '../../lib/classicNavigation';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  requestedTab?: ClassicSettingsTab | null;
}

type Tab = 'profile' | 'ai' | 'services' | 'accessibility' | 'tools' | 'agents' | 'privacy' | 'advanced' | 'about';

const ALL_TABS: { id: Tab; label: string; icon: typeof User; contributeurOnly?: boolean }[] = [
  { id: 'profile', label: 'Profil', icon: User },
  { id: 'ai', label: 'IA', icon: Cpu },
  { id: 'services', label: 'Services', icon: Layers },
  { id: 'accessibility', label: 'Accessibilité', icon: Accessibility },
  { id: 'tools', label: 'Outils', icon: Wrench, contributeurOnly: true },
  { id: 'agents', label: 'Agents', icon: Zap, contributeurOnly: true },
  { id: 'privacy', label: 'Confidentialité', icon: Shield },
  { id: 'advanced', label: 'Avancé', icon: SlidersHorizontal, contributeurOnly: true },
  { id: 'about', label: 'À propos', icon: Info },
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
    () => requestedTab ?? resolveClassicSettingsTab(window.location.search) ?? 'profile',
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadWarnings, setLoadWarnings] = useState<string[]>([]);
  const [operationStatus, setOperationStatus] = useState<string | null>(null);
  const [retryOperation, setRetryOperation] = useState<(() => void) | null>(null);
  const { isContributeur, setUXMode } = useUXMode();
  const visibleTabs = ALL_TABS.filter(
    (tab) => !tab.contributeurOnly || isContributeur || tab.id === activeTab,
  );

  // US-013 : piège de focus (Tab + restauration à la fermeture). Pas d'onEscape :
  // Échap reste géré par la pile unifiée (resolveEscape, L7) via le store.
  const dialogRef = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(dialogRef, { active: isOpen, isolateBackground: true });

  // Configuration LLM
  const [selectedProvider, setSelectedProvider] = useState<api.LLMProvider>('anthropic');
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-6');
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [corruptedKeys, setCorruptedKeys] = useState<string[]>([]);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

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

  async function loadSettings() {
    setLoading(true);
    setLoadWarnings([]);
    const [keysState, llmState, preferencesState, statsState, profileState, workingDirState, ollamaState, resourcesState, groqState, webSearchState] = await Promise.all([
      loadSetting('clés API', api.getApiKeysWithCorrupted(), { keys: {} as Record<string, boolean>, corrupted: [] }),
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
        if ('auto_extract_entities' in prefs && typeof prefs.auto_extract_entities === 'boolean') {
          setAutoExtractEntities(prefs.auto_extract_entities);
        }
      }
    } catch (err) {
      setLoadWarnings((current) => [...new Set([...current, 'données de configuration'])]);
      setError(err instanceof Error ? err.message : 'La configuration chargée est inutilisable.');
    } finally {
      setLoading(false);
    }
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
      return;
    }

    const providerConfig = PROVIDERS.find(p => p.id === selectedProvider);
    if (providerConfig?.keyPrefix && !apiKeyInput.startsWith(providerConfig.keyPrefix)) {
      setError(`La clé API doit commencer par "${providerConfig.keyPrefix}"`);
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

    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    if (provider === 'ollama' && ollamaModels.length > 0) {
      defaultModel = ollamaModels[0];
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
      setError(null);
      setOperationStatus('Enregistrement du fournisseur IA…');
      setRetryOperation(null);
      try {
        await api.setLLMConfig(provider, defaultModel);
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
      return (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
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
            error={error}
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
            showApiKey={showApiKey}
            setShowApiKey={setShowApiKey}
            ollamaStatus={ollamaStatus}
            ollamaModels={ollamaModels}
            systemResources={systemResources}
            saving={saving}
            saved={saved}
            error={error}
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
            showApiKey={showApiKey}
            setShowApiKey={setShowApiKey}
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
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Paramètres"
            data-testid="settings-modal"
            data-active-tab={activeTab}
            data-requested-tab={requestedTab ?? ''}
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 flex max-h-[calc(100vh-1rem)] w-[calc(100%-1rem)] max-w-3xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2xl sm:max-h-[85vh] ${Z_LAYER.MODAL}`}
          >
            {/* En-tête */}
            <div className="flex shrink-0 items-center justify-between border-b border-border/50 px-4 py-3 sm:px-6 sm:py-4">
              <h2 className="text-lg font-semibold text-text">Paramètres</h2>
              <Button variant="ghost" size="icon" onClick={onClose} data-testid="settings-close-btn" aria-label="Fermer les paramètres">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Corps : sidebar + contenu */}
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden sm:flex-row">
              {/* Sidebar navigation */}
              <nav role="tablist" aria-label="Rubriques des paramètres" className="flex w-full shrink-0 items-stretch gap-1 overflow-x-auto border-b border-border/30 bg-background/30 p-2 sm:block sm:w-44 sm:overflow-y-auto sm:border-b-0 sm:border-r sm:py-2">
                {/* Toggle Mode Contributeur */}
                <div className="mb-0 min-w-40 shrink-0 border-r border-border/30 px-2 py-2 sm:mb-2 sm:min-w-0 sm:border-b sm:border-r-0 sm:px-4 sm:py-3">
                  <label className="flex items-center gap-2 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={isContributeur}
                        onChange={(e) => setUXMode(e.target.checked ? 'contributeur' : 'standard')}
                        className="sr-only peer"
                        data-testid="ux-mode-toggle"
                      />
                      <div className="w-9 h-5 bg-border/50 rounded-full peer-checked:bg-accent-cyan/60 transition-colors" />
                      <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-text rounded-full transition-transform peer-checked:translate-x-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-medium text-text block leading-tight">Mode Contributeur</span>
                      <span className="text-xs text-text-muted leading-tight">Fonctions avancées</span>
                    </div>
                  </label>
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
                      className={`flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm transition-colors sm:w-full sm:gap-3 sm:border-b-0 sm:border-r-2 sm:px-4 ${
                        isActive
                          ? 'border-accent-cyan bg-accent-tint text-accent'
                          : 'border-transparent text-text-muted hover:bg-surface-elevated/30 hover:text-text'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </nav>

              {/* Contenu */}
              <div
                id={`settings-panel-${activeTab}`}
                role="tabpanel"
                aria-labelledby={`settings-tab-${activeTab}`}
                tabIndex={0}
                className="min-w-0 flex-1 overflow-y-auto p-4 outline-none sm:p-6"
              >
                {loadWarnings.length > 0 && (
                  <div role="alert" className="mb-4 rounded-lg border border-warning/40 bg-[var(--color-warning-tint)] p-3 text-sm text-warning">
                    <p><strong>Valeurs de secours affichées.</strong> Indisponible{loadWarnings.length > 1 ? 's' : ''} : {loadWarnings.join(', ')}.</p>
                    <button type="button" onClick={() => void loadSettings()} className="mt-2 rounded-md border border-warning px-3 py-2 font-semibold">Réessayer le chargement</button>
                  </div>
                )}
                {operationStatus && <p role="status" className="mb-4 rounded-lg border border-info/40 bg-[var(--color-info-tint)] p-3 text-sm text-info">{operationStatus}</p>}
                {error && retryOperation && (
                  <div role="alert" className="mb-4 rounded-lg border border-error/40 bg-[var(--color-error-tint)] p-3 text-sm text-error">
                    <p>{error}</p>
                    <button type="button" onClick={retryOperation} className="mt-2 rounded-md border border-error px-3 py-2 font-semibold">Réessayer</button>
                  </div>
                )}
                {renderContent()}
              </div>
            </div>

            {/* Pied de page */}
            <div className="flex shrink-0 justify-end gap-3 border-t border-border/50 px-4 py-3 sm:px-6 sm:py-4">
              <Button variant="ghost" onClick={onClose}>
                Fermer
              </Button>
              {activeTab === 'profile' && (
                <Button
                  variant="primary"
                  onClick={handleSaveProfile}
                  disabled={profileSaving || !profileForm.name.trim()}
                  data-testid="settings-save-btn"
                >
                  {profileSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
