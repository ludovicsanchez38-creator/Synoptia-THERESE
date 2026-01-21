# Story E5-07 : Ajouter les paramètres utilisateur

## Description

En tant que **utilisateur**,
Je veux **personnaliser THÉRÈSE selon mes préférences**,
Afin de **adapter l'outil à ma façon de travailler**.

## Contexte technique

- **Composants impactés** : Frontend React, Backend Python
- **Dépendances** : E1-01, E1-03
- **Fichiers concernés** :
  - `src/frontend/src/pages/Settings.tsx` (nouveau)
  - `src/frontend/src/stores/settingsStore.ts` (nouveau)
  - `src/backend/therese/api/routes/settings.py` (nouveau)

## Critères d'acceptation

- [ ] Page Settings accessible via ⌘,
- [ ] Configuration clé API Claude
- [ ] Choix du modèle LLM (Claude, Mistral)
- [ ] Personnalisation prompt système
- [ ] Paramètres mémoire (auto-extraction on/off)
- [ ] Réglages interface (taille texte, animations)
- [ ] Export/Import configuration
- [ ] Validation des clés API

## Notes techniques

### Store des settings

```typescript
// stores/settingsStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Settings {
  // API
  apiProvider: 'claude' | 'mistral' | 'ollama';
  apiKey: string;
  apiModel: string;

  // LLM
  systemPrompt: string;
  temperature: number;
  maxTokens: number;

  // Mémoire
  autoExtractEntities: boolean;
  memoryContextSize: number;
  confidenceThreshold: number;

  // Interface
  fontSize: 'small' | 'medium' | 'large';
  enableAnimations: boolean;
  compactMode: boolean;
  sidebarDefaultTab: 'history' | 'memory' | 'files';

  // Données
  dataPath: string;
}

interface SettingsStore extends Settings {
  updateSettings: (partial: Partial<Settings>) => void;
  resetToDefaults: () => void;
  exportSettings: () => string;
  importSettings: (json: string) => boolean;
}

const defaultSettings: Settings = {
  apiProvider: 'claude',
  apiKey: '',
  apiModel: 'claude-sonnet-4-20250514',

  systemPrompt: `Tu es THÉRÈSE, une assistante IA française pour entrepreneurs.
Tu es directe, efficace et pragmatique.
Tu mémorises les informations importantes pour les conversations futures.`,
  temperature: 0.7,
  maxTokens: 4096,

  autoExtractEntities: true,
  memoryContextSize: 5,
  confidenceThreshold: 0.7,

  fontSize: 'medium',
  enableAnimations: true,
  compactMode: false,
  sidebarDefaultTab: 'history',

  dataPath: '',
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      ...defaultSettings,

      updateSettings: (partial) => set(partial),

      resetToDefaults: () => set(defaultSettings),

      exportSettings: () => {
        const { updateSettings, resetToDefaults, exportSettings, importSettings, ...settings } = get();
        return JSON.stringify(settings, null, 2);
      },

      importSettings: (json) => {
        try {
          const parsed = JSON.parse(json);
          set(parsed);
          return true;
        } catch {
          return false;
        }
      },
    }),
    {
      name: 'therese-settings',
      partialize: (state) => {
        const { updateSettings, resetToDefaults, exportSettings, importSettings, ...settings } = state;
        return settings;
      },
    }
  )
);
```

### Page Settings

```tsx
// pages/Settings.tsx
import { useState } from 'react';
import { Key, Bot, Brain, Palette, Database, Download, Upload, RotateCcw } from 'lucide-react';
import { useSettingsStore } from '../stores/settingsStore';

const sections = [
  { id: 'api', label: 'API & Modèle', icon: Key },
  { id: 'llm', label: 'Comportement IA', icon: Bot },
  { id: 'memory', label: 'Mémoire', icon: Brain },
  { id: 'interface', label: 'Interface', icon: Palette },
  { id: 'data', label: 'Données', icon: Database },
];

export function SettingsPage() {
  const [activeSection, setActiveSection] = useState('api');
  const settings = useSettingsStore();

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-56 border-r border-border bg-surface">
        <div className="p-4">
          <h1 className="text-lg font-semibold text-text">Paramètres</h1>
        </div>
        <nav className="px-2">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  activeSection === section.id
                    ? 'bg-accent-cyan/10 text-accent-cyan'
                    : 'text-text-muted hover:text-text hover:bg-surface-elevated'
                )}
              >
                <Icon className="w-4 h-4" />
                {section.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl">
          {activeSection === 'api' && <ApiSettings />}
          {activeSection === 'llm' && <LLMSettings />}
          {activeSection === 'memory' && <MemorySettings />}
          {activeSection === 'interface' && <InterfaceSettings />}
          {activeSection === 'data' && <DataSettings />}
        </div>
      </div>
    </div>
  );
}
```

### Section API

```tsx
// components/settings/ApiSettings.tsx
import { useState } from 'react';
import { Eye, EyeOff, CheckCircle, XCircle, Loader } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';

export function ApiSettings() {
  const { apiProvider, apiKey, apiModel, updateSettings } = useSettingsStore();
  const [showKey, setShowKey] = useState(false);
  const [validating, setValidating] = useState(false);
  const [isValid, setIsValid] = useState<boolean | null>(null);

  const providers = [
    { id: 'claude', name: 'Claude (Anthropic)', models: ['claude-sonnet-4-20250514', 'claude-opus-4-20250514', 'claude-3-5-haiku-20241022'] },
    { id: 'mistral', name: 'Mistral AI', models: ['mistral-large-latest', 'mistral-medium-latest'] },
    { id: 'ollama', name: 'Ollama (local)', models: ['llama3', 'mistral', 'codellama'] },
  ];

  const currentProvider = providers.find((p) => p.id === apiProvider);

  const validateKey = async () => {
    if (!apiKey) return;
    setValidating(true);
    try {
      const response = await fetch('/api/settings/validate-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: apiProvider, key: apiKey }),
      });
      setIsValid(response.ok);
    } catch {
      setIsValid(false);
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-text">API & Modèle</h2>

      {/* Provider */}
      <div>
        <label className="block text-sm font-medium text-text mb-2">Fournisseur</label>
        <div className="grid grid-cols-3 gap-3">
          {providers.map((provider) => (
            <button
              key={provider.id}
              onClick={() => updateSettings({
                apiProvider: provider.id as any,
                apiModel: provider.models[0],
              })}
              className={cn(
                'p-4 rounded-lg border text-left transition-colors',
                apiProvider === provider.id
                  ? 'border-accent-cyan bg-accent-cyan/10'
                  : 'border-border hover:border-accent-cyan/50'
              )}
            >
              <p className="font-medium text-text">{provider.name}</p>
            </button>
          ))}
        </div>
      </div>

      {/* API Key */}
      {apiProvider !== 'ollama' && (
        <div>
          <label className="block text-sm font-medium text-text mb-2">Clé API</label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => {
                  updateSettings({ apiKey: e.target.value });
                  setIsValid(null);
                }}
                placeholder={`Clé ${currentProvider?.name || ''}`}
                className="w-full px-4 py-2 pr-10 bg-surface-elevated border border-border rounded-lg text-text"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                {showKey ? (
                  <EyeOff className="w-4 h-4 text-text-muted" />
                ) : (
                  <Eye className="w-4 h-4 text-text-muted" />
                )}
              </button>
            </div>
            <button
              onClick={validateKey}
              disabled={!apiKey || validating}
              className="px-4 py-2 bg-surface-elevated border border-border rounded-lg hover:border-accent-cyan/50 disabled:opacity-50"
            >
              {validating ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : isValid === true ? (
                <CheckCircle className="w-4 h-4 text-success" />
              ) : isValid === false ? (
                <XCircle className="w-4 h-4 text-error" />
              ) : (
                'Valider'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Model */}
      <div>
        <label className="block text-sm font-medium text-text mb-2">Modèle</label>
        <select
          value={apiModel}
          onChange={(e) => updateSettings({ apiModel: e.target.value })}
          className="w-full px-4 py-2 bg-surface-elevated border border-border rounded-lg text-text"
        >
          {currentProvider?.models.map((model) => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
```

### Section Mémoire

```tsx
// components/settings/MemorySettings.tsx
export function MemorySettings() {
  const {
    autoExtractEntities,
    memoryContextSize,
    confidenceThreshold,
    updateSettings,
  } = useSettingsStore();

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-text">Mémoire</h2>

      {/* Auto-extraction */}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-text">Extraction automatique</p>
          <p className="text-sm text-text-muted">
            Extraire automatiquement les contacts, projets et faits des conversations
          </p>
        </div>
        <Switch
          checked={autoExtractEntities}
          onChange={(checked) => updateSettings({ autoExtractEntities: checked })}
        />
      </div>

      {/* Context size */}
      <div>
        <label className="block text-sm font-medium text-text mb-2">
          Éléments de contexte par message
        </label>
        <input
          type="range"
          min={1}
          max={10}
          value={memoryContextSize}
          onChange={(e) => updateSettings({ memoryContextSize: Number(e.target.value) })}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-text-muted mt-1">
          <span>1 élément</span>
          <span className="font-medium text-accent-cyan">{memoryContextSize} éléments</span>
          <span>10 éléments</span>
        </div>
      </div>

      {/* Confidence threshold */}
      <div>
        <label className="block text-sm font-medium text-text mb-2">
          Seuil de confiance pour extraction
        </label>
        <input
          type="range"
          min={0.5}
          max={0.95}
          step={0.05}
          value={confidenceThreshold}
          onChange={(e) => updateSettings({ confidenceThreshold: Number(e.target.value) })}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-text-muted mt-1">
          <span>50%</span>
          <span className="font-medium text-accent-cyan">{Math.round(confidenceThreshold * 100)}%</span>
          <span>95%</span>
        </div>
      </div>
    </div>
  );
}
```

### Route API validation

```python
# therese/api/routes/settings.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic
from mistralai.client import MistralClient

router = APIRouter(prefix="/settings", tags=["settings"])


class ValidateKeyRequest(BaseModel):
    provider: str
    key: str


@router.post("/validate-key")
async def validate_api_key(request: ValidateKeyRequest):
    """Valide une clé API"""
    try:
        if request.provider == "claude":
            client = anthropic.Anthropic(api_key=request.key)
            # Test minimal
            client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
        elif request.provider == "mistral":
            client = MistralClient(api_key=request.key)
            # Test minimal
            client.chat(
                model="mistral-tiny",
                messages=[{"role": "user", "content": "test"}]
            )
        else:
            raise HTTPException(400, "Provider inconnu")

        return {"valid": True}
    except Exception as e:
        raise HTTPException(401, f"Clé invalide: {str(e)}")
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌────────────────────────────────────────────────────────────────┐
│ Paramètres                                                     │
├───────────────┬────────────────────────────────────────────────┤
│               │                                                │
│ 🔑 API        │  API & Modèle                                  │
│ 🤖 IA         │  ────────────────────────────────────────────  │
│ 🧠 Mémoire    │                                                │
│ 🎨 Interface  │  Fournisseur                                   │
│ 💾 Données    │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│               │  │ Claude  │ │ Mistral │ │ Ollama  │          │
│               │  │ (actif) │ │         │ │ (local) │          │
│               │  └─────────┘ └─────────┘ └─────────┘          │
│               │                                                │
│               │  Clé API                                       │
│               │  ┌─────────────────────────────┐ [Valider ✓]  │
│               │  │ sk-ant-api03-...           │               │
│               │  └─────────────────────────────┘               │
│               │                                                │
│               │  Modèle                                        │
│               │  ┌─────────────────────────────────────────┐  │
│               │  │ claude-sonnet-4-20250514             ▼ │  │
│               │  └─────────────────────────────────────────┘  │
│               │                                                │
└───────────────┴────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] 5 sections de settings
- [ ] Validation clé API
- [ ] Persistance localStorage
- [ ] Export/Import JSON
- [ ] Raccourci ⌘, fonctionne
- [ ] Tests unitaires

---

*Sprint : 3*
*Assigné : Agent Dev*
