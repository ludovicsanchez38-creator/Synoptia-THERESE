// Onglet Services - Paramètres THÉRÈSE
// Génération d'images, transcription vocale, recherche web, extraction auto
// Extrait de LLMTab pour alléger la navigation

import { Check, AlertCircle, Loader2, Eye, EyeOff, Mic, Image as ImageIcon, Globe, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';
import { IMAGE_PROVIDERS } from './LLMTab';

export interface ServicesTabProps {
  // Clés API (pour vérifier si configurées)
  apiKeys: Record<string, boolean>;
  showApiKey: boolean;
  setShowApiKey: (v: boolean) => void;
  error: string | null;
  setError: (v: string | null) => void;
  // Génération d'images
  selectedImageProvider: string;
  onSelectImageProvider: (provider: string) => void;
  imageKeyInputs: Record<string, string>;
  setImageKeyInputs: (v: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void;
  imageKeySaving: string | null;
  imageKeySaved: string | null;
  onSaveImageKey: (apiKeyId: 'openai_image' | 'gemini_image' | 'fal') => void;
  // Transcription vocale Groq
  hasGroqKey: boolean;
  groqKeyInput: string;
  setGroqKeyInput: (v: string) => void;
  groqSaving: boolean;
  groqSaved: boolean;
  onSaveGroqKey: () => void;
  // Recherche web
  webSearchEnabled: boolean;
  webSearchLoading: boolean;
  onToggleWebSearch: () => void;
  // Brave Search
  hasBraveKey: boolean;
  braveKeyInput: string;
  setBraveKeyInput: (v: string) => void;
  braveSaving: boolean;
  braveSaved: boolean;
  onSaveBraveKey: () => void;
  // Extraction automatique
  autoExtractEntities: boolean;
  onToggleAutoExtract: () => void;
}

export function ServicesTab({
  apiKeys,
  showApiKey,
  setShowApiKey,
  error: _error,
  setError,
  selectedImageProvider,
  onSelectImageProvider,
  imageKeyInputs,
  setImageKeyInputs,
  imageKeySaving,
  imageKeySaved,
  onSaveImageKey,
  hasGroqKey,
  groqKeyInput,
  setGroqKeyInput,
  groqSaving,
  groqSaved,
  onSaveGroqKey,
  webSearchEnabled,
  webSearchLoading,
  onToggleWebSearch,
  hasBraveKey,
  braveKeyInput,
  setBraveKeyInput,
  braveSaving,
  braveSaved,
  onSaveBraveKey,
  autoExtractEntities,
  onToggleAutoExtract,
}: ServicesTabProps) {
  void _error;

  return (
    <div className="space-y-6">
      {/* Génération d'images */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-accent-magenta/20 flex items-center justify-center">
            <ImageIcon className="w-5 h-5 text-purple-400" />
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
                          Clé OK
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-400">
                          Clé requise
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-text-muted mt-0.5">{provider.description}</p>
                  </div>
                </button>

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

                  {isSaved && (
                    <p className="text-sm text-green-400 flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      Clé enregistrée
                    </p>
                  )}

                  <p className="text-xs text-text-muted">
                    Obtenez votre clé sur{' '}
                    <a href={provider.consoleUrl} target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:underline">
                      {new URL(provider.consoleUrl).hostname}
                    </a>
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

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

        {hasGroqKey ? (
          <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
            <Check className="w-4 h-4 text-green-400" />
            <span className="text-sm text-green-400">Dictée vocale active</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <AlertCircle className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-yellow-400">Dictée vocale désactivée</span>
          </div>
        )}

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
            <Button variant="primary" onClick={onSaveGroqKey} disabled={groqSaving || !groqKeyInput.trim()}>
              {groqSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sauver'}
            </Button>
          </div>

          {groqSaved && (
            <p className="text-sm text-green-400 flex items-center gap-1">
              <Check className="w-3 h-3" />
              Clé Groq enregistrée
            </p>
          )}

          <p className="text-xs text-text-muted">
            Obtenez votre clé sur{' '}
            <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:underline">
              console.groq.com
            </a>
            {' '}- Gratuit, rapide
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
              Permet aux LLMs de chercher sur le web
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

        {/* Brave Search (optionnel) */}
        <div className="ml-[52px] space-y-2">
          <div className="flex items-center gap-2">
            <p className="text-xs text-text-muted flex-1">
              <strong>Brave Search</strong> (optionnel) -{' '}
              <a href="https://brave.com/search/api/" target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:underline">
                Obtenir une clé gratuite
              </a>
            </p>
            {hasBraveKey && (
              <span className="flex items-center gap-1 text-xs text-green-400">
                <Check className="w-3 h-3" /> OK
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <input
              type="password"
              value={braveKeyInput}
              onChange={(e) => setBraveKeyInput(e.target.value)}
              placeholder="BSA..."
              className="flex-1 px-3 py-1.5 rounded-lg bg-surface border border-border text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50"
            />
            <Button variant="primary" size="sm" onClick={onSaveBraveKey} disabled={braveSaving || !braveKeyInput.trim()} className="text-xs px-3">
              {braveSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : braveSaved ? <Check className="w-3 h-3" /> : 'Sauver'}
            </Button>
          </div>
        </div>
      </div>

      {/* Extraction automatique */}
      <div className="pt-4 border-t border-border/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-accent-cyan" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-text">Extraction automatique</h3>
            <p className="text-xs text-text-muted">
              Extraire contacts et projets des conversations
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
