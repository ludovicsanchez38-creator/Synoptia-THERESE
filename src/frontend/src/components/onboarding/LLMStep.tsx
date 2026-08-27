/**
 * THERESE v2 - LLM Step
 *
 * Third step of the onboarding wizard - Configure LLM provider and API key.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Key, Check, AlertCircle, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import * as api from '../../services/api';
import { TEXTES_ONBOARDING } from './textes';
import { FOURNISSEURS as PROVIDERS, chargerCatalogue, selectionApresCatalogue, type ModeleDecore } from '../../lib/catalogueModeles';
import { Button } from '../ui/Button';
import { LocalModelFeasibility } from '../llm/LocalModelFeasibility';
import { handleRovingFocus } from '../../lib/rovingFocus';
import { Spinner } from '../ui/Spinner';

interface LLMStepProps {
  onNext: (provider: api.LLMProvider | null) => void;
  onBack: () => void;
}

// Catalogue centralisé (dette 0.43.4) : l'onboarding déclarait sa PROPRE copie
// des fournisseurs et elle divergeait déjà des Réglages - gpt-5.3-codex y était
// encore proposé, retiré partout ailleurs. Une seule copie statique de repli
// (lib/catalogueModeles), la liste dynamique vient du backend.

const LLM_SETUP_TIMEOUT_MS = 10_000;

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(
      () => reject(new Error('La vérification des modèles prend trop de temps.')),
      timeoutMs,
    );
    promise.then(
      (value) => {
        clearTimeout(timeoutId);
        resolve(value);
      },
      (error: unknown) => {
        clearTimeout(timeoutId);
        reject(error);
      },
    );
  });
}

export function LLMStep({ onNext, onBack }: LLMStepProps) {
  const [selectedProvider, setSelectedProvider] = useState<api.LLMProvider>('anthropic');
  // La LISTE des modèles cloud vient du backend ; le repli statique ne sert
  // que si la route échoue. En onboarding rien n'est encore enregistré : si le
  // modèle sélectionné n'existe pas dans la liste fraîche, on prend le premier.
  const [catalogueDynamique, setCatalogueDynamique] = useState<ModeleDecore[] | null>(null);
  // Adresse d'espace de travail Qwen : sans elle, le fournisseur ne peut pas
  // fonctionner - elle fait donc partie du parcours, pas d'un réglage caché.
  const [baseUrlInput, setBaseUrlInput] = useState('');
  // Revue dette : l'arrivée du catalogue dynamique corrigeait la sélection
  // même quand l'utilisateur venait de choisir un modèle à la main - un
  // reclassement silencieux, précisément ce qu'on corrige partout ailleurs.
  const modeleChoisiParLUtilisateur = useRef(false);
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-6');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [ollamaStatus, setOllamaStatus] = useState<api.OllamaStatus | null>(null);
  // BUG-169 : on garde la CAPACITÉ du modèle, pas seulement son nom. Un modèle
  // sans appel d'outils ne peut ni créer un contact, ni poser un rendez-vous.
  // Le masquer laisserait une liste vide sans explication ; on le montre
  // désactivé, avec son motif.
  const [ollamaModels, setOllamaModels] = useState<
    { nom: string; gereLesOutils: boolean; motif?: string | null }[]
  >([]);
  const [systemResources, setSystemResources] = useState<api.SystemResources | null>(null);
  const [saving, setSaving] = useState(false);
  const [configuring, setConfiguring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const loadRequestRef = useRef(0);
  const configuringRef = useRef(false);

  const loadState = useCallback(async () => {
    const activeRequest = ++loadRequestRef.current;
    setLoading(true);
    setLoadError(null);
    try {
      const [keys, ollamaStatusData, systemResourcesData] = await withTimeout(Promise.all([
        api.getApiKeys(),
        api.getOllamaStatus(),
        api.getSystemResources().catch(() => null),
      ]), LLM_SETUP_TIMEOUT_MS);
      if (activeRequest !== loadRequestRef.current) return;
      setApiKeys(keys);
      setOllamaStatus(ollamaStatusData);
      setSystemResources(systemResourcesData);
      setOllamaModels(
        ollamaStatusData.available
          ? ollamaStatusData.models.map((model) => ({
              nom: model.name,
              // Un modèle inconnu du serveur est présumé capable : Ollama
              // accepte n'importe quel modèle, y compris construit localement.
              gereLesOutils: model.gere_les_outils !== false,
              motif: model.motif_indisponible,
            }))
          : [],
      );
    } catch (err) {
      if (activeRequest !== loadRequestRef.current) return;
      console.error('Failed to load LLM state:', err);
      setLoadError(
        err instanceof Error && err.message.includes('trop de temps')
          ? `${err.message} Tu peux réessayer ou configurer plus tard.`
          : 'Impossible de vérifier les modèles disponibles. Tu peux réessayer ou configurer plus tard.',
      );
    } finally {
      if (activeRequest === loadRequestRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadState();
    return () => { loadRequestRef.current += 1; };
  }, [loadState]);

  const currentProviderConfig = PROVIDERS.find(p => p.id === selectedProvider);
  const hasApiKey = apiKeys[selectedProvider] === true;
  const needsApiKey = selectedProvider !== 'ollama';

  const availableModels: {
    id: string;
    name: string;
    badge?: string;
    indisponible?: boolean;
    motif?: string | null;
  }[] = selectedProvider === 'ollama'
    ? ollamaModels.map((m) => ({
        id: m.nom,
        name: m.nom,
        badge: m.gereLesOutils ? undefined : 'Sans actions',
        indisponible: !m.gereLesOutils,
        motif: m.motif,
      }))
    : catalogueDynamique ?? (currentProviderConfig?.models || []);

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
      setApiKeyInput('');
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    setCatalogueDynamique(null);
    if (selectedProvider === 'ollama') return;
    let annule = false;
    void chargerCatalogue(selectedProvider).then((modeles) => {
      if (annule || !modeles) return;
      setCatalogueDynamique(modeles);
      setSelectedModel((actuel) =>
        selectionApresCatalogue(actuel, modeles, modeleChoisiParLUtilisateur.current),
      );
    });
    return () => { annule = true; };
  }, [selectedProvider]);

  async function handleSelectProvider(provider: api.LLMProvider) {
    setSelectedProvider(provider);
    modeleChoisiParLUtilisateur.current = false;
    setError(null);
    setSaved(false);

    const providerConfig = PROVIDERS.find(p => p.id === provider);
    let defaultModel = providerConfig?.models[0]?.id || '';

    if (provider === 'ollama' && ollamaModels.length > 0) {
      // Ne jamais pré-sélectionner un modèle incapable d'agir : c'est ce qui a
      // fait attendre 3 min 26 s au testeur pour une réponse dégradée.
      const capable = ollamaModels.find((m) => m.gereLesOutils);
      defaultModel = (capable ?? ollamaModels[0]).nom;
    }

    if (defaultModel) {
      setSelectedModel(defaultModel);
    }
  }

  async function handleContinue() {
    if (configuringRef.current) return;
    configuringRef.current = true;
    setConfiguring(true);
    setError(null);
    try {
      await api.setLLMConfig(
        selectedProvider,
        selectedModel,
        undefined,
        selectedProvider === 'qwen' ? baseUrlInput.trim() : undefined,
      );
      onNext(selectedProvider);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la configuration');
      configuringRef.current = false;
      setConfiguring(false);
    }
  }

  const canContinue = selectedProvider === 'ollama'
    ? Boolean(
        ollamaStatus?.available
        && ollamaModels.some((m) => m.gereLesOutils)
        && selectedModel,
      )
    : (hasApiKey || saved)
      // L'adresse Qwen n'est pas optionnelle : continuer sans elle livrerait
      // un fournisseur configuré incapable de répondre.
      && (selectedProvider !== 'qwen' || /^https?:\/\//.test(baseUrlInput.trim()));

  if (loading) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3" role="status">
        <Spinner taille="zone" className="text-accent-cyan" />
        <p className="text-sm text-text-muted">Vérification des modèles disponibles…</p>
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
          <h2 className="text-xl font-semibold text-text">{TEXTES_ONBOARDING.choixServiceIA.titre}</h2>
          <p className="text-sm text-text-muted">{TEXTES_ONBOARDING.choixServiceIA.sousTitre}</p>
        </div>
      </div>

      {/* Provider Selection */}
      {/* BUG-100 : pas de plafond de hauteur sur cette liste. Avec 10 providers et la
          barre de défilement masquée par défaut sur macOS, un conteneur trop court
          cachait Ollama (le dernier provider). */}
      <div
        role="radiogroup"
        aria-label="Sélection du provider LLM"
        className="space-y-2 mb-6"
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
              tabIndex={isSelected ? 0 : -1}
              onClick={() => handleSelectProvider(provider.id)}
              onKeyDown={(event) => handleRovingFocus(event, '[role="radio"]', 'vertical')}
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
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--color-error-tint)] text-error">
                      Non disponible
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-muted mt-0.5">{provider.description}</p>
              </div>
              {provider.id !== 'ollama' && (
                <div className={`shrink-0 ${providerHasKey ? 'text-success' : 'text-text-muted'}`}>
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
            <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-success-tint)] border border-success/40 rounded-lg">
              <Check className="w-4 h-4 text-success" />
              <span className="text-sm text-success">Clé API configurée (chiffrée localement)</span>
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
                    className="w-full px-4 py-2.5 pr-10 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors font-mono"
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
                  onClick={handleSaveApiKey}
                  disabled={saving || !apiKeyInput.trim()}
                >
                  {saving ? <Spinner taille="bouton" /> : 'Sauver'}
                </Button>
              </div>

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
            </>
          )}

          {saved && (
            <div className="flex items-center gap-2 text-sm text-success">
              <Check className="w-3 h-3" />
              Clé API enregistrée
            </div>
          )}
        </div>
      )}

      {/* Adresse d'espace de travail Qwen (dette 0.43.4) : l'URL contient
          l'identifiant du compte - sans elle, le fournisseur ne répond pas. */}
      {selectedProvider === 'qwen' && (
        <div className="mb-6">
          <label htmlFor="qwen-base-url" className="text-sm text-text-muted mb-2 block">
            Adresse de ton espace de travail
          </label>
          <input
            id="qwen-base-url"
            type="url"
            value={baseUrlInput}
            onChange={(e) => setBaseUrlInput(e.target.value)}
            placeholder="https://ton-espace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
            className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors"
          />
          <p className="text-xs text-text-muted mt-2">
            Dans Alibaba Model Studio, copie l'adresse « compatible-mode/v1 » de ton
            espace de travail. Elle est indispensable pour continuer.
          </p>
        </div>
      )}

      {/* Model Selection */}
      {availableModels.length > 0 && (
        <div className="mb-6">
          <label htmlFor="llm-model" className="text-sm text-text-muted mb-2 block">Modèle</label>
          <select
            id="llm-model"
            value={selectedModel}
            onChange={(e) => {
              modeleChoisiParLUtilisateur.current = true;
              setSelectedModel(e.target.value);
            }}
            className="w-full px-4 py-2.5 bg-background/60 border border-border/50 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent-cyan transition-colors"
          >
            {availableModels.map((model) => (
              <option key={model.id} value={model.id} disabled={model.indisponible}>
                {model.name} {model.badge ? `(${model.badge})` : ''}
              </option>
            ))}
          </select>

          {/* BUG-169 : le motif, dit à l'utilisateur plutôt que gardé pour le
              code. Un modèle qui disparaît sans explication est le défaut qu'on
              corrige partout ailleurs dans cette version ; un modèle désactivé
              sans raison visible en serait la moitié. */}
          {availableModels.some((model) => model.indisponible) && (
            <p className="mt-2 text-xs text-text-muted">
              {availableModels.find((model) => model.indisponible)?.motif
                ?? "Certains modèles installés ne savent pas déclencher d'actions : "
                   + 'ils sont grisés.'}
            </p>
          )}

          {selectedProvider === 'ollama' && (
            <div className="mt-3">
              <LocalModelFeasibility
                model={ollamaStatus?.models.find((model) => model.name === selectedModel)}
                resources={systemResources}
              />
            </div>
          )}
        </div>
      )}

      {/* BUG-166. Le bouton de revérification ci-dessous n'apparaissait qu'en
          cas d'ERREUR. Or un Ollama simplement pas encore lancé ne produit
          aucune erreur : il répond proprement « indisponible ». Le testeur
          voyait donc Ollama grisé, sans aucun moyen de revérifier après l'avoir
          démarré — il fallait relancer tout l'assistant. On propose la
          revérification dès qu'Ollama est absent, erreur ou pas. */}
      {!loadError && ollamaStatus && !ollamaStatus.available && (
        <div className="mb-6 rounded-lg border border-border bg-surface px-3 py-3">
          <p className="text-sm text-text-muted">
            Ollama n'a pas répondu. S'il n'était pas encore lancé, démarre-le
            puis revérifie : inutile de recommencer l'installation.
          </p>
          <button
            type="button"
            onClick={() => void loadState()}
            className="mt-3 text-xs font-semibold text-text underline underline-offset-2"
          >
            Revérifier la disponibilité
          </button>
        </div>
      )}

      {/* Error */}
      {loadError && (
        <div className="mb-6 rounded-lg border border-warning/30 bg-[var(--color-warning-tint)] px-3 py-3" role="alert">
          <div className="flex items-start gap-2 text-sm text-warning">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span className="flex-1">{loadError}</span>
          </div>
          <button type="button" onClick={() => void loadState()} className="mt-3 text-xs font-semibold text-text underline underline-offset-2">
            Réessayer la vérification
          </button>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 mb-6 bg-[var(--color-error-tint)] border border-error/40 rounded-lg" role="alert">
          <AlertCircle className="w-4 h-4 text-error" />
          <span className="text-sm text-error">{error}</span>
        </div>
      )}

      {/* Warning if no API key configured */}
      {needsApiKey && !hasApiKey && (
        <div className="flex items-center gap-2 px-3 py-2 mb-4 bg-[var(--color-warning-tint)] border border-warning/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-warning shrink-0" />
          <span className="text-sm text-warning">
            Sans clé API, THÉRÈSE ne pourra pas fonctionner. Configure une clé ou utilise Ollama.
          </span>
        </div>
      )}

      {/* Footer */}
      <div className="flex justify-between pt-4 border-t border-border/30">
        <Button variant="ghost" onClick={onBack} disabled={configuring} data-testid="onboarding-prev-btn">
          Retour
        </Button>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={() => onNext(null)} disabled={configuring} data-testid="onboarding-skip-btn">
            Configurer plus tard
          </Button>
          <Button
            variant="primary"
            onClick={handleContinue}
            disabled={configuring || !canContinue}
            title={!canContinue ? 'Configure une clé API, démarre Ollama ou choisis « Configurer plus tard »' : undefined}
            data-testid="onboarding-next-btn"
          >
            {configuring ? 'Configuration…' : 'Continuer'}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
