// Onglet configuration LLM - Paramètres THERESE
// Sélection provider, clé API, modèle, transcription vocale, recherche web, images, extraction auto

import { useState } from 'react';
import { Key, Check, AlertCircle, XCircle, Loader2, Eye, EyeOff, Cpu, Database, RefreshCw, Plus } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';

// Configuration des providers LLM
export interface ProviderConfig {
  id: api.LLMProvider;
  name: string;
  description: string;
  keyPrefix?: string;
  keyPlaceholder?: string;
  consoleUrl?: string;
  models: { id: string; name: string; badge?: string }[];
}

export const PROVIDERS: ProviderConfig[] = [
  {
    id: 'anthropic',
    name: 'Claude (Anthropic)',
    description: 'Recommandé - Excellent coding et français',
    keyPrefix: 'sk-ant-',
    keyPlaceholder: 'sk-ant-...',
    consoleUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      { id: 'claude-opus-4-6', name: 'Claude Opus 4.6', badge: 'Flagship' },
      { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6', badge: 'Recommandé' },
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
    description: 'Gemini 3.1 - Contexte 1M tokens',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      { id: 'gemini-3.1-pro-preview', name: 'Gemini 3.1 Pro', badge: 'Flagship' },
      { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash', badge: 'Rapide' },
      { id: 'gemini-3.1-flash-lite-preview', name: 'Gemini 3.1 Flash Lite', badge: 'Économique' },
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
      { id: 'mistral-large-latest', name: 'Mistral Large 3', badge: 'Flagship' },
      { id: 'mistral-large-2512', name: 'Mistral Large 3 (fixé)', badge: 'Stable' },
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
    id: 'openrouter',
    name: 'OpenRouter',
    description: 'Accès unifié à 200+ modèles (Claude, GPT, Gemini, Llama...)',
    keyPrefix: 'sk-or-',
    keyPlaceholder: 'sk-or-v1-...',
    consoleUrl: 'https://openrouter.ai/keys',
    models: [
      { id: 'anthropic/claude-sonnet-4-6', name: 'Claude Sonnet 4.6', badge: 'Recommandé' },
      { id: 'anthropic/claude-opus-4-6', name: 'Claude Opus 4.6', badge: 'Premium' },
      { id: 'openai/gpt-5.2', name: 'GPT-5.2' },
      { id: 'google/gemini-3.1-pro', name: 'Gemini 3.1 Pro' },
      { id: 'nvidia/nemotron-3-super-120b-a12b', name: 'Nemotron 3 Super 120B', badge: 'NVIDIA' },
      { id: 'nvidia/nemotron-3-nano-30b-a3b', name: 'Nemotron 3 Nano 30B', badge: 'Économique' },
      { id: 'meta-llama/llama-4-maverick', name: 'Llama 4 Maverick', badge: 'Open Source' },
    ],
  },
  {
    id: 'perplexity',
    name: 'Perplexity',
    description: 'Recherche augmentée par IA (Sonar)',
    keyPrefix: 'pplx-',
    keyPlaceholder: 'pplx-...',
    consoleUrl: 'https://www.perplexity.ai/settings/api',
    models: [
      { id: 'sonar-pro', name: 'Sonar Pro', badge: 'Recherche' },
      { id: 'sonar', name: 'Sonar', badge: 'Rapide' },
      { id: 'sonar-reasoning-pro', name: 'Sonar Reasoning Pro', badge: 'Raisonnement' },
      { id: 'sonar-reasoning', name: 'Sonar Reasoning' },
    ],
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek V3 et R1 (raisonnement)',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.deepseek.com/api_keys',
    models: [
      { id: 'deepseek-chat', name: 'DeepSeek Chat', badge: 'V3' },
      { id: 'deepseek-reasoner', name: 'DeepSeek Reasoner', badge: 'R1' },
    ],
  },
  {
    id: 'infomaniak',
    name: 'Infomaniak AI',
    description: 'IA souveraine suisse - serveurs en Suisse, RGPD',
    keyPlaceholder: 'Ton token API Infomaniak...',
    consoleUrl: 'https://www.infomaniak.com/fr/hebergement/ai-tools',
    models: [
      { id: 'mix', name: 'Mix', badge: 'Polyvalent' },
      { id: 'mix-large', name: 'Mix Large', badge: 'Puissant' },
    ],
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: '100% local - Aucune clé API requise',
    models: [], // Chargé dynamiquement
  },
];

// Configuration des providers de génération d'images
export interface ImageProviderConfig {
  id: string;
  name: string;
  description: string;
  apiKeyId: 'openai_image' | 'gemini_image' | 'fal';
  keyName: string;
  keyPrefix: string;
  keyPlaceholder: string;
  consoleUrl: string;
}

export const IMAGE_PROVIDERS: ImageProviderConfig[] = [
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
    name: 'Nano Banana 2',
    description: 'Génération d\'images Google Gemini',
    apiKeyId: 'gemini_image',
    keyName: 'Gemini (Image)',
    keyPrefix: 'AIza',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
  },
  {
    id: 'fal-flux-pro',
    name: 'Fal Flux Pro',
    description: 'Génération d\'images rapide (Flux Pro v1.1)',
    apiKeyId: 'fal',
    keyName: 'Fal',
    keyPrefix: '',
    keyPlaceholder: 'Clé API Fal...',
    consoleUrl: 'https://fal.ai/dashboard/keys',
  },
];

export interface LLMTabProps {
  selectedProvider: api.LLMProvider;
  selectedModel: string;
  apiKeys: Record<string, boolean>;
  corruptedKeys?: string[];
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
  // BUG-049 : re-tester la disponibilité Ollama à la demande
  onRetestOllama?: () => void;
  retestingOllama?: boolean;
}

export function LLMTab({
  selectedProvider,
  selectedModel,
  apiKeys,
  corruptedKeys = [],
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
  onRetestOllama,
  retestingOllama = false,
}: LLMTabProps) {
  const currentProviderConfig = PROVIDERS.find(p => p.id === selectedProvider);
  const hasApiKey = apiKeys[selectedProvider] === true;
  const needsApiKey = selectedProvider !== 'ollama';

  // Modèles disponibles pour le provider sélectionné
  const availableModels: { id: string; name: string; badge?: string }[] = selectedProvider === 'ollama'
    ? ollamaModels.map(name => ({ id: name, name }))
    : currentProviderConfig?.models || [];

  return (
    <div className="space-y-6">
      {/* Sélection du provider */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h3 className="font-medium text-text">Fournisseur LLM</h3>
            <p className="text-xs text-text-muted">Choisis ton fournisseur d'IA</p>
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
                  <div className={`shrink-0 ${corruptedKeys.includes(provider.id) ? 'text-red-400' : providerHasKey ? 'text-green-400' : 'text-text-muted'}`}>
                    {corruptedKeys.includes(provider.id) ? <XCircle className="w-4 h-4" /> : providerHasKey ? <Check className="w-4 h-4" /> : <Key className="w-4 h-4" />}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Saisie clé API (pas pour Ollama) */}
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

          {/* Statut */}
          {corruptedKeys.includes(selectedProvider) ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
              <XCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">Clé API corrompue - ressaisis-la</span>
            </div>
          ) : hasApiKey ? (
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

          {/* Input + Sauvegarder */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <label htmlFor="settings-api-key" className="sr-only">Clé API</label>
                <input
                  id="settings-api-key"
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
                  className="w-full px-4 py-2.5 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors font-mono"
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
                Clé API enregistrée
              </p>
            )}

            {/* Lien d'aide */}
            {currentProviderConfig?.consoleUrl && (
              <p className="text-xs text-text-muted">
                Obtiens ta clé sur{' '}
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

      {/* Statut Ollama */}
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

          <div className="flex items-center gap-2">
            {ollamaStatus?.available ? (
              <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg flex-1">
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Ollama connecté ({ollamaStatus.base_url})</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg flex-1">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-sm text-red-400">
                  {ollamaStatus?.error || 'Ollama non disponible'}
                </span>
              </div>
            )}
            {/* BUG-049 : bouton Re-tester pour forcer un re-check sans recharger les paramètres */}
            {onRetestOllama && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onRetestOllama}
                disabled={retestingOllama}
                title="Re-tester la connexion Ollama"
                className="shrink-0"
              >
                <RefreshCw className={`w-4 h-4 ${retestingOllama ? 'animate-spin' : ''}`} />
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Sélection du modèle - BUG-084 : ajout modèle custom */}
      <ModelSelector
        availableModels={availableModels}
        selectedModel={selectedModel}
        onSelectModel={onSelectModel}
        selectedProvider={selectedProvider}
      />

    </div>
  );
}


// BUG-084 : Composant séparé pour la sélection de modèle avec option custom
function ModelSelector({
  availableModels,
  selectedModel,
  onSelectModel,
  selectedProvider,
}: {
  availableModels: { id: string; name: string; badge?: string }[];
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  selectedProvider: string;
}) {
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customModelId, setCustomModelId] = useState('');

  // Vérifier si le modèle sélectionné est dans la liste prédéfinie
  const isCustomModel = selectedModel && !availableModels.some(m => m.id === selectedModel);

  function handleAddCustomModel() {
    const trimmed = customModelId.trim();
    if (!trimmed) return;
    onSelectModel(trimmed);
    setCustomModelId('');
    setShowCustomInput(false);
  }

  if (availableModels.length === 0 && selectedProvider !== 'ollama') {
    return null;
  }

  return (
    <div className="space-y-3 pt-4 border-t border-border/30">
      <div className="flex items-center justify-between">
        <label className="text-sm text-text-muted">Modèle</label>
        {selectedProvider !== 'ollama' && (
          <button
            onClick={() => setShowCustomInput(!showCustomInput)}
            className="flex items-center gap-1 text-xs text-accent-cyan hover:text-accent-cyan/80 transition-colors"
            title="Utiliser un identifiant de modèle personnalisé"
          >
            <Plus className="w-3 h-3" />
            Custom
          </button>
        )}
      </div>

      <select
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
        className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors [&>option]:bg-[#0B1226] [&>option]:text-[#E6EDF7]"
        style={{ backgroundColor: 'var(--color-background, #0B1226)', color: 'var(--color-text, #E6EDF7)' }}
      >
        {availableModels.map((model) => (
          <option key={model.id} value={model.id} style={{ backgroundColor: '#0B1226', color: '#E6EDF7' }}>
            {model.name} {model.badge ? `(${model.badge})` : ''}
          </option>
        ))}
        {isCustomModel && (
          <option value={selectedModel} style={{ backgroundColor: '#0B1226', color: '#E6EDF7' }}>
            {selectedModel} (personnalisé)
          </option>
        )}
      </select>

      {/* Champ de saisie modèle personnalisé */}
      {showCustomInput && (
        <div className="space-y-2">
          <p className="text-xs text-text-muted">
            Saisis l'identifiant exact du modèle tel qu'il apparait dans l'API du fournisseur.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={customModelId}
              onChange={(e) => setCustomModelId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && customModelId.trim()) {
                  handleAddCustomModel();
                }
              }}
              placeholder={
                selectedProvider === 'anthropic' ? 'claude-sonnet-4-6-20260407' :
                selectedProvider === 'openai' ? 'gpt-5.2-turbo' :
                selectedProvider === 'openrouter' ? 'anthropic/claude-opus-4-6' :
                'identifiant-du-modele'
              }
              className="flex-1 px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 font-mono"
            />
            <Button
              variant="primary"
              size="sm"
              onClick={handleAddCustomModel}
              disabled={!customModelId.trim()}
            >
              Utiliser
            </Button>
          </div>
        </div>
      )}

      {isCustomModel && (
        <p className="text-xs text-accent-cyan flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          Modèle personnalisé actif : {selectedModel}
        </p>
      )}
    </div>
  );
}
