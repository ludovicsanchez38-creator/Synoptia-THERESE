// Onglet configuration LLM - Paramètres THERESE
// Sélection provider, clé API, modèle, transcription vocale, recherche web, images, extraction auto

import { useEffect, useState } from 'react';
import { Key, Check, AlertCircle, XCircle, Eye, EyeOff, Cpu, Database, RefreshCw, Plus } from 'lucide-react';
import { Button } from '../ui/Button';
import * as api from '../../services/api';
import type { LLMEffort } from '../../services/api/config';
import { LocalModelFeasibility } from '../llm/LocalModelFeasibility';
import { FOURNISSEURS as PROVIDERS, chargerCatalogue, type ModeleDecore } from '../../lib/catalogueModeles';
import { handleRovingFocus } from '../../lib/rovingFocus';

// Configuration des providers LLM - catalogue centralisé (dette 0.43.4) :
// la liste statique vit dans lib/catalogueModeles, la liste dynamique vient
// du backend. Ré-exports pour ne pas casser les importeurs existants.
export type { FournisseurConfig as ProviderConfig } from '../../lib/catalogueModeles';
export { FOURNISSEURS as PROVIDERS } from '../../lib/catalogueModeles';
import { Spinner } from '../ui/Spinner';

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
    id: 'gpt-image-2',
    name: 'GPT Image 2',
    description: 'Génération d\'images OpenAI (gpt-image-2)',
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
    // BUG-099 : pas de préfixe imposé (les clés Gemini peuvent commencer par 'AIza' ou 'AQ')
    keyPrefix: '',
    keyPlaceholder: 'Clé API Gemini...',
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
  systemResources: api.SystemResources | null;
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
  systemResources,
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

  // Catalogue dynamique (dette 0.43.4) : la LISTE vient du backend, la liste
  // statique du fournisseur ne sert plus que de repli hors-ligne.
  const [catalogueDynamique, setCatalogueDynamique] = useState<ModeleDecore[] | null>(null);
  useEffect(() => {
    setCatalogueDynamique(null);
    if (selectedProvider === 'ollama') return;
    let annule = false;
    void chargerCatalogue(selectedProvider).then((modeles) => {
      if (!annule) setCatalogueDynamique(modeles);
    });
    return () => { annule = true; };
  }, [selectedProvider]);

  // Adresse personnalisée Qwen : l'adresse d'espace de travail est propre au
  // compte - sans elle, le fournisseur ne peut pas fonctionner.
  const [baseUrlInput, setBaseUrlInput] = useState('');
  const [baseUrlSaved, setBaseUrlSaved] = useState(false);
  const [savingBaseUrl, setSavingBaseUrl] = useState(false);
  useEffect(() => {
    setBaseUrlSaved(false);
    if (selectedProvider !== 'qwen') return;
    let annule = false;
    void api.getLLMConfig().then((config) => {
      if (!annule && config.provider === 'qwen') setBaseUrlInput(config.base_url ?? '');
    }).catch(() => {});
    return () => { annule = true; };
  }, [selectedProvider]);

  async function handleSaveBaseUrl() {
    setSavingBaseUrl(true);
    setError(null);
    try {
      await api.setLLMConfig(selectedProvider, selectedModel, undefined, baseUrlInput.trim());
      setBaseUrlSaved(true);
      setTimeout(() => setBaseUrlSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'enregistrement de l'adresse");
    } finally {
      setSavingBaseUrl(false);
    }
  }

  // Modèles disponibles pour le provider sélectionné
  const availableModels: { id: string; name: string; badge?: string }[] = selectedProvider === 'ollama'
    ? ollamaModels.map(name => ({ id: name, name }))
    : catalogueDynamique ?? (currentProviderConfig?.models || []);

  return (
    <div className="space-y-6">
      {/* Sélection du provider */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-sm bg-accent-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
            <Cpu className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-medium text-text">Fournisseur LLM</h3>
            <p className="text-xs text-text-muted">Choisis ton fournisseur d'IA</p>
          </div>
        </div>

        <div className="space-y-2" role="radiogroup" aria-label="Fournisseur LLM">
          {PROVIDERS.map((provider) => {
            const isAvailable = provider.id === 'ollama'
              ? ollamaStatus?.available
              : true;
            const providerHasKey = apiKeys[provider.id] === true;

            return (
              <button
                key={provider.id}
                type="button"
                role="radio"
                aria-checked={selectedProvider === provider.id}
                tabIndex={selectedProvider === provider.id ? 0 : -1}
                onClick={() => onSelectProvider(provider.id)}
                onKeyDown={(event) => handleRovingFocus(event, '[role="radio"]', 'vertical')}
                disabled={!isAvailable && provider.id === 'ollama'}
                className={`w-full flex items-center gap-3 p-3 rounded-md border transition-all text-left ${
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
                      <span className="px-2 py-0.5 rounded-sm text-xs font-medium bg-accent-cyan/20 text-accent-cyan-ink">
                        Recommandé
                      </span>
                    )}
                    {provider.id === 'ollama' && !isAvailable && (
                      <span className="px-2 py-0.5 rounded-sm text-xs font-medium bg-[var(--color-error-tint)] text-error">
                        Non disponible
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-muted mt-0.5">{provider.description}</p>
                </div>
                {provider.id !== 'ollama' && (
                  <div className={`shrink-0 ${corruptedKeys.includes(provider.id) ? 'text-error' : providerHasKey ? 'text-success' : 'text-text-muted'}`}>
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
            <div className="w-10 h-10 rounded-sm bg-domaine-factures-tint border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
              <Key className="w-5 h-5 text-accent-magenta-ink" />
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
            <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-error-tint)] border border-error/40 rounded-md">
              <XCircle className="w-4 h-4 text-error" />
              <span className="text-sm text-error">Clé API corrompue - ressaisis-la</span>
            </div>
          ) : hasApiKey ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-success-tint)] border border-success/40 rounded-md">
              <Check className="w-4 h-4 text-success" />
              <span className="text-sm text-success">Clé API configurée</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-warning-tint)] border border-warning/40 rounded-md">
              <AlertCircle className="w-4 h-4 text-warning" />
              <span className="text-sm text-warning">Aucune clé API configurée</span>
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
                  className="w-full px-4 py-2.5 pr-10 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  aria-label={showApiKey ? 'Masquer la clé API' : 'Afficher la clé API'}
                  aria-pressed={showApiKey}
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
                {saving ? <Spinner taille="bouton" /> : 'Sauver'}
              </Button>
            </div>

            {/* Erreur */}
            {error && (
              <p className="text-sm text-error flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {error}
              </p>
            )}

            {/* Succès */}
            {saved && (
              <p role="status" className="text-sm text-success flex items-center gap-1">
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
                  className="text-accent-cyan-ink hover:underline"
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
            <div className="w-10 h-10 rounded-sm bg-[var(--color-success-tint)] border-[1.5px] border-[var(--btn-ink)] flex items-center justify-center">
              <Database className="w-5 h-5 text-success" />
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
              <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-success-tint)] border border-success/40 rounded-md flex-1">
                <Check className="w-4 h-4 text-success" />
                <span className="text-sm text-success">Ollama connecté ({ollamaStatus.base_url})</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-error-tint)] border border-error/40 rounded-md flex-1">
                <AlertCircle className="w-4 h-4 text-error" />
                <span className="text-sm text-error">
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
                aria-label="Re-tester la connexion Ollama"
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

      {/* Adresse d'espace de travail Qwen (dette 0.43.4) : l'URL contient
          l'identifiant du compte, le défaut ne peut fonctionner pour personne. */}
      {selectedProvider === 'qwen' && (
        <div className="space-y-2 p-3 rounded-sm border-[1.5px] border-border bg-surface">
          <label htmlFor="qwen-base-url" className="text-sm font-medium text-text">
            Adresse de ton espace de travail
          </label>
          <p className="text-xs text-text-muted">
            Dans Alibaba Model Studio, copie l'adresse « compatible-mode/v1 » de ton
            espace de travail. Sans elle, Qwen ne peut pas répondre.
          </p>
          <div className="flex gap-2">
            <input
              id="qwen-base-url"
              type="url"
              value={baseUrlInput}
              onChange={(e) => setBaseUrlInput(e.target.value)}
              placeholder="https://ton-espace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
              className="flex-1 px-3 py-2 text-sm rounded-sm border-[1.5px] border-border bg-background text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
            <Button
              onClick={() => void handleSaveBaseUrl()}
              disabled={savingBaseUrl || !baseUrlInput.trim()}
              size="sm"
            >
              {savingBaseUrl ? <Spinner taille="bouton" /> : baseUrlSaved ? <Check className="w-4 h-4" /> : 'Enregistrer'}
            </Button>
          </div>
        </div>
      )}
      {selectedProvider === 'ollama' && selectedModel && (
        <LocalModelFeasibility
          model={ollamaStatus?.models.find((model) => model.name === selectedModel)}
          resources={systemResources}
        />
      )}

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
        <label htmlFor="settings-llm-model" className="text-sm text-text-muted">Modèle</label>
        {selectedProvider !== 'ollama' && (
          <button
            onClick={() => setShowCustomInput(!showCustomInput)}
            className="flex items-center gap-1 text-xs text-accent-cyan-ink hover:text-accent-cyan-ink transition-colors"
            title="Utiliser un identifiant de modèle personnalisé"
          >
            <Plus className="w-3 h-3" />
            Custom
          </button>
        )}
      </div>

      <select
        id="settings-llm-model"
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
        className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-md text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors [&>option]:bg-surface [&>option]:text-text"
      >
        {availableModels.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name} {model.badge ? `(${model.badge})` : ''}
          </option>
        ))}
        {isCustomModel && (
          <option value={selectedModel}>
            {selectedModel} (personnalisé)
          </option>
        )}
      </select>

      {/* Effort de raisonnement (10/07/2026) - applique uniquement aux
          modeles au support verifie (Fable/Sonnet 5/4.6/Opus 4.5+, GPT-5.6,
          Grok 4.5, Ollama thinking) ; Auto = defaut du serveur. */}
      <EffortSelector selectedProvider={selectedProvider} selectedModel={selectedModel} />

      {/* Champ de saisie modèle personnalisé */}
      {showCustomInput && (
        <div className="space-y-2">
          <p className="text-xs text-text-muted">
            Saisis l'identifiant exact du modèle tel qu'il apparait dans l'API du fournisseur.
          </p>
          <div className="flex gap-2">
            <input aria-label="Identifiant du modèle personnalisé"
              type="text"
              value={customModelId}
              onChange={(e) => setCustomModelId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && customModelId.trim()) {
                  handleAddCustomModel();
                }
              }}
              placeholder={
                selectedProvider === 'anthropic' ? 'claude-opus-4-8' :
                selectedProvider === 'openai' ? 'gpt-5.5' :
                selectedProvider === 'openrouter' ? 'anthropic/claude-opus-4-8' :
                'identifiant-du-modele'
              }
              className="flex-1 px-3 py-2 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 font-mono"
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
        <p className="text-xs text-accent-cyan-ink flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          Modèle personnalisé actif : {selectedModel}
        </p>
      )}
    </div>
  );
}


const EFFORT_OPTIONS = [
  { value: 'auto', label: 'Auto (défaut du modèle)' },
  { value: 'low', label: 'Faible - rapide et économique' },
  { value: 'medium', label: 'Moyen' },
  { value: 'high', label: 'Élevé - raisonnement approfondi' },
  { value: 'max', label: 'Maximal - le plus lent, le plus fiable' },
] as const;

function EffortSelector({
  selectedProvider,
  selectedModel,
}: {
  selectedProvider: string;
  selectedModel: string;
}) {
  const [effort, setEffort] = useState<string>('auto');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [failedEffort, setFailedEffort] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getLLMConfig()
      .then((cfg) => {
        if (!cancelled) setEffort(cfg.effort || 'auto');
      })
      .catch((reason) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : 'Effort de raisonnement indisponible.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleChange(value: string) {
    const previous = effort;
    setEffort(value);
    setSaving(true);
    setError(null);
    setStatus('Enregistrement de l’effort…');
    setFailedEffort(null);
    try {
      await api.setLLMConfig(
        selectedProvider as api.LLMProvider,
        selectedModel,
        value as LLMEffort
      );
      setStatus('Effort de raisonnement enregistré.');
    } catch (err) {
      setEffort(previous);
      setStatus(null);
      setFailedEffort(value);
      setError(err instanceof Error ? err.message : 'L’effort de raisonnement n’a pas pu être enregistré.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <div>
        <label htmlFor="llm-effort" className="text-sm text-text-muted">
          Effort de raisonnement
        </label>
        <p className="text-xs text-text-muted">
          Appliqué aux modèles qui le gèrent (Claude récents, GPT-5.6, Grok 4.5,
          modèles Ollama « thinking »). Auto laisse le modèle décider.
        </p>
        </div>
        <select
        id="llm-effort"
        value={effort}
        disabled={saving}
        onChange={(e) => void handleChange(e.target.value)}
        className="px-3 py-2 bg-background/60 border border-border/50 rounded-md text-sm text-text focus:outline-none focus:border-accent-cyan/50 transition-colors [&>option]:bg-surface [&>option]:text-text"
      >
        {EFFORT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
        </select>
      </div>
      {status && <p role="status" className="mt-2 text-xs text-info">{status}</p>}
      {error && (
        <div role="alert" className="mt-2 rounded-md border border-error/40 bg-[var(--color-error-tint)] p-3 text-xs text-error">
          <p>{error}</p>
          <button type="button" onClick={() => failedEffort && void handleChange(failedEffort)} className="mt-2 rounded-md border border-error px-3 py-2 font-semibold">Réessayer</button>
        </div>
      )}
    </div>
  );
}
