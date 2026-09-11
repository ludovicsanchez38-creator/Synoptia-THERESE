// Onglet configuration LLM - Paramètres THERESE
// Sélection provider, clé API, modèle, transcription vocale, recherche web, images, extraction auto

import { useEffect, useState } from 'react';
import { Check, AlertCircle, XCircle, Eye, EyeOff, Cpu, RefreshCw, Plus } from 'lucide-react';
import { Button } from '../ui/Button';
import { Carte, CarteTete } from '../ui/Carte';
import { Etiquette, type TonEtiquette } from '../ui/Etiquette';
import { Alerte } from '../ui/Alerte';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { FormField } from '../ui/FormField';
import * as api from '../../services/api';
import type { LLMEffort } from '../../services/api/config';
import { LocalModelFeasibility } from '../llm/LocalModelFeasibility';
import { FOURNISSEURS as PROVIDERS, chargerCatalogue, type ModeleDecore } from '../../lib/catalogueModeles';
import { effortTransmisSansOutils, modeleOpenAIRaisonnant } from '../../lib/effortOpenAI';

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
  /**
   * Lot 9 : vrai quand `error` est un REFUS DE CLÉ (clé vide, mauvais préfixe,
   * échec de `setApiKey`). Lui seul pose `aria-invalid` sur le champ et rend
   * l'alerte ici ; toute autre erreur est annoncée par la coque, une fois.
   */
  cleInvalide?: boolean;
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
  cleInvalide = false,
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

  /**
   * La ligne « quoi » de la carte Ollama : UNE chaîne, jamais une
   * concaténation de la description du catalogue et d'un compte. La
   * description statique (« 100% local - Aucune clé API requise ») ment dès
   * que le service est injoignable.
   */
  function quoiOllama(): string {
    if (!ollamaStatus?.available) return 'Service local injoignable';
    const n = ollamaStatus?.models.length ?? 0;
    if (n === 0) return 'Aucun modèle installé';
    const compte = n === 1 ? '1 modèle installé' : `${n} modèles installés`;
    const prefixe = selectedProvider === 'ollama' && selectedModel ? `${selectedModel} · ` : '';
    // `ollamaStatus` vaut `null` sur un chemin réel (valeur de secours de
    // `loadSetting`), d'où l'accès optionnel jusqu'au bout.
    const fiche = ollamaStatus?.models.find((m) => m.name === selectedModel);
    const outils = selectedProvider === 'ollama' && fiche?.gere_les_outils === true
      ? ' · outils pris en charge'
      : '';
    return `${prefixe}${compte}${outils}`;
  }

  /**
   * Le statut d'un service local injoignable est fait de deux phrases : celle
   * du serveur (ou son repli) puis la consigne. Le design dit « suivi de »
   * sans nommer le joint : on ajoute un point à la première quand elle n'en a
   * pas, plutôt que de coller « Ollama ne répond pas Démarrez Ollama… ».
   */
  function phraseClose(texte: string): string {
    return /[.!?…]$/.test(texte.trim()) ? texte.trim() : `${texte.trim()}.`;
  }

  /**
   * Les étiquettes d'une carte, de gauche à droite. « Actif » s'AJOUTE à
   * l'état de clé, il ne le remplace pas : un fournisseur courant sans clé
   * doit dire les deux.
   */
  function etiquettesDe(id: string): { ton: TonEtiquette; texte: string }[] {
    const pilules: { ton: TonEtiquette; texte: string }[] = [];
    if (id === 'anthropic') pilules.push({ ton: 'info', texte: 'Recommandé' });

    const ollamaEnPanne = id === 'ollama' && !ollamaStatus?.available;
    if (id === selectedProvider && !ollamaEnPanne) pilules.push({ ton: 'succes', texte: 'Actif' });

    if (corruptedKeys.includes(id)) pilules.push({ ton: 'erreur', texte: 'Clé corrompue' });
    else if (ollamaEnPanne) pilules.push({ ton: 'attention', texte: 'Indisponible' });
    else if (id !== 'ollama' && apiKeys[id]) pilules.push({ ton: 'info', texte: 'Clé enregistrée' });
    else if (id !== 'ollama') pilules.push({ ton: 'neutre', texte: 'Sans clé' });

    return pilules;
  }

  return (
    <div className="space-y-4">
      {/* La section : le titre, puis la grille des quatorze services. */}
      <Carte as="section" aria-labelledby="settings-ia-title">
        <CarteTete
          idTitre="settings-ia-title"
          icone={<Cpu className="h-[18px] w-[18px]" />}
          titre="Service d’IA"
          meta="Le modèle qui répond. En local, rien ne quitte ton ordinateur. En ligne, chaque fournisseur demande ton accord une fois."
        />

        {/* Doctrine `Segments`, entière : `role="group"` nommé + `aria-pressed`,
            ordre de tabulation naturel, AUCUNE gestion de flèches. Un radio APG
            se coche à la flèche, or `setLLMConfig` est un POST : la sélection ne
            doit pas suivre le focus. Sans roving, une carte désactivée est la
            seule que le clavier saute, au lieu de sortir la grille entière du
            clavier quand Ollama est à la fois courant et indisponible. */}
        <div
          role="group"
          aria-label="Choix du service d’IA"
          className="grid grid-cols-2 gap-2.5 px-4 pb-4"
        >
          {PROVIDERS.map((provider) => {
            const indisponible = provider.id === 'ollama' && !ollamaStatus?.available;
            const courant = selectedProvider === provider.id;

            return (
              <button
                key={provider.id}
                type="button"
                aria-pressed={courant}
                onClick={() => onSelectProvider(provider.id)}
                disabled={indisponible}
                className={`grid grid-cols-[1fr_auto] gap-x-2.5 gap-y-0.5 p-3 rounded-sm border text-left text-sm min-h-9 focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-ring ${
                  courant
                    ? 'border-accent bg-accent-tint ring-2 ring-ring/30 ring-offset-0'
                    : 'border-border hover:bg-surface-2'
                } ${indisponible ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span className="min-w-0 font-semibold text-text">{provider.name}</span>
                {/* Les pilules vivent dans un conteneur : posées en enfants
                    directs de la grille, la deuxième retomberait en colonne 1
                    d'une nouvelle rangée, et la carte perdrait sa forme. */}
                <span className="flex flex-wrap items-center gap-1 justify-self-end">
                  {etiquettesDe(provider.id).map((pilule) => (
                    <Etiquette key={pilule.texte} ton={pilule.ton}>{pilule.texte}</Etiquette>
                  ))}
                </span>
                <span className="col-span-2 text-sm text-text-muted">
                  {provider.id === 'ollama' ? quoiOllama() : provider.description}
                </span>
              </button>
            );
          })}
        </div>
      </Carte>

      {/* La carte du service : la clé (ou le statut Ollama), puis le modèle et
          l'effort. UNE carte, au nom du service, jamais deux titres homonymes
          empilés. Elle n'est jamais conditionnée au catalogue : un fournisseur
          venu du serveur et absent de `FOURNISSEURS` a quand même une clé à
          saisir, et une carte conditionnée la lui retirerait. */}
      <Carte as="section" aria-labelledby="settings-service-title">
        <CarteTete
          niveau="h3"
          idTitre="settings-service-title"
          titre={currentProviderConfig?.name ?? selectedProvider}
          meta={
            needsApiKey
              ? (hasApiKey
                ? 'La clé est chiffrée sur ton ordinateur et n’est jamais affichée en entier.'
                : 'Nécessaire pour utiliser ce fournisseur')
              : undefined
          }
        />

        {needsApiKey ? (
          <div className="space-y-2 px-4 pb-4">
            {/* La consigne de reprise garde ses mots ET sa couleur. Aucun rôle,
                comme aujourd'hui : cet état est présent dès le montage et ne
                répond à aucune action, une annonce assertive le ferait relire à
                chaque ouverture de la rubrique. */}
            {corruptedKeys.includes(selectedProvider) && (
              <p className="flex items-center gap-2 text-sm text-error">
                <XCircle aria-hidden="true" className="h-[18px] w-[18px]" />
                Clé API corrompue - ressaisis-la
              </p>
            )}

            <label htmlFor="settings-api-key" className="block text-sm font-semibold">Clé d’API</label>
            <div className="flex items-center gap-2">
              <div className="min-w-0 flex-1">
                <Input
                  id="settings-api-key"
                  type={showApiKey ? 'text' : 'password'}
                  className="font-mono tracking-widest"
                  error={Boolean(cleInvalide && error)}
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
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                aria-label={showApiKey ? 'Masquer la clé API' : 'Afficher la clé API'}
                aria-pressed={showApiKey}
              >
                {showApiKey ? <EyeOff className="h-[18px] w-[18px]" /> : <Eye className="h-[18px] w-[18px]" />}
              </Button>
              <Button
                variant="primary"
                size="md"
                onClick={onSaveApiKey}
                disabled={saving || !apiKeyInput.trim()}
              >
                {saving ? <Spinner taille="bouton" /> : hasApiKey ? 'Remplacer' : 'Enregistrer'}
              </Button>
            </div>

            {/* Le refus de clé n'a qu'UNE alerte, ici : la coque se tait quand
                `cleInvalide` est vrai. Pas d'`action` : la reprise est le bouton
                d'enregistrement, deux lignes plus haut. */}
            {cleInvalide && error && (
              <Alerte icone={<AlertCircle className="h-[18px] w-[18px]" />}>{error}</Alerte>
            )}

            {saved && (
              <p role="status" className="flex items-center gap-1 text-sm text-success">
                <Check className="h-4 w-4" />
                Clé API enregistrée
              </p>
            )}

            {currentProviderConfig?.consoleUrl && (
              <p className="text-sm text-text-muted">
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
        ) : (
          /* Ollama : le statut du service local prend la place du bloc clé. Le
             padding est sur le conteneur, pas sur le paragraphe : le laisser aux
             deux ferait 32 px de marge horizontale. Pas d'`Alerte` pour
             l'indisponibilité : `role="alert"` ferait relire une annonce
             assertive à chaque montage, pour un état de service permanent. */
          <div className="flex items-center gap-2 px-4 py-3">
            {ollamaStatus?.available ? (
              <p role="status" className="flex-1 text-sm text-text-muted">
                Ollama connecté ({ollamaStatus.base_url})
              </p>
            ) : (
              <p role="status" className="flex-1 text-sm text-warning">
                {phraseClose(ollamaStatus?.error || 'Ollama non disponible')} Démarrez Ollama pour utiliser des modèles locaux.
              </p>
            )}
            {onRetestOllama && (
              <Button
                variant="ghost"
                size="icon"
                type="button"
                onClick={onRetestOllama}
                disabled={retestingOllama}
                title="Re-tester la connexion Ollama"
                aria-label="Re-tester la connexion Ollama"
                className="shrink-0"
              >
                <RefreshCw className={`h-[18px] w-[18px] ${retestingOllama ? 'animate-spin' : ''}`} />
              </Button>
            )}
          </div>
        )}

        <ModelSelector
          availableModels={availableModels}
          selectedModel={selectedModel}
          onSelectModel={onSelectModel}
          selectedProvider={selectedProvider}
        />
      </Carte>

      {/* Adresse d'espace de travail Qwen (dette 0.43.4) : l'URL contient
          l'identifiant du compte, le défaut ne peut fonctionner pour personne. */}
      {selectedProvider === 'qwen' && (
        <Carte as="section" className="p-4">
          <div className="flex items-end gap-2">
            <div className="min-w-0 flex-1">
              <FormField
                label="Adresse de ton espace de travail"
                htmlFor="qwen-base-url"
                description="Dans Alibaba Model Studio, copie l'adresse « compatible-mode/v1 » de ton espace de travail. Sans elle, Qwen ne peut pas répondre."
              >
                <Input
                  id="qwen-base-url"
                  type="url"
                  value={baseUrlInput}
                  onChange={(e) => setBaseUrlInput(e.target.value)}
                  placeholder="https://ton-espace.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
                />
              </FormField>
            </div>
            {/* « Enregistrer l'adresse », jamais « Enregistrer » : sur un Qwen
                sans clé, deux boutons du même nom cohabiteraient à l'écran. */}
            <Button
              variant="primary"
              size="md"
              onClick={() => void handleSaveBaseUrl()}
              disabled={savingBaseUrl || !baseUrlInput.trim()}
            >
              {savingBaseUrl ? <Spinner taille="bouton" /> : baseUrlSaved ? <Check className="h-4 w-4" /> : 'Enregistrer l’adresse'}
            </Button>
          </div>
        </Carte>
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

  /**
   * `Select` ne rend QUE son tableau `options` : l'entrée du modèle hors
   * catalogue, glissée jusqu'ici en enfant du `<select>`, doit y entrer. Sans
   * elle, la `value` ne correspondrait à aucune option et le navigateur
   * afficherait la première, c'est-à-dire un modèle qui n'est pas celui
   * enregistré (BUG-084).
   */
  const options = [
    ...availableModels.map((model) => ({
      value: model.id,
      label: model.badge ? `${model.name} (${model.badge})` : model.name,
    })),
    ...(isCustomModel ? [{ value: selectedModel, label: `${selectedModel} (personnalisé)` }] : []),
  ];

  function handleAddCustomModel() {
    const trimmed = customModelId.trim();
    if (!trimmed) return;
    onSelectModel(trimmed);
    setCustomModelId('');
    setShowCustomInput(false);
  }

  /**
   * Les deux rangées vont ensemble, jamais l'une sans l'autre : régler un
   * effort sans modèle serait un état neuf, et `handleChange` partirait avec un
   * modèle vide. La carte, elle, reste montée : la clé y vit.
   */
  const rangeesRendues = options.length > 0 || selectedProvider === 'ollama';
  if (!rangeesRendues) return null;

  // La maquette ôte le filet du haut à la PREMIÈRE `.ligne-reglage` de sa
  // carte ; dans la carte du service, ce premier enfant est la clé ou le statut
  // Ollama, pas une rangée de réglage. Les deux rangées gardent donc leur filet.
  const rangee = 'grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 py-2.5 border-t border-border px-4';

  return (
    <>
      <div className={rangee}>
        <label htmlFor="settings-llm-model" className="text-sm font-semibold">Modèle</label>
        <Select
          id="settings-llm-model"
          value={selectedModel}
          options={options}
          placeholder={options.length === 0 ? 'Aucun modèle installé' : undefined}
          onChange={(e) => onSelectModel(e.target.value)}
        />
        {selectedProvider !== 'ollama' && (
          <Button
            variant="ghost"
            size="md"
            type="button"
            onClick={() => setShowCustomInput(!showCustomInput)}
            title="Utiliser un identifiant de modèle personnalisé"
            className="col-start-1 justify-self-start"
          >
            <Plus className="mr-1 h-[18px] w-[18px]" />
            Custom
          </Button>
        )}
      </div>

      {isCustomModel && (
        <p className="flex items-center gap-2 px-4 text-sm text-accent-cyan-ink">
          <AlertCircle aria-hidden="true" className="h-[18px] w-[18px]" />
          Modèle personnalisé actif : {selectedModel}
        </p>
      )}

      {/* Le champ « modèle hors liste » appartient au bouton qui l'ouvre : le
          mettre après la carte l'éloignerait de son déclencheur. */}
      {showCustomInput && (
        <div className="space-y-2 px-4 py-2">
          <p className="text-sm text-text-muted">
            Saisis l'identifiant exact du modèle tel qu'il apparait dans l'API du fournisseur.
          </p>
          <div className="flex gap-2">
            <div className="min-w-0 flex-1">
              <Input
                aria-label="Identifiant du modèle personnalisé"
                type="text"
                className="font-mono"
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
              />
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={handleAddCustomModel}
              disabled={!customModelId.trim()}
            >
              Utiliser
            </Button>
          </div>
        </div>
      )}

      {/* Effort de raisonnement (10/07/2026) - applique uniquement aux
          modeles au support verifie (Fable/Sonnet 5/4.6/Opus 4.5+, GPT-5.6,
          Grok 4.5, Ollama thinking) ; Auto = defaut du serveur. */}
      <EffortSelector
        selectedProvider={selectedProvider}
        selectedModel={selectedModel}
        classeRangee={rangee}
      />
    </>
  );
}


const EFFORT_OPTIONS = [
  { value: 'auto', label: 'Auto (défaut du modèle)' },
  { value: 'low', label: 'Faible - rapide et économique' },
  { value: 'medium', label: 'Moyen' },
  { value: 'high', label: 'Élevé - raisonnement approfondi' },
  { value: 'max', label: 'Maximal - le plus lent, le plus fiable' },
] as const;

export function EffortSelector({
  selectedProvider,
  selectedModel,
  classeRangee = 'grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 py-2.5 border-t border-border px-4',
}: {
  selectedProvider: string;
  selectedModel: string;
  /** Lot 9 : la rangée de la carte du service, mot pour mot celle du modèle. */
  classeRangee?: string;
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

  // P-045 : la famille GPT-5/o-series refuse outils + raisonnement sur
  // /v1/chat/completions ; le moteur neutralise l'effort dès qu'une
  // conversation utilise des outils. L'écran le dit, sans promettre que
  // l'effort passe sans outils sur un modèle non pris en charge.
  const mentionOutils = selectedProvider === 'openai' && modeleOpenAIRaisonnant(selectedModel);
  const effortSansOutils = effortTransmisSansOutils(selectedModel);

  return (
    <>
      <div className={classeRangee}>
        <label htmlFor="llm-effort" className="text-sm font-semibold">
          Effort de raisonnement
        </label>
        <Select
          id="llm-effort"
          value={effort}
          disabled={saving}
          options={EFFORT_OPTIONS.map((opt) => ({ value: opt.value, label: opt.label }))}
          /* Deux valeurs, dans cet ordre, et JAMAIS `undefined` : l'aide
             ci-dessous décrit le champ en toutes circonstances, la mention ne
             s'y ajoute que lorsqu'elle est rendue. */
          aria-describedby={mentionOutils ? 'llm-effort-aide llm-effort-outils' : 'llm-effort-aide'}
          onChange={(e) => void handleChange(e.target.value)}
        />
        <p id="llm-effort-aide" className="col-start-1 text-sm text-text-muted">
          Appliqué aux modèles qui le gèrent (Claude récents, GPT-5.6, Grok 4.5,
          modèles Ollama « thinking »). Auto laisse le modèle décider.
        </p>
        {mentionOutils && (
          <p id="llm-effort-outils" data-testid="effort-mention-outils" className="col-span-2 mt-2 text-sm text-text-muted">
            Dans THÉRÈSE, l'effort est désactivé pour ce modèle dès qu'une conversation utilise des outils :
            l'API d'OpenAI refuse le raisonnement avec des outils sur ce chemin.{' '}
            {effortSansOutils
              ? 'Sans outils, ce réglage est transmis (trame, rédaction).'
              : 'Sans outils, ce réglage n\'est pas transmis à ce modèle : seuls les GPT-5.6 sont pris en charge.'}
          </p>
        )}
        {/* `col-span-2` : la rangée est une grille à deux colonnes, sans lui
            ces deux blocs tomberaient en colonne 1 et déplaceraient le Select. */}
        {status && <p role="status" className="col-span-2 mt-2 text-sm text-info">{status}</p>}
        {error && (
          <Alerte
            className="col-span-2 mt-2"
            icone={<AlertCircle className="h-[18px] w-[18px]" />}
            action={(
              <Button
                variant="ghost"
                size="md"
                type="button"
                onClick={() => failedEffort && void handleChange(failedEffort)}
              >
                Réessayer l’effort
              </Button>
            )}
          >
            {error}
          </Alerte>
        )}
      </div>
    </>
  );
}
