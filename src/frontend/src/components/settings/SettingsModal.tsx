import { useState, useEffect } from 'react';
import { X, Key, Check, AlertCircle, Loader2, Eye, EyeOff, Cpu, Database, Sparkles, User, FolderOpen, Upload, Mic, Image as ImageIcon, Wrench, Globe, Accessibility, Gauge, AlertTriangle } from 'lucide-react';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { motion, AnimatePresence } from 'framer-motion';
import { open } from '@tauri-apps/plugin-dialog';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import { ToolsPanel } from './ToolsPanel';
import { CRMSyncPanel } from './CRMSyncPanel';
import { useDemoStore } from '../../stores/demoStore';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = 'profile' | 'api' | 'tools' | 'data' | 'accessibility' | 'performance' | 'personalisation' | 'escalation';

// Provider configuration
interface ProviderConfig {
  id: api.LLMProvider;
  name: string;
  description: string;
  keyPrefix?: string;
  keyPlaceholder?: string;
  consoleUrl?: string;
  models: { id: string; name: string; badge?: string }[];
}

const PROVIDERS: ProviderConfig[] = [
  {
    id: 'anthropic',
    name: 'Claude (Anthropic)',
    description: 'Recommandé - Excellent coding et français',
    keyPrefix: 'sk-ant-',
    keyPlaceholder: 'sk-ant-...',
    consoleUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      { id: 'claude-opus-4-5-20251101', name: 'Claude Opus 4.5', badge: 'Flagship' },
      { id: 'claude-sonnet-4-5-20250929', name: 'Claude Sonnet 4.5', badge: 'Recommandé' },
      { id: 'claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5', badge: 'Rapide' },
    ],
  },
  {
    id: 'openai',
    name: 'GPT (OpenAI)',
    description: 'GPT-5 series - Polyvalent et puissant',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.openai.com/api-keys',
    models: [
      { id: 'gpt-5.2', name: 'GPT-5.2', badge: 'Flagship' },
      { id: 'gpt-5', name: 'GPT-5' },
      { id: 'gpt-4.1', name: 'GPT-4.1', badge: 'Coding' },
      { id: 'gpt-4o', name: 'GPT-4o', badge: 'Rapide' },
      { id: 'o3', name: 'o3', badge: 'Reasoning' },
      { id: 'o4-mini', name: 'o4-mini', badge: 'Économique' },
    ],
  },
  {
    id: 'gemini',
    name: 'Gemini (Google)',
    description: 'Gemini 3 - Contexte 1M tokens',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      { id: 'gemini-3-pro-preview', name: 'Gemini 3 Pro', badge: 'Flagship' },
      { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash', badge: 'Rapide' },
      { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', badge: 'Recommandé' },
      { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
    ],
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    description: 'IA française souveraine',
    keyPlaceholder: '...',
    consoleUrl: 'https://console.mistral.ai/api-keys',
    models: [
      { id: 'mistral-large-latest', name: 'Mistral Large', badge: 'Flagship' },
      { id: 'codestral-latest', name: 'Codestral', badge: 'Coding' },
      { id: 'devstral-small-latest', name: 'Devstral Small', badge: 'Dev' },
      { id: 'mistral-small-latest', name: 'Mistral Small', badge: 'Économique' },
    ],
  },
  {
    id: 'grok',
    name: 'Grok (xAI)',
    description: 'Grok 4 - Most intelligent model',
    keyPrefix: 'xai-',
    keyPlaceholder: 'xai-...',
    consoleUrl: 'https://console.x.ai',
    models: [
      { id: 'grok-4', name: 'Grok 4', badge: 'Flagship' },
      { id: 'grok-4.1-fast', name: 'Grok 4.1 Fast', badge: 'Rapide' },
      { id: 'grok-3', name: 'Grok 3' },
    ],
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: '100% local - Aucune clé API requise',
    models: [], // Loaded dynamically
  },
];

// Image generation providers
interface ImageProviderConfig {
  id: string;
  name: string;
  description: string;
  apiKeyId: 'openai_image' | 'gemini_image';  // Specific image API key
  keyName: string;  // Human-readable key name
  keyPrefix: string;  // Expected prefix for validation
  keyPlaceholder: string;  // Placeholder text
  consoleUrl: string;  // URL to get API key
}

const IMAGE_PROVIDERS: ImageProviderConfig[] = [
  {
    id: 'gpt-image-1.5',
    name: 'GPT Image 1.5',
    description: 'Génération d\'images OpenAI (gpt-image-1.5)',
    apiKeyId: 'openai_image',
    keyName: 'OpenAI (Image)',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.openai.com/api-keys',
  },
  {
    id: 'nanobanan-pro',
    name: 'Nano Banana Pro',
    description: 'Génération d\'images Google Gemini',
    apiKeyId: 'gemini_image',
    keyName: 'Gemini (Image)',
    keyPrefix: 'AIza',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
  },
];

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // LLM Configuration
  const [selectedProvider, setSelectedProvider] = useState<api.LLMProvider>('anthropic');
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-5-20250929');
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  // Ollama
  const [ollamaStatus, setOllamaStatus] = useState<api.OllamaStatus | null>(null);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);

  // Groq (Voice transcription)
  const [hasGroqKey, setHasGroqKey] = useState(false);
  const [groqKeyInput, setGroqKeyInput] = useState('');
  const [groqSaving, setGroqSaving] = useState(false);
  const [groqSaved, setGroqSaved] = useState(false);

  // Image generation
  const [selectedImageProvider, setSelectedImageProvider] = useState('gpt-image-1.5');
  const [imageKeyInputs, setImageKeyInputs] = useState<Record<string, string>>({});
  const [imageKeySaving, setImageKeySaving] = useState<string | null>(null);
  const [imageKeySaved, setImageKeySaved] = useState<string | null>(null);

  // Web search
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);
  const [webSearchLoading, setWebSearchLoading] = useState(false);

  // Memory settings
  const [autoExtractEntities, setAutoExtractEntities] = useState(true);

  // Profile settings
  const [profile, setProfile] = useState<api.UserProfile | null>(null);
  const [profileForm, setProfileForm] = useState({
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

  // Working directory
  const [workingDir, setWorkingDir] = useState<string | null>(null);

  // Stats
  const [stats, setStats] = useState<api.Stats | null>(null);

  // Load settings on open
  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  // Refresh stats (for CRM sync callback)
  async function refreshStats() {
    try {
      const statsData = await api.getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to refresh stats:', err);
    }
  }

  async function loadSettings() {
    setLoading(true);
    try {
      const [keys, llmConfig, preferences, statsData, profileData, workingDirData, ollamaStatusData, groqKeyStatus, webSearchStatus] = await Promise.all([
        api.getApiKeys(),
        api.getLLMConfig().catch(() => ({ provider: 'anthropic', model: 'claude-sonnet-4-5-20250929', available_models: [] })),
        api.getPreferences().catch(() => ({})),
        api.getStats().catch(() => null),
        api.getProfile().catch(() => null),
        api.getWorkingDirectory().catch(() => ({ path: null, exists: false })),
        api.getOllamaStatus().catch(() => null),
        api.hasGroqKey().catch(() => false),
        api.getWebSearchStatus().catch(() => ({ enabled: true })),
      ]);

      setApiKeys(keys);
      setSelectedProvider(llmConfig.provider as api.LLMProvider);
      setSelectedModel(llmConfig.model);
      setStats(statsData);
      setProfile(profileData);
      setWorkingDir(workingDirData?.path || null);
      setHasGroqKey(groqKeyStatus);
      setWebSearchEnabled(webSearchStatus.enabled);

      // Ollama status
      if (ollamaStatusData) {
        setOllamaStatus(ollamaStatusData);
        if (ollamaStatusData.available && ollamaStatusData.models.length > 0) {
          setOllamaModels(ollamaStatusData.models.map(m => m.name));
        }
      }

      // Initialize profile form
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

      // Load saved preferences
      if (preferences && typeof preferences === 'object') {
        const prefs = preferences as Record<string, unknown>;
        if ('auto_extract_entities' in prefs && typeof prefs.auto_extract_entities === 'boolean') {
          setAutoExtractEntities(prefs.auto_extract_entities);
        }
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveApiKey() {
    if (!apiKeyInput.trim()) {
      setError('Veuillez entrer une clé API');
      return;
    }

    // Find provider config
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
      setApiKeyInput('');

      // Reset saved status after delay
      setTimeout(() => {
        setSaved(false);
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveGroqKey() {
    if (!groqKeyInput.trim()) {
      setError('Veuillez entrer une clé API Groq');
      return;
    }

    // Groq API keys start with "gsk_"
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

      setTimeout(() => {
        setGroqSaved(false);
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setGroqSaving(false);
    }
  }

  async function handleSaveImageKey(apiKeyId: 'openai_image' | 'gemini_image') {
    const keyInput = imageKeyInputs[apiKeyId] || '';
    if (!keyInput.trim()) {
      setError('Veuillez entrer une clé API');
      return;
    }

    // Validate format
    const provider = IMAGE_PROVIDERS.find(p => p.apiKeyId === apiKeyId);
    if (provider && !keyInput.startsWith(provider.keyPrefix)) {
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

      setTimeout(() => {
        setImageKeySaved(null);
      }, 3000);
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
      console.error('Failed to toggle web search:', err);
    } finally {
      setWebSearchLoading(false);
    }
  }

  async function handleSelectProvider(provider: api.LLMProvider) {
    setSelectedProvider(provider);

    // Get default model for provider
    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    // For Ollama, use first available model
    if (provider === 'ollama' && ollamaModels.length > 0) {
      defaultModel = ollamaModels[0];
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
      // Save the LLM config
      try {
        await api.setLLMConfig(provider, defaultModel);
      } catch (err) {
        console.error('Failed to save LLM config:', err);
      }
    }
  }

  async function handleSelectModel(modelId: string) {
    setSelectedModel(modelId);
    try {
      await api.setLLMConfig(selectedProvider, modelId);
    } catch (err) {
      console.error('Failed to save LLM config:', err);
    }
  }

  async function handleToggleAutoExtract() {
    const newValue = !autoExtractEntities;
    setAutoExtractEntities(newValue);
    try {
      await api.setPreference('auto_extract_entities', newValue, 'memory');
    } catch (err) {
      console.error('Failed to save preference:', err);
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

      setTimeout(() => {
        setProfileSaved(false);
      }, 3000);
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
      console.error('Failed to set working directory:', err);
    }
  }

  // Handle escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-3xl bg-surface border border-border rounded-xl shadow-2xl z-50 max-h-[85vh] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <h2 className="text-lg font-semibold text-text">Paramètres</h2>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border/50 shrink-0 overflow-x-auto scrollbar-hide">
              <button
                onClick={() => setActiveTab('profile')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'profile'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <User className="w-4 h-4" />
                Profil
              </button>
              <button
                onClick={() => setActiveTab('api')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'api'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Cpu className="w-4 h-4" />
                LLM
              </button>
              <button
                onClick={() => setActiveTab('tools')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'tools'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Wrench className="w-4 h-4" />
                Tools
              </button>
              <button
                onClick={() => setActiveTab('data')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'data'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Database className="w-4 h-4" />
                Données
              </button>
              <button
                onClick={() => setActiveTab('accessibility')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'accessibility'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Accessibility className="w-4 h-4" />
                A11Y
              </button>
              <button
                onClick={() => setActiveTab('performance')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'performance'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Gauge className="w-4 h-4" />
                Perf
              </button>
              <button
                onClick={() => setActiveTab('escalation')}
                className={`shrink-0 flex items-center justify-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'escalation'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <AlertTriangle className="w-4 h-4" />
                Limites
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
                </div>
              ) : activeTab === 'profile' ? (
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
              ) : activeTab === 'tools' ? (
                <ToolsPanel onError={setError} />
              ) : activeTab === 'api' ? (
                <LLMConfigTab
                  selectedProvider={selectedProvider}
                  selectedModel={selectedModel}
                  apiKeys={apiKeys}
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
                  autoExtractEntities={autoExtractEntities}
                  onToggleAutoExtract={handleToggleAutoExtract}
                  // Groq Voice props
                  hasGroqKey={hasGroqKey}
                  groqKeyInput={groqKeyInput}
                  setGroqKeyInput={setGroqKeyInput}
                  groqSaving={groqSaving}
                  groqSaved={groqSaved}
                  onSaveGroqKey={handleSaveGroqKey}
                  // Web search props
                  webSearchEnabled={webSearchEnabled}
                  webSearchLoading={webSearchLoading}
                  onToggleWebSearch={handleToggleWebSearch}
                  // Image generation props
                  selectedImageProvider={selectedImageProvider}
                  onSelectImageProvider={setSelectedImageProvider}
                  imageKeyInputs={imageKeyInputs}
                  setImageKeyInputs={setImageKeyInputs}
                  imageKeySaving={imageKeySaving}
                  imageKeySaved={imageKeySaved}
                  onSaveImageKey={handleSaveImageKey}
                />
              ) : activeTab === 'accessibility' ? (
                <AccessibilityTab />
              ) : activeTab === 'performance' ? (
                <PerformanceTab />
              ) : activeTab === 'escalation' ? (
                <EscalationTab />
              ) : (
                <DataTab
                  stats={stats}
                  workingDir={workingDir}
                  onSelectWorkingDir={handleSelectWorkingDir}
                  onRefreshStats={refreshStats}
                />
              )}
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-border/50 shrink-0">
              <Button variant="ghost" onClick={onClose}>
                Fermer
              </Button>
              {activeTab === 'profile' && (
                <Button
                  variant="primary"
                  onClick={handleSaveProfile}
                  disabled={profileSaving || !profileForm.name.trim()}
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

// Profile Tab
function ProfileTab({
  profileForm,
  setProfileForm,
  profile,
  saving: _saving,
  saved,
  error,
  setError,
  onSave: _onSave,
  onImport,
}: {
  profileForm: {
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
  };
  setProfileForm: (form: typeof profileForm | ((prev: typeof profileForm) => typeof profileForm)) => void;
  profile: api.UserProfile | null;
  saving: boolean;
  saved: boolean;
  error: string | null;
  setError: (e: string | null) => void;
  onSave: () => void;
  onImport: () => void;
}) {
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

      {/* Status */}
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

      {/* Form fields */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-text-muted mb-1 block">Nom complet *</label>
            <input
              type="text"
              value={profileForm.name}
              onChange={(e) => {
                setProfileForm((prev) => ({ ...prev, name: e.target.value }));
                setError(null);
              }}
              placeholder="Ludovic Sanchez"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Surnom</label>
            <input
              type="text"
              value={profileForm.nickname}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, nickname: e.target.value }))}
              placeholder="Ludo"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-text-muted mb-1 block">Entreprise</label>
            <input
              type="text"
              value={profileForm.company}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="Synoptïa"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Rôle</label>
            <input
              type="text"
              value={profileForm.role}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, role: e.target.value }))}
              placeholder="Entrepreneur IA"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-text-muted mb-1 block">Email</label>
            <input
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="ludo@synoptia.fr"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Localisation</label>
            <input
              type="text"
              value={profileForm.location}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, location: e.target.value }))}
              placeholder="Manosque, France"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
        </div>

        {/* Facturation */}
        <div>
          <label className="text-xs text-text-muted mb-1 block">Adresse (facturation)</label>
          <input
            type="text"
            value={profileForm.address}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, address: e.target.value }))}
            placeholder="294 Montee des Genets, 04100 Manosque"
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-text-muted mb-1 block">SIREN</label>
            <input
              type="text"
              value={profileForm.siren}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, siren: e.target.value }))}
              placeholder="991 606 781"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">TVA intracommunautaire</label>
            <input
              type="text"
              value={profileForm.tva_intra}
              onChange={(e) => setProfileForm((prev) => ({ ...prev, tva_intra: e.target.value }))}
              placeholder="FR 08 991 606 781"
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-text-muted mb-1 block">Contexte additionnel</label>
          <textarea
            value={profileForm.context}
            onChange={(e) => setProfileForm((prev) => ({ ...prev, context: e.target.value }))}
            placeholder="Infos supplémentaires sur ton activité, tes projets en cours..."
            rows={3}
            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 resize-none"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}

      {/* Success */}
      {saved && (
        <p className="text-sm text-green-400 flex items-center gap-1">
          <Check className="w-3 h-3" />
          Profil enregistré
        </p>
      )}

      {/* Help text */}
      <p className="text-xs text-text-muted">
        Tu peux aussi importer ton profil depuis un fichier THERESE.md
      </p>
    </div>
  );
}

// LLM Configuration Tab (replaces API Key + Model tabs)
function LLMConfigTab({
  selectedProvider,
  selectedModel,
  apiKeys,
  apiKeyInput,
  setApiKeyInput,
  showApiKey,
  setShowApiKey,
  ollamaStatus,
  ollamaModels,
  saving,
  saved,
  error,
  setError,
  onSelectProvider,
  onSelectModel,
  onSaveApiKey,
  autoExtractEntities,
  onToggleAutoExtract,
  // Groq Voice props
  hasGroqKey,
  groqKeyInput,
  setGroqKeyInput,
  groqSaving,
  groqSaved,
  onSaveGroqKey,
  // Web search props
  webSearchEnabled,
  webSearchLoading,
  onToggleWebSearch,
  // Image generation props
  selectedImageProvider,
  onSelectImageProvider,
  imageKeyInputs,
  setImageKeyInputs,
  imageKeySaving,
  imageKeySaved,
  onSaveImageKey,
}: {
  selectedProvider: api.LLMProvider;
  selectedModel: string;
  apiKeys: Record<string, boolean>;
  apiKeyInput: string;
  setApiKeyInput: (v: string) => void;
  showApiKey: boolean;
  setShowApiKey: (v: boolean) => void;
  ollamaStatus: api.OllamaStatus | null;
  ollamaModels: string[];
  saving: boolean;
  saved: boolean;
  error: string | null;
  setError: (v: string | null) => void;
  onSelectProvider: (provider: api.LLMProvider) => void;
  onSelectModel: (modelId: string) => void;
  onSaveApiKey: () => void;
  autoExtractEntities: boolean;
  onToggleAutoExtract: () => void;
  // Groq Voice props
  hasGroqKey: boolean;
  groqKeyInput: string;
  setGroqKeyInput: (v: string) => void;
  groqSaving: boolean;
  groqSaved: boolean;
  onSaveGroqKey: () => void;
  // Web search props
  webSearchEnabled: boolean;
  webSearchLoading: boolean;
  onToggleWebSearch: () => void;
  // Image generation props
  selectedImageProvider: string;
  onSelectImageProvider: (provider: string) => void;
  imageKeyInputs: Record<string, string>;
  setImageKeyInputs: (v: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void;
  imageKeySaving: string | null;
  imageKeySaved: string | null;
  onSaveImageKey: (apiKeyId: 'openai_image' | 'gemini_image') => void;
}) {
  const currentProviderConfig = PROVIDERS.find(p => p.id === selectedProvider);
  const hasApiKey = apiKeys[selectedProvider] === true;
  const needsApiKey = selectedProvider !== 'ollama';

  // Get models for current provider
  const availableModels: { id: string; name: string; badge?: string }[] = selectedProvider === 'ollama'
    ? ollamaModels.map(name => ({ id: name, name }))
    : currentProviderConfig?.models || [];

  return (
    <div className="space-y-6">
      {/* Provider Selection */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Fournisseur LLM</h3>
            <p className="text-xs text-text-muted">Choisissez votre fournisseur d'IA</p>
          </div>
        </div>

        <div className="space-y-2">
          {PROVIDERS.map((provider) => {
            const isAvailable = provider.id === 'ollama'
              ? ollamaStatus?.available
              : true;
            const providerHasKey = apiKeys[provider.id] === true;

            return (
              <button
                key={provider.id}
                onClick={() => onSelectProvider(provider.id)}
                disabled={!isAvailable && provider.id === 'ollama'}
                className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left ${
                  selectedProvider === provider.id
                    ? 'bg-accent-cyan/10 border-accent-cyan/50'
                    : 'bg-background/40 border-border/50 hover:border-border'
                } ${!isAvailable && provider.id === 'ollama' ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                    selectedProvider === provider.id
                      ? 'border-accent-cyan bg-accent-cyan'
                      : 'border-border'
                  }`}
                >
                  {selectedProvider === provider.id && (
                    <div className="w-1.5 h-1.5 rounded-full bg-background" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-text">{provider.name}</span>
                    {provider.id === 'anthropic' && (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-accent-cyan/20 text-accent-cyan">
                        Recommandé
                      </span>
                    )}
                    {provider.id === 'ollama' && !isAvailable && (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400">
                        Non disponible
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-muted mt-0.5">{provider.description}</p>
                </div>
                {provider.id !== 'ollama' && (
                  <div className={`shrink-0 ${providerHasKey ? 'text-green-400' : 'text-text-muted'}`}>
                    {providerHasKey ? <Check className="w-4 h-4" /> : <Key className="w-4 h-4" />}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* API Key Input (not for Ollama) */}
      {needsApiKey && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-magenta/20 to-accent-cyan/20 flex items-center justify-center">
              <Key className="w-5 h-5 text-accent-magenta" />
            </div>
            <div>
              <h3 className="font-medium text-text">Clé API {currentProviderConfig?.name}</h3>
              <p className="text-xs text-text-muted">
                {hasApiKey ? 'Clé configurée' : 'Nécessaire pour utiliser ce fournisseur'}
              </p>
            </div>
          </div>

          {/* Status */}
          {hasApiKey ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
              <Check className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-400">Clé API configurée</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
              <AlertCircle className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-yellow-400">Aucune clé API configurée</span>
            </div>
          )}

          {/* Input + Save */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKeyInput}
                  onChange={(e) => {
                    setApiKeyInput(e.target.value);
                    setError(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && apiKeyInput.trim()) {
                      onSaveApiKey();
                    }
                  }}
                  placeholder={currentProviderConfig?.keyPlaceholder || '...'}
                  className="w-full px-4 py-2.5 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
                >
                  {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <Button
                variant="primary"
                onClick={onSaveApiKey}
                disabled={saving || !apiKeyInput.trim()}
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
              </Button>
            </div>

            {/* Error */}
            {error && (
              <p className="text-sm text-red-400 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {error}
              </p>
            )}

            {/* Success */}
            {saved && (
              <p className="text-sm text-green-400 flex items-center gap-1">
                <Check className="w-3 h-3" />
                Clé API enregistrée
              </p>
            )}

            {/* Help link */}
            {currentProviderConfig?.consoleUrl && (
              <p className="text-xs text-text-muted">
                Obtenez votre clé sur{' '}
                <a
                  href={currentProviderConfig.consoleUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-cyan hover:underline"
                >
                  {new URL(currentProviderConfig.consoleUrl).hostname}
                </a>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Ollama Status */}
      {selectedProvider === 'ollama' && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500/20 to-accent-cyan/20 flex items-center justify-center">
              <Database className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <h3 className="font-medium text-text">Ollama Local</h3>
              <p className="text-xs text-text-muted">
                {ollamaStatus?.available
                  ? `${ollamaModels.length} modèle(s) disponible(s)`
                  : 'Démarrez Ollama pour utiliser des modèles locaux'}
              </p>
            </div>
          </div>

          {ollamaStatus?.available ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
              <Check className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-400">Ollama connecté ({ollamaStatus.base_url})</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">
                {ollamaStatus?.error || 'Ollama non disponible'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Model Selection */}
      {availableModels.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <label className="text-sm text-text-muted">Modèle</label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors"
          >
            {availableModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} {model.badge ? `(${model.badge})` : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Groq Voice Transcription */}
      <div className="space-y-3 pt-4 border-t border-border/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-magenta/20 to-accent-cyan/20 flex items-center justify-center">
            <Mic className="w-5 h-5 text-accent-magenta" />
          </div>
          <div>
            <h3 className="font-medium text-text">Transcription vocale</h3>
            <p className="text-xs text-text-muted">
              Clé API Groq pour la transcription audio (Whisper)
            </p>
          </div>
        </div>

        {/* Groq Status */}
        {hasGroqKey ? (
          <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
            <Check className="w-4 h-4 text-green-400" />
            <span className="text-sm text-green-400">Clé Groq configurée - Dictée vocale active</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <AlertCircle className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-yellow-400">Clé Groq non configurée - Dictée vocale désactivée</span>
          </div>
        )}

        {/* Groq Input */}
        <div className="space-y-2">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={groqKeyInput}
                onChange={(e) => {
                  setGroqKeyInput(e.target.value);
                  setError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && groqKeyInput.trim()) {
                    onSaveGroqKey();
                  }
                }}
                placeholder="gsk_..."
                className="w-full px-4 py-2.5 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/50 transition-colors font-mono"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
              >
                {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <Button
              variant="primary"
              onClick={onSaveGroqKey}
              disabled={groqSaving || !groqKeyInput.trim()}
            >
              {groqSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
            </Button>
          </div>

          {/* Groq Success */}
          {groqSaved && (
            <p className="text-sm text-green-400 flex items-center gap-1">
              <Check className="w-3 h-3" />
              Clé Groq enregistrée
            </p>
          )}

          {/* Help link */}
          <p className="text-xs text-text-muted">
            Obtenez votre clé sur{' '}
            <a
              href="https://console.groq.com/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent-cyan hover:underline"
            >
              console.groq.com
            </a>
            {' '}- Gratuit, rapide, excellent en français
          </p>
        </div>
      </div>

      {/* Web Search */}
      <div className="space-y-3 pt-4 border-t border-border/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Globe className="w-5 h-5 text-accent-cyan" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-text">Recherche Web</h3>
            <p className="text-xs text-text-muted">
              Permet aux LLMs de chercher sur le web à la demande
            </p>
          </div>
          <button
            onClick={onToggleWebSearch}
            disabled={webSearchLoading}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              webSearchEnabled ? 'bg-accent-cyan' : 'bg-surface-elevated'
            } ${webSearchLoading ? 'opacity-50' : ''}`}
          >
            <span
              className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                webSearchEnabled ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
        <div className="text-xs text-text-muted space-y-1 pl-13 ml-[52px]">
          <p>• <strong>Gemini</strong> : Google Search Grounding (natif)</p>
          <p>• <strong>Claude, GPT, Mistral, Grok</strong> : DuckDuckGo (tool calling)</p>
        </div>
      </div>

      {/* Image Generation */}
      <div className="space-y-3 pt-4 border-t border-border/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <ImageIcon className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Génération d'images</h3>
            <p className="text-xs text-text-muted">
              Clés API dédiées pour la génération d'images
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {IMAGE_PROVIDERS.map((provider) => {
            const hasImageKey = apiKeys[provider.apiKeyId] === true;
            const keyInput = imageKeyInputs[provider.apiKeyId] || '';
            const isSaving = imageKeySaving === provider.apiKeyId;
            const isSaved = imageKeySaved === provider.apiKeyId;

            return (
              <div key={provider.id} className="space-y-2">
                {/* Provider header with radio */}
                <button
                  onClick={() => onSelectImageProvider(provider.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left ${
                    selectedImageProvider === provider.id
                      ? 'bg-accent-cyan/10 border-accent-cyan/50'
                      : 'bg-background/40 border-border/50 hover:border-border'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                      selectedImageProvider === provider.id
                        ? 'border-accent-cyan bg-accent-cyan'
                        : 'border-border'
                    }`}
                  >
                    {selectedImageProvider === provider.id && (
                      <div className="w-1.5 h-1.5 rounded-full bg-background" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-text">{provider.name}</span>
                      {hasImageKey ? (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400">
                          Clé {provider.keyName} OK
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-400">
                          Clé {provider.keyName} requise
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-text-muted mt-0.5">{provider.description}</p>
                  </div>
                </button>

                {/* API Key input for this provider */}
                <div className="pl-7 space-y-2">
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={keyInput}
                        onChange={(e) => {
                          setImageKeyInputs(prev => ({ ...prev, [provider.apiKeyId]: e.target.value }));
                          setError(null);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && keyInput.trim()) {
                            onSaveImageKey(provider.apiKeyId);
                          }
                        }}
                        placeholder={provider.keyPlaceholder}
                        className="w-full px-3 py-2 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 transition-colors font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <Button
                      variant="primary"
                      onClick={() => onSaveImageKey(provider.apiKeyId)}
                      disabled={isSaving || !keyInput.trim()}
                    >
                      {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
                    </Button>
                  </div>

                  {/* Success message */}
                  {isSaved && (
                    <p className="text-sm text-green-400 flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      Clé {provider.keyName} enregistrée
                    </p>
                  )}

                  {/* Help link */}
                  <p className="text-xs text-text-muted">
                    Obtenez votre clé sur{' '}
                    <a
                      href={provider.consoleUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent-cyan hover:underline"
                    >
                      {new URL(provider.consoleUrl).hostname}
                    </a>
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Info about separate keys */}
        <p className="text-xs text-text-muted italic">
          Ces clés sont distinctes des clés LLM. Vous pouvez utiliser des projets/comptes différents pour le chat et la génération d'images.
        </p>
      </div>

      {/* Auto-extract toggle */}
      <div className="pt-4 border-t border-border/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-accent-cyan" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-text">Extraction automatique</h3>
            <p className="text-xs text-text-muted">
              Extraire automatiquement les contacts et projets des conversations
            </p>
          </div>
          <button
            onClick={onToggleAutoExtract}
            className={`w-12 h-6 rounded-full p-1 transition-colors ${
              autoExtractEntities ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transition-transform ${
                autoExtractEntities ? 'translate-x-6' : ''
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}

// Data Tab
function DataTab({
  stats,
  workingDir,
  onSelectWorkingDir,
  onRefreshStats,
}: {
  stats: api.Stats | null;
  workingDir: string | null;
  onSelectWorkingDir: () => void;
  onRefreshStats?: () => void;
}) {
  return (
    <div className="space-y-6">
      {/* Local Storage Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Database className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Stockage des données</h3>
            <p className="text-xs text-text-muted">
              Vos données sont stockées localement sur votre machine
            </p>
          </div>
        </div>

        {/* Working Directory */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm text-text-muted">Dossier de travail</label>
            <Button variant="ghost" size="sm" onClick={onSelectWorkingDir}>
              <FolderOpen className="w-4 h-4 mr-2" />
              Parcourir
            </Button>
          </div>
          <div className="p-3 bg-background/40 rounded-lg border border-border/30">
            <p className="text-xs text-text font-mono truncate">
              {workingDir || 'Non configuré'}
            </p>
          </div>
        </div>

        {stats ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Conversations" value={stats.entities.conversations} />
              <StatCard label="Messages" value={stats.entities.messages} />
              <StatCard label="Contacts" value={stats.entities.contacts} />
              <StatCard label="Projets" value={stats.entities.projects} />
            </div>

            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xs text-text-muted mb-1">Emplacement de la base</p>
              <p className="text-xs text-text font-mono truncate">{stats.db_path}</p>
            </div>

            <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">
                  Données stockées localement - 100% privé
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-background/40 rounded-lg border border-border/30 text-center">
            <p className="text-sm text-text-muted">Statistiques non disponibles</p>
          </div>
        )}
      </div>

      {/* Separator */}
      <div className="border-t border-border/30" />

      {/* Demo Mode Section */}
      <DemoModeSection />

      {/* Separator */}
      <div className="border-t border-border/30" />

      {/* CRM Sync Section */}
      <CRMSyncPanel onSyncComplete={onRefreshStats} />
    </div>
  );
}

// Demo Mode Section
function DemoModeSection() {
  const demoEnabled = useDemoStore((s) => s.enabled);
  const toggleDemo = useDemoStore((s) => s.toggle);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          demoEnabled
            ? 'bg-accent-cyan/20'
            : 'bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20'
        }`}>
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
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-accent-cyan flex-shrink-0" />
            <span className="text-sm text-accent-cyan">
              Mode démo actif - les données réelles sont masquées
            </span>
          </div>
          <p className="text-xs text-text-muted mt-1.5">
            Raccourci : ⌘⇧D pour activer/désactiver
          </p>
        </div>
      )}

      <p className="text-xs text-text-muted/60">
        Idéal pour les vidéos de présentation et les démos en direct.
        Aucune donnée n'est modifiée en base.
      </p>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="p-3 bg-background/40 rounded-lg border border-border/30">
      <p className="text-2xl font-bold text-text">{value.toLocaleString('fr-FR')}</p>
      <p className="text-xs text-text-muted">{label}</p>
    </div>
  );
}

// Accessibility Tab (US-A11Y-01 to US-A11Y-05)
function AccessibilityTab() {
  const {
    reduceMotion,
    setReduceMotion,
    fontSize,
    setFontSize,
    highContrast,
    setHighContrast,
    showKeyboardHints,
    setShowKeyboardHints,
  } = useAccessibilityStore();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <Accessibility className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="font-medium text-text">Accessibilité</h3>
          <p className="text-xs text-text-muted">
            Personnalisez l'interface pour vos besoins
          </p>
        </div>
      </div>

      {/* Reduce Motion (US-A11Y-04) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="reduce-motion" className="text-sm font-medium text-text">
              Réduire les animations
            </label>
            <p className="text-xs text-text-muted">
              Désactive les animations pour les utilisateurs photosensibles
            </p>
          </div>
          <button
            id="reduce-motion"
            role="switch"
            aria-checked={reduceMotion}
            onClick={() => setReduceMotion(!reduceMotion)}
            className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              reduceMotion ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                reduceMotion ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Font Size */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-text">Taille de police</label>
        <div className="flex gap-2" role="radiogroup" aria-label="Taille de police">
          {(['small', 'medium', 'large'] as const).map((size) => (
            <button
              key={size}
              role="radio"
              aria-checked={fontSize === size}
              onClick={() => setFontSize(size)}
              className={`flex-1 py-2 px-3 rounded-lg border text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan ${
                fontSize === size
                  ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan'
                  : 'bg-background/40 border-border/30 text-text-muted hover:border-border'
              }`}
            >
              {size === 'small' ? 'Petite' : size === 'medium' ? 'Moyenne' : 'Grande'}
            </button>
          ))}
        </div>
      </div>

      {/* High Contrast (US-A11Y-03) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="high-contrast" className="text-sm font-medium text-text">
              Contraste élevé
            </label>
            <p className="text-xs text-text-muted">
              Augmente le contraste pour une meilleure lisibilité
            </p>
          </div>
          <button
            id="high-contrast"
            role="switch"
            aria-checked={highContrast}
            onClick={() => setHighContrast(!highContrast)}
            className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              highContrast ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                highContrast ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Keyboard Hints (US-A11Y-01, US-A11Y-05) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="keyboard-hints" className="text-sm font-medium text-text">
              Afficher les raccourcis clavier
            </label>
            <p className="text-xs text-text-muted">
              Affiche les indications de raccourcis dans l'interface
            </p>
          </div>
          <button
            id="keyboard-hints"
            role="switch"
            aria-checked={showKeyboardHints}
            onClick={() => setShowKeyboardHints(!showKeyboardHints)}
            className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              showKeyboardHints ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                showKeyboardHints ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Info box */}
      <div className="p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <div className="flex items-start gap-2">
          <Accessibility className="w-4 h-4 text-accent-cyan mt-0.5" />
          <div className="text-sm text-accent-cyan">
            <p className="font-medium">Raccourcis clavier disponibles</p>
            <ul className="mt-1 text-xs space-y-0.5 text-accent-cyan/80">
              <li>⌘+K : Palette de commandes</li>
              <li>⌘+B : Conversations</li>
              <li>⌘+M : Mémoire</li>
              <li>⌘+D : Board de décision</li>
              <li>Tab / Shift+Tab : Navigation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

// Performance Tab (US-PERF-01 to US-PERF-05)
function PerformanceTab() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<api.PerformanceStatus | null>(null);
  const [cleaningUp, setCleaningUp] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setLoading(true);
    try {
      const data = await api.getPerformanceStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load performance status:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCleanup() {
    setCleaningUp(true);
    try {
      await api.triggerMemoryCleanup();
      await loadStatus();
    } catch (err) {
      console.error('Cleanup failed:', err);
    } finally {
      setCleaningUp(false);
    }
  }

  async function handleToggleBatterySaver() {
    if (!status) return;
    try {
      const newEnabled = !status.power.battery_saver_mode;
      await api.setBatterySaver(newEnabled);
      await loadStatus();
    } catch (err) {
      console.error('Failed to toggle battery saver:', err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <Gauge className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="font-medium text-text">Performances</h3>
          <p className="text-xs text-text-muted">
            Monitoring et optimisation
          </p>
        </div>
      </div>

      {/* Streaming Metrics (US-PERF-01) */}
      {status?.streaming && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-text">Temps de réponse</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.streaming.avg_first_token_ms?.toFixed(0) || '–'} ms
              </p>
              <p className="text-xs text-text-muted">Premier token (moyenne)</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.streaming.p95_first_token_ms?.toFixed(0) || '–'} ms
              </p>
              <p className="text-xs text-text-muted">Premier token (P95)</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">{status.streaming.total_requests}</p>
              <p className="text-xs text-text-muted">Requêtes totales</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">{status.streaming.total_tokens?.toLocaleString('fr-FR') || 0}</p>
              <p className="text-xs text-text-muted">Tokens générés</p>
            </div>
          </div>
          {/* SLA Status */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
            status.streaming.meets_sla
              ? 'bg-green-500/10 border border-green-500/20'
              : 'bg-yellow-500/10 border border-yellow-500/20'
          }`}>
            {status.streaming.meets_sla ? (
              <>
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">SLA respecté ({"<"} 2s)</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-yellow-400">SLA non respecté ({">"} 2s)</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Memory Management (US-PERF-03) */}
      {status?.memory && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-text">Mémoire</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCleanup}
              disabled={cleaningUp}
            >
              {cleaningUp ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Nettoyer'
              )}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.memory.uptime_hours.toFixed(1)}h
              </p>
              <p className="text-xs text-text-muted">Uptime</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-2xl font-bold text-text">
                {status.memory.last_cleanup_ago_minutes.toFixed(0)} min
              </p>
              <p className="text-xs text-text-muted">Dernier nettoyage</p>
            </div>
          </div>
        </div>
      )}

      {/* Battery Saver (US-PERF-05) */}
      {status?.power && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-text">Mode économie d'énergie</h4>
              <p className="text-xs text-text-muted">
                Réduit les vérifications et animations pour économiser la batterie
              </p>
            </div>
            <button
              onClick={handleToggleBatterySaver}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                status.power.battery_saver_mode ? 'bg-accent-cyan' : 'bg-border'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                  status.power.battery_saver_mode ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2 bg-background/40 rounded border border-border/30">
              <span className="text-text-muted">Health check : </span>
              <span className="text-text">{status.power.health_check_interval}s</span>
            </div>
            <div className="p-2 bg-background/40 rounded border border-border/30">
              <span className="text-text-muted">Animations : </span>
              <span className="text-text">{status.power.reduce_animations ? 'Réduites' : 'Normales'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Conversations count */}
      {status?.conversations_total !== undefined && (
        <div className="pt-4 border-t border-border/30">
          <div className="p-3 bg-background/40 rounded-lg border border-border/30">
            <p className="text-2xl font-bold text-text">{status.conversations_total}</p>
            <p className="text-xs text-text-muted">Conversations indexées</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Escalation Tab (US-ESC-01 to US-ESC-05)
function EscalationTab() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<api.EscalationStatus | null>(null);
  const [limits, setLimits] = useState<api.TokenLimits | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [statusData, limitsData] = await Promise.all([
        api.getEscalationStatus(),
        api.getTokenLimits(),
      ]);
      setStatus(statusData);
      setLimits(limitsData);
    } catch (err) {
      console.error('Failed to load escalation data:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveLimits() {
    if (!limits) return;
    setSaving(true);
    try {
      await api.setTokenLimits(limits);
      await loadData();
    } catch (err) {
      console.error('Failed to save limits:', err);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
      </div>
    );
  }

  // Calculate usage percentages
  const dailyInputPercent = limits && status?.daily_usage
    ? Math.min(100, (status.daily_usage.input_tokens / limits.daily_input_limit) * 100)
    : 0;
  const monthlyBudgetPercent = limits && status?.monthly_usage
    ? Math.min(100, (status.monthly_usage.cost_eur / limits.monthly_budget_eur) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="font-medium text-text">Limites & Consommation</h3>
          <p className="text-xs text-text-muted">
            Contrôle des coûts et de l'utilisation des tokens
          </p>
        </div>
      </div>

      {/* Daily Usage (US-ESC-04) */}
      {status?.daily_usage && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-text">Usage aujourd'hui</h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {(status.daily_usage.input_tokens / 1000).toFixed(1)}K
              </p>
              <p className="text-xs text-text-muted">Tokens entrée</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {(status.daily_usage.output_tokens / 1000).toFixed(1)}K
              </p>
              <p className="text-xs text-text-muted">Tokens sortie</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {status.daily_usage.cost_eur.toFixed(2)} €
              </p>
              <p className="text-xs text-text-muted">Coût</p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-text-muted">
              <span>Limite quotidienne</span>
              <span>{dailyInputPercent.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-background rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  dailyInputPercent > 90 ? 'bg-red-500' : dailyInputPercent > 75 ? 'bg-yellow-500' : 'bg-accent-cyan'
                }`}
                style={{ width: `${dailyInputPercent}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Monthly Usage */}
      {status?.monthly_usage && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <h4 className="text-sm font-medium text-text">Usage ce mois</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {(status.monthly_usage.input_tokens / 1000).toFixed(1)}K
              </p>
              <p className="text-xs text-text-muted">Tokens totaux</p>
            </div>
            <div className="p-3 bg-background/40 rounded-lg border border-border/30">
              <p className="text-xl font-bold text-text">
                {status.monthly_usage.cost_eur.toFixed(2)} €
              </p>
              <p className="text-xs text-text-muted">Coût total</p>
            </div>
          </div>
          {/* Budget progress */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-text-muted">
              <span>Budget mensuel ({limits?.monthly_budget_eur || 50} €)</span>
              <span>{monthlyBudgetPercent.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-background rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  monthlyBudgetPercent > 90 ? 'bg-red-500' : monthlyBudgetPercent > 75 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${monthlyBudgetPercent}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Limits Configuration (US-ESC-03) */}
      {limits && (
        <div className="space-y-3 pt-4 border-t border-border/30">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-text">Limites configurables</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSaveLimits}
              disabled={saving}
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-text-muted mb-1 block">Max tokens/requête (entrée)</label>
              <input
                type="number"
                value={limits.max_input_tokens}
                onChange={(e) => setLimits({ ...limits, max_input_tokens: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Max tokens/requête (sortie)</label>
              <input
                type="number"
                value={limits.max_output_tokens}
                onChange={(e) => setLimits({ ...limits, max_output_tokens: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Limite quotidienne (tokens)</label>
              <input
                type="number"
                value={limits.daily_input_limit}
                onChange={(e) => setLimits({ ...limits, daily_input_limit: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">Budget mensuel (€)</label>
              <input
                type="number"
                step="0.01"
                value={limits.monthly_budget_eur}
                onChange={(e) => setLimits({ ...limits, monthly_budget_eur: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Alerter à (% du budget)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={limits.warn_at_percentage}
              onChange={(e) => setLimits({ ...limits, warn_at_percentage: parseInt(e.target.value) || 80 })}
              className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            />
          </div>
        </div>
      )}

      {/* Info */}
      <div className="p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-accent-cyan mt-0.5" />
          <div className="text-sm text-accent-cyan">
            <p className="font-medium">Indicateurs IA (US-ESC-01)</p>
            <p className="text-xs text-accent-cyan/80 mt-1">
              THÉRÈSE détecte automatiquement quand l'IA n'est pas sûre de sa réponse et l'indique dans la conversation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
