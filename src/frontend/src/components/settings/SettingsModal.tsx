// Modal Paramètres - Shell principal avec navigation par onglets
// Les onglets sont extraits dans des composants séparés pour la maintenabilité

import { useState, useEffect } from 'react';
import { X, Cpu, Database, User, Wrench, Accessibility, Gauge, AlertTriangle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { open } from '@tauri-apps/plugin-dialog';
import { Button } from '../ui/Button';
import { modalVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';

// Composants des onglets
import { ProfileTab, ProfileFormData } from './ProfileTab';
import { LLMTab, PROVIDERS, IMAGE_PROVIDERS } from './LLMTab';
import { DataTab } from './DataTab';
import { AccessibilityTab } from './AccessibilityTab';
import { PerformanceTab } from './PerformanceTab';
import { LimitsTab } from './LimitsTab';
import { ToolsPanel } from './ToolsPanel';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = 'profile' | 'api' | 'tools' | 'data' | 'accessibility' | 'performance' | 'personalisation' | 'escalation';

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Configuration LLM
  const [selectedProvider, setSelectedProvider] = useState<api.LLMProvider>('anthropic');
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-5-20250929');
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  // Ollama
  const [ollamaStatus, setOllamaStatus] = useState<api.OllamaStatus | null>(null);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);

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

  // Rafraîchissement des stats (callback sync CRM)
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

      // Statut Ollama
      if (ollamaStatusData) {
        setOllamaStatus(ollamaStatusData);
        if (ollamaStatusData.available && ollamaStatusData.models.length > 0) {
          setOllamaModels(ollamaStatusData.models.map(m => m.name));
        }
      }

      // Initialisation du formulaire profil
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

      // Chargement des préférences sauvegardées
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

  async function handleSaveApiKey() {
    if (!apiKeyInput.trim()) {
      setError('Veuillez entrer une clé API');
      return;
    }

    // Vérification du format de la clé
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

    // Les clés Groq commencent par "gsk_"
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

    // Validation du format
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
      console.error('Échec du changement recherche web:', err);
    } finally {
      setWebSearchLoading(false);
    }
  }

  async function handleSelectProvider(provider: api.LLMProvider) {
    setSelectedProvider(provider);

    // Modèle par défaut pour le provider sélectionné
    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    // Pour Ollama, utiliser le premier modèle disponible
    if (provider === 'ollama' && ollamaModels.length > 0) {
      defaultModel = ollamaModels[0];
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
      try {
        await api.setLLMConfig(provider, defaultModel);
      } catch (err) {
        console.error('Échec de la sauvegarde de la config LLM:', err);
      }
    }
  }

  async function handleSelectModel(modelId: string) {
    setSelectedModel(modelId);
    try {
      await api.setLLMConfig(selectedProvider, modelId);
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
            {/* En-tête */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 shrink-0">
              <h2 className="text-lg font-semibold text-text">Paramètres</h2>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Onglets */}
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

            {/* Contenu */}
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
                <LLMTab
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
                  // Props transcription vocale Groq
                  hasGroqKey={hasGroqKey}
                  groqKeyInput={groqKeyInput}
                  setGroqKeyInput={setGroqKeyInput}
                  groqSaving={groqSaving}
                  groqSaved={groqSaved}
                  onSaveGroqKey={handleSaveGroqKey}
                  // Props recherche web
                  webSearchEnabled={webSearchEnabled}
                  webSearchLoading={webSearchLoading}
                  onToggleWebSearch={handleToggleWebSearch}
                  // Props génération d'images
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
                <LimitsTab />
              ) : (
                <DataTab
                  stats={stats}
                  workingDir={workingDir}
                  onSelectWorkingDir={handleSelectWorkingDir}
                  onRefreshStats={refreshStats}
                />
              )}
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
