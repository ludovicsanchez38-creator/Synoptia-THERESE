/**
 * THERESE v2 - LLM Step
 *
 * Third step of the onboarding wizard - Configure LLM provider and API key.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Key, Check, AlertCircle, Eye, EyeOff, Loader2, AlertTriangle } from 'lucide-react';
import * as api from '../../services/api';
import { Button } from '../ui/Button';

interface LLMStepProps {
  onNext: () => void;
  onBack: () => void;
}

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
    description: 'Recommandé - Excellent pour le français',
    keyPrefix: 'sk-ant-',
    keyPlaceholder: 'sk-ant-...',
    consoleUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      { id: 'claude-sonnet-4-5-20250929', name: 'Claude 4.5 Sonnet', badge: 'Recommandé' },
      { id: 'claude-haiku-4-5-20251001', name: 'Claude 4.5 Haiku', badge: 'Rapide' },
      { id: 'claude-opus-4-6', name: 'Claude 4.6 Opus', badge: 'Premium' },
    ],
  },
  {
    id: 'openai',
    name: 'GPT (OpenAI)',
    description: 'Polyvalent et puissant',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.openai.com/api-keys',
    models: [
      { id: 'gpt-5.2', name: 'GPT-5.2', badge: 'Recommandé' },
      { id: 'gpt-5', name: 'GPT-5' },
      { id: 'o3', name: 'o3', badge: 'Reasoning' },
      { id: 'o3-mini', name: 'o3 Mini', badge: 'Économique' },
    ],
  },
  {
    id: 'gemini',
    name: 'Gemini (Google)',
    description: 'Contexte très long (1M tokens)',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash', badge: 'Recommandé' },
      { id: 'gemini-3-pro-preview', name: 'Gemini 3 Pro', badge: 'Flagship' },
      { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
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
      { id: 'mistral-large-latest', name: 'Mistral Large', badge: 'Puissant' },
      { id: 'codestral-latest', name: 'Codestral', badge: 'Code' },
      { id: 'mistral-small-latest', name: 'Mistral Small', badge: 'Économique' },
    ],
  },
  {
    id: 'grok',
    name: 'Grok (xAI)',
    description: 'IA de xAI (Elon Musk)',
    keyPrefix: 'xai-',
    keyPlaceholder: 'xai-...',
    consoleUrl: 'https://console.x.ai',
    models: [
      { id: 'grok-4', name: 'Grok 4', badge: 'Flagship' },
      { id: 'grok-4-1-fast-non-reasoning', name: 'Grok 4.1 Fast', badge: 'Rapide' },
      { id: 'grok-3-beta', name: 'Grok 3', badge: 'Économique' },
    ],
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: '100% local - Aucune clé API requise',
    models: [],
  },
];

export function LLMStep({ onNext, onBack }: LLMStepProps) {
  const [selectedProvider, setSelectedProvider] = useState<api.LLMProvider>('anthropic');
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-5-20250929');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [ollamaStatus, setOllamaStatus] = useState<api.OllamaStatus | null>(null);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load initial state
  useEffect(() => {
    async function loadState() {
      try {
        const [keys, ollamaStatusData] = await Promise.all([
          api.getApiKeys().catch(() => ({})),
          api.getOllamaStatus().catch(() => null),
        ]);
        setApiKeys(keys);
        if (ollamaStatusData) {
          setOllamaStatus(ollamaStatusData);
          if (ollamaStatusData.available && ollamaStatusData.models.length > 0) {
            setOllamaModels(ollamaStatusData.models.map(m => m.name));
          }
        }
      } catch (err) {
        console.error('Failed to load LLM state:', err);
      } finally {
        setLoading(false);
      }
    }
    loadState();
  }, []);

  const currentProviderConfig = PROVIDERS.find(p => p.id === selectedProvider);
  const hasApiKey = apiKeys[selectedProvider] === true;
  const needsApiKey = selectedProvider !== 'ollama';

  const availableModels: { id: string; name: string; badge?: string }[] = selectedProvider === 'ollama'
    ? ollamaModels.map(name => ({ id: name, name }))
    : currentProviderConfig?.models || [];

  async function handleSaveApiKey() {
    if (!apiKeyInput.trim()) {
      setError('Veuillez entrer une clé API');
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
      setApiKeyInput('');
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  async function handleSelectProvider(provider: api.LLMProvider) {
    setSelectedProvider(provider);
    setError(null);
    setSaved(false);

    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    if (provider === 'ollama' && ollamaModels.length > 0) {
      defaultModel = ollamaModels[0];
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
    }
  }

  async function handleContinue() {
    // Save LLM config
    try {
      await api.setLLMConfig(selectedProvider, selectedModel);
      onNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la configuration');
    }
  }

  // Note: canContinue is computed inline in the render for button disabled state
  function _canContinue() {
    if (selectedProvider === 'ollama') {
      return ollamaStatus?.available && ollamaModels.length > 0;
    }
    // Check apiKeys state directly (updated after save) OR just saved
    return apiKeys[selectedProvider] === true || saved;
  }
  void _canContinue; // suppress unused warning

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-accent-cyan" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col px-8 py-6 h-full overflow-y-auto"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
          <Cpu className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-text">Choisis ton LLM</h2>
          <p className="text-sm text-text-muted">Configure le modèle d'IA à utiliser</p>
        </div>
      </div>

      {/* Provider Selection */}
      <div
        role="radiogroup"
        aria-label="Sélection du provider LLM"
        className="space-y-2 mb-6 max-h-48 overflow-y-auto"
      >
        {PROVIDERS.map((provider) => {
          const isAvailable = provider.id === 'ollama' ? ollamaStatus?.available : true;
          const providerHasKey = apiKeys[provider.id] === true;
          const isSelected = selectedProvider === provider.id;

          return (
            <button
              key={provider.id}
              role="radio"
              aria-checked={isSelected}
              onClick={() => handleSelectProvider(provider.id)}
              disabled={!isAvailable && provider.id === 'ollama'}
              className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left focus:outline-none focus:ring-2 focus:ring-accent-cyan ${
                isSelected
                  ? 'bg-accent-cyan/10 border-accent-cyan/50'
                  : 'bg-background/40 border-border/50 hover:border-border'
              } ${!isAvailable && provider.id === 'ollama' ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div
                className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                  isSelected
                    ? 'border-accent-cyan bg-accent-cyan'
                    : 'border-border'
                }`}
              >
                {isSelected && (
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

      {/* API Key Input (not for Ollama) */}
      {needsApiKey && selectedProvider && (
        <div className="space-y-3 mb-6 pt-4 border-t border-border/30">
          {hasApiKey ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
              <Check className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-400">Clé API configurée</span>
            </div>
          ) : (
            <>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <label htmlFor="llm-api-key" className="sr-only">Clé API {currentProviderConfig?.name}</label>
                  <input
                    id="llm-api-key"
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKeyInput}
                    onChange={(e) => {
                      setApiKeyInput(e.target.value);
                      setError(null);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && apiKeyInput.trim()) {
                        handleSaveApiKey();
                      }
                    }}
                    placeholder={currentProviderConfig?.keyPlaceholder || 'Clé API...'}
                    className="w-full px-4 py-2.5 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/70 focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors font-mono"
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
                  onClick={handleSaveApiKey}
                  disabled={saving || !apiKeyInput.trim()}
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
                </Button>
              </div>

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
            </>
          )}

          {saved && (
            <div className="flex items-center gap-2 text-sm text-green-400">
              <Check className="w-3 h-3" />
              Clé API enregistrée
            </div>
          )}
        </div>
      )}

      {/* Model Selection */}
      {availableModels.length > 0 && (
        <div className="mb-6">
          <label htmlFor="llm-model" className="text-sm text-text-muted mb-2 block">Modèle</label>
          <select
            id="llm-model"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors"
          >
            {availableModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} {model.badge ? `(${model.badge})` : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 mb-6 bg-red-500/10 border border-red-500/20 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span className="text-sm text-red-400">{error}</span>
        </div>
      )}

      {/* Warning if no API key configured */}
      {needsApiKey && !hasApiKey && (
        <div className="flex items-center gap-2 px-3 py-2 mb-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />
          <span className="text-sm text-yellow-400">
            Sans clé API, THÉRÈSE ne pourra pas fonctionner. Configure une clé ou utilise Ollama.
          </span>
        </div>
      )}

      {/* Footer */}
      <div className="flex justify-between pt-4 border-t border-border/30">
        <Button variant="ghost" onClick={onBack}>
          Retour
        </Button>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={onNext}>
            Passer
          </Button>
          <Button
            variant="primary"
            onClick={handleContinue}
            disabled={needsApiKey && !hasApiKey}
            title={needsApiKey && !hasApiKey ? 'Configure une clé API ou clique sur "Passer"' : undefined}
          >
            Continuer
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
