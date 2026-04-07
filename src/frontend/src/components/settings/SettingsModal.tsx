// Modal Paramètres - Shell principal avec navigation sidebar
// Refonte v0.4.0 : 8 onglets → 6, sidebar verticale, UX simplifiée

import { useState, useEffect } from 'react';
import { X, User, Cpu, Layers, Wrench, SlidersHorizontal, Info, Loader2, Zap, Shield } from 'lucide-react';
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
import { AgentsTab } from './AgentsTab';
import { PrivacyTab } from './PrivacyTab';
import { resolveModelForProvider } from './modelResolution';
import { Z_LAYER } from '../../styles/z-layers';
import { useUXMode } from '../../hooks/useUXMode';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = 'profile' | 'ai' | 'services' | 'tools' | 'agents' | 'privacy' | 'advanced' | 'about';

const ALL_TABS: { id: Tab; label: string; icon: typeof User; contributeurOnly?: boolean }[] = [
  { id: 'profile', label: 'Profil', icon: User },
  { id: 'ai', label: 'IA', icon: Cpu },
  { id: 'services', label: 'Services', icon: Layers },
  { id: 'tools', label: 'Outils', icon: Wrench, contributeurOnly: true },
  { id: 'agents', label: 'Agents', icon: Zap, contributeurOnly: true },
  { id: 'privacy', label: 'Confidentialité', icon: Shield },
  { id: 'advanced', label: 'Avancé', icon: SlidersHorizontal, contributeurOnly: true },
  { id: 'about', label: 'À propos', icon: Info },
];

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { isContributeur, setUXMode } = useUXMode();

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
  const [retestingOllama, setRetestingOllama] = useState(false);

  // Groq (transcription vocale)
  const [hasGroqKey, setHasGroqKey] = useState(false);
  const [groqKeyInput, setGroqKeyInput] = useState('');
  const [groqSaving, setGroqSaving] = useState(false);
  const [groqSaved, setGroqSaved] = useState(false);

  // Génération d'images
  const [selectedImageProvider, setSelectedImageProvider] = useState('gpt-image-1.5');
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
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  async function refreshStats() {
    try {
      const statsData = await api.getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Échec du rafraîchissement des stats:', err);
    }
  }

  async function loadSettings() {
    setLoading(true);
    try {
      const [keysResult, llmConfig, preferences, statsData, profileData, workingDirData, ollamaStatusData, groqKeyStatus, webSearchStatus] = await Promise.all([
        api.getApiKeysWithCorrupted().catch((): api.ApiKeysResult => ({ keys: {} as Record<string, boolean>, corrupted: [] })),
        api.getLLMConfig().catch(() => ({ provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [] })),
        api.getPreferences().catch(() => ({})),
        api.getStats().catch(() => null),
        api.getProfile().catch(() => null),
        api.getWorkingDirectory().catch(() => ({ path: null, exists: false })),
        api.getOllamaStatus().catch(() => null),
        api.hasGroqKey().catch(() => false),
        api.getWebSearchStatus().catch(() => ({ enabled: true })),
      ]);

      const keys = keysResult.keys;
      setApiKeys(keys);
      setCorruptedKeys(keysResult.corrupted);

      const loadedProvider = llmConfig.provider as api.LLMProvider;
      const resolvedModel = resolveModelForProvider(loadedProvider, llmConfig.model, ollamaStatusData);

      setSelectedProvider(loadedProvider);
      setSelectedModel(resolvedModel);
      setStats(statsData);
      setProfile(profileData);
      setWorkingDir(workingDirData?.path || null);
      setHasGroqKey(groqKeyStatus);
      setHasBraveKey(!!keys.brave);
      setWebSearchEnabled(webSearchStatus.enabled);

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
      console.error('Échec du chargement des paramètres:', err);
    } finally {
      setLoading(false);
    }
  }

  async function retestOllama() {
    setRetestingOllama(true);
    try {
      const statusData = await api.getOllamaStatus();
      if (statusData) {
        setOllamaStatus(statusData);
        if (statusData.available && statusData.models.length > 0) {
          setOllamaModels(statusData.models.map((m: { name: string }) => m.name));
        }
      }
    } catch {
      // laisser l'état précédent
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
    try {
      await api.setWebSearchEnabled(newValue);
      setWebSearchEnabled(newValue);
    } catch (err) {
      console.error('Échec du changement recherche web:', err);
    } finally {
      setWebSearchLoading(false);
    }
  }

  async function handleSelectProvider(provider: api.LLMProvider) {
    setSelectedProvider(provider);

    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    if (provider === 'ollama' && ollamaModels.length > 0) {
      defaultModel = ollamaModels[0];
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
      try {
        await api.setLLMConfig(provider, defaultModel);
        window.dispatchEvent(new Event('therese:llm-config-changed'));
      } catch (err) {
        console.error('Échec de la sauvegarde de la config LLM:', err);
      }
    }
  }

  async function handleSelectModel(modelId: string) {
    setSelectedModel(modelId);
    try {
      await api.setLLMConfig(selectedProvider, modelId);
      window.dispatchEvent(new Event('therese:llm-config-changed'));
    } catch (err) {
      console.error('Échec de la sauvegarde de la config LLM:', err);
    }
  }

  async function handleToggleAutoExtract() {
    const newValue = !autoExtractEntities;
    setAutoExtractEntities(newValue);
    try {
      await api.setPreference('auto_extract_entities', newValue, 'memory');
    } catch (err) {
      console.error('Échec de la sauvegarde de la préférence:', err);
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
        context: profileForm.context,
      });
      setProfile(savedProfile);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
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
          context: importedProfile.context || '',
        });
        setProfileSaved(true);
        setTimeout(() => setProfileSaved(false), 3000);
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
        const result = await api.setWorkingDirectory(selected);
        setWorkingDir(result.path);
      }
    } catch (err) {
      console.error('Échec de la sélection du dossier de travail:', err);
    }
  }

  // Gestion de la touche Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

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
            role="dialog"
            aria-modal="true"
            aria-label="Paramètres"
            data-testid="settings-modal"
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-3xl bg-surface border border-border rounded-xl shadow-2xl ${Z_LAYER.MODAL} max-h-[85vh] overflow-hidden flex flex-col`}
          >
            {/* En-tête */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <h2 className="text-lg font-semibold text-text">Paramètres</h2>
              <Button variant="ghost" size="icon" onClick={onClose} data-testid="settings-close-btn">
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Corps : sidebar + contenu */}
            <div className="flex-1 flex overflow-hidden min-h-0">
              {/* Sidebar navigation */}
              <nav className="w-44 shrink-0 border-r border-border/30 py-2 overflow-y-auto bg-background/30">
                {/* Toggle Mode Contributeur */}
                <div className="px-4 py-3 border-b border-border/30 mb-2">
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
                      <span className="text-[10px] text-text-muted leading-tight">Fonctions avancées</span>
                    </div>
                  </label>
                </div>
                {ALL_TABS
                  .filter((tab) => !tab.contributeurOnly || isContributeur)
                  .map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      data-testid={`settings-tab-${tab.id}`}
                      onClick={() => { setActiveTab(tab.id); setError(null); }}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                        isActive
                          ? 'bg-accent-cyan/10 text-accent-cyan border-r-2 border-accent-cyan'
                          : 'text-text-muted hover:text-text hover:bg-surface-elevated/30'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </nav>

              {/* Contenu */}
              <div className="flex-1 overflow-y-auto p-6">
                {renderContent()}
              </div>
            </div>

            {/* Pied de page */}
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-border/50 shrink-0">
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
