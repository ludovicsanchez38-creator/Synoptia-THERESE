// Onglet configuration LLM - Paramètres THÉRÈSE
// Sélection provider, clé API, modèle, transcription vocale, recherche web, images, extraction auto

import { Key, Check, AlertCircle, Loader2, Eye, EyeOff, Cpu, Database, Sparkles, Mic, Image as ImageIcon, Globe } from 'lucide-react';
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
    id: 'openrouter',
    name: 'OpenRouter',
    description: 'Accès unifié à 200+ modèles (Claude, GPT, Gemini, Llama...)',
    keyPrefix: 'sk-or-',
    keyPlaceholder: 'sk-or-v1-...',
    consoleUrl: 'https://openrouter.ai/keys',
    models: [
      { id: 'anthropic/claude-sonnet-4-5', name: 'Claude Sonnet 4.5', badge: 'Recommandé' },
      { id: 'anthropic/claude-opus-4-6', name: 'Claude Opus 4.6', badge: 'Premium' },
      { id: 'openai/gpt-5.2', name: 'GPT-5.2' },
      { id: 'google/gemini-3-pro', name: 'Gemini 3 Pro' },
      { id: 'meta-llama/llama-4-maverick', name: 'Llama 4 Maverick', badge: 'Open Source' },
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
    name: 'Nano Banana Pro',
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
  // Props transcription vocale Groq
  hasGroqKey: boolean;
  groqKeyInput: string;
  setGroqKeyInput: (v: string) => void;
  groqSaving: boolean;
  groqSaved: boolean;
  onSaveGroqKey: () => void;
  // Props recherche web
  webSearchEnabled: boolean;
  webSearchLoading: boolean;
  onToggleWebSearch: () => void;
  // Props génération d'images
  selectedImageProvider: string;
  onSelectImageProvider: (provider: string) => void;
  imageKeyInputs: Record<string, string>;
  setImageKeyInputs: (v: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void;
  imageKeySaving: string | null;
  imageKeySaved: string | null;
  onSaveImageKey: (apiKeyId: 'openai_image' | 'gemini_image' | 'fal') => void;
}

export function LLMTab({
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
  // Props transcription vocale Groq
  hasGroqKey,
  groqKeyInput,
  setGroqKeyInput,
  groqSaving,
  groqSaved,
  onSaveGroqKey,
  // Props recherche web
  webSearchEnabled,
  webSearchLoading,
  onToggleWebSearch,
  // Props génération d'images
  selectedImageProvider,
  onSelectImageProvider,
  imageKeyInputs,
  setImageKeyInputs,
  imageKeySaving,
  imageKeySaved,
  onSaveImageKey,
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

      {/* Sélection du modèle */}
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

      {/* Transcription vocale Groq */}
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

        {/* Statut Groq */}
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

        {/* Saisie clé Groq */}
        <div className="space-y-2">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <label htmlFor="settings-groq-key" className="sr-only">Clé API Groq</label>
              <input
                id="settings-groq-key"
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
              onClick={onSaveGroqKey}
              disabled={groqSaving || !groqKeyInput.trim()}
            >
              {groqSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
            </Button>
          </div>

          {/* Succès Groq */}
          {groqSaved && (
            <p className="text-sm text-green-400 flex items-center gap-1">
              <Check className="w-3 h-3" />
              Clé Groq enregistrée
            </p>
          )}

          {/* Lien d'aide */}
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

      {/* Recherche Web */}
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

      {/* Génération d'images */}
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
                {/* En-tête provider avec radio */}
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

                {/* Saisie clé API pour ce provider */}
                <div className="pl-7 space-y-2">
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <label htmlFor={`settings-image-key-${provider.apiKeyId}`} className="sr-only">Clé API {provider.keyName}</label>
                      <input
                        id={`settings-image-key-${provider.apiKeyId}`}
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
                        className="w-full px-3 py-2 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors font-mono"
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

                  {/* Message de succès */}
                  {isSaved && (
                    <p className="text-sm text-green-400 flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      Clé {provider.keyName} enregistrée
                    </p>
                  )}

                  {/* Lien d'aide */}
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

        {/* Info sur les clés séparées */}
        <p className="text-xs text-text-muted italic">
          Ces clés sont distinctes des clés LLM. Vous pouvez utiliser des projets/comptes différents pour le chat et la génération d'images.
        </p>
      </div>

      {/* Toggle extraction automatique */}
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
