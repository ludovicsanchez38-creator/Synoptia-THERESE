# Story E5-08 : Implémenter l'onboarding premier lancement

## Description

En tant que **nouvel utilisateur**,
Je veux **être guidé lors du premier lancement**,
Afin de **configurer THÉRÈSE rapidement et comprendre ses fonctionnalités**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E1-01, E5-07
- **Fichiers concernés** :
  - `src/frontend/src/components/Onboarding.tsx` (nouveau)
  - `src/frontend/src/stores/onboardingStore.ts` (nouveau)

## Critères d'acceptation

- [ ] Détection premier lancement
- [ ] Wizard multi-étapes (4-5 étapes)
- [ ] Configuration clé API obligatoire
- [ ] Présentation des fonctionnalités clés
- [ ] Possibilité de skip (avec warning)
- [ ] Animation engageante
- [ ] Progression sauvegardée

## Notes techniques

### Store onboarding

```typescript
// stores/onboardingStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface OnboardingStore {
  hasCompletedOnboarding: boolean;
  currentStep: number;
  skipped: boolean;

  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  complete: () => void;
  skip: () => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingStore>()(
  persist(
    (set) => ({
      hasCompletedOnboarding: false,
      currentStep: 0,
      skipped: false,

      setStep: (currentStep) => set({ currentStep }),
      nextStep: () => set((state) => ({ currentStep: state.currentStep + 1 })),
      prevStep: () => set((state) => ({ currentStep: Math.max(0, state.currentStep - 1) })),
      complete: () => set({ hasCompletedOnboarding: true, currentStep: 0 }),
      skip: () => set({ hasCompletedOnboarding: true, skipped: true }),
      reset: () => set({ hasCompletedOnboarding: false, currentStep: 0, skipped: false }),
    }),
    {
      name: 'onboarding-state',
    }
  )
);
```

### Composant Onboarding

```tsx
// components/Onboarding.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { useOnboardingStore } from '../stores/onboardingStore';
import { useSettingsStore } from '../stores/settingsStore';
import {
  WelcomeStep,
  ApiKeyStep,
  FeaturesStep,
  PersonalizeStep,
  CompleteStep,
} from './onboarding';

const steps = [
  { id: 'welcome', component: WelcomeStep },
  { id: 'apikey', component: ApiKeyStep },
  { id: 'features', component: FeaturesStep },
  { id: 'personalize', component: PersonalizeStep },
  { id: 'complete', component: CompleteStep },
];

export function Onboarding() {
  const { hasCompletedOnboarding, currentStep, nextStep, prevStep, complete, skip } =
    useOnboardingStore();

  if (hasCompletedOnboarding) return null;

  const CurrentStepComponent = steps[currentStep].component;
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <div className="fixed inset-0 z-50 bg-bg flex items-center justify-center">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent-cyan/5 via-bg to-accent-magenta/5" />

      {/* Content */}
      <div className="relative w-full max-w-2xl px-8">
        {/* Progress */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                'w-2 h-2 rounded-full transition-all',
                index === currentStep
                  ? 'w-8 bg-accent-cyan'
                  : index < currentStep
                  ? 'bg-accent-cyan/50'
                  : 'bg-border'
              )}
            />
          ))}
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <CurrentStepComponent />
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          <div>
            {!isFirstStep && (
              <button
                onClick={prevStep}
                className="px-4 py-2 text-text-muted hover:text-text transition-colors"
              >
                Retour
              </button>
            )}
          </div>

          <div className="flex items-center gap-4">
            {!isLastStep && (
              <button
                onClick={skip}
                className="text-sm text-text-muted hover:text-text transition-colors"
              >
                Passer
              </button>
            )}

            <button
              onClick={isLastStep ? complete : nextStep}
              className="px-6 py-2 bg-accent-cyan text-bg rounded-lg font-medium hover:bg-accent-cyan/90 transition-colors"
            >
              {isLastStep ? 'Commencer' : 'Continuer'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### Étape Bienvenue

```tsx
// components/onboarding/WelcomeStep.tsx
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

export function WelcomeStep() {
  return (
    <div className="text-center">
      {/* Logo animé */}
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, type: 'spring' }}
        className="w-24 h-24 mx-auto mb-8 rounded-2xl bg-gradient-to-br from-accent-cyan to-accent-magenta p-0.5"
      >
        <div className="w-full h-full bg-bg rounded-2xl flex items-center justify-center">
          <Sparkles className="w-12 h-12 text-accent-cyan" />
        </div>
      </motion.div>

      <motion.h1
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-3xl font-bold text-text mb-4"
      >
        Bienvenue sur THÉRÈSE
      </motion.h1>

      <motion.p
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-text-muted text-lg max-w-md mx-auto"
      >
        Ton assistante IA avec de la mémoire.
        <br />
        <span className="text-accent-cyan">Ta mémoire, tes données, ton business.</span>
      </motion.p>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mt-8 flex items-center justify-center gap-6 text-sm text-text-muted"
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-success" />
          100% local
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-accent-cyan" />
          Mémoire persistante
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-accent-magenta" />
          Fait pour toi
        </div>
      </motion.div>
    </div>
  );
}
```

### Étape Clé API

```tsx
// components/onboarding/ApiKeyStep.tsx
import { useState } from 'react';
import { Key, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';

export function ApiKeyStep() {
  const { apiKey, apiProvider, updateSettings } = useSettingsStore();
  const [validating, setValidating] = useState(false);
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateKey = async (key: string) => {
    if (!key) return;
    setValidating(true);
    setError(null);

    try {
      const response = await fetch('/api/settings/validate-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: apiProvider, key }),
      });

      if (response.ok) {
        setIsValid(true);
        updateSettings({ apiKey: key });
      } else {
        const data = await response.json();
        setIsValid(false);
        setError(data.detail || 'Clé invalide');
      }
    } catch {
      setIsValid(false);
      setError('Erreur de connexion');
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="text-center">
      <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-accent-cyan/10 flex items-center justify-center">
        <Key className="w-8 h-8 text-accent-cyan" />
      </div>

      <h2 className="text-2xl font-bold text-text mb-2">Configure ton accès IA</h2>
      <p className="text-text-muted mb-8">
        THÉRÈSE utilise Claude par défaut. Entre ta clé API Anthropic.
      </p>

      <div className="max-w-md mx-auto">
        <div className="relative">
          <input
            type="password"
            defaultValue={apiKey}
            onChange={(e) => {
              setIsValid(null);
              setError(null);
            }}
            onBlur={(e) => validateKey(e.target.value)}
            placeholder="sk-ant-api03-..."
            className={cn(
              'w-full px-4 py-3 bg-surface-elevated border rounded-lg text-text text-center',
              isValid === true && 'border-success',
              isValid === false && 'border-error',
              isValid === null && 'border-border'
            )}
          />

          {/* Status icon */}
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            {validating && <Loader className="w-5 h-5 text-text-muted animate-spin" />}
            {isValid === true && <CheckCircle className="w-5 h-5 text-success" />}
            {isValid === false && <AlertCircle className="w-5 h-5 text-error" />}
          </div>
        </div>

        {error && (
          <p className="mt-2 text-sm text-error">{error}</p>
        )}

        {isValid === true && (
          <p className="mt-2 text-sm text-success">Clé valide ! Tu peux continuer.</p>
        )}

        <p className="mt-4 text-xs text-text-muted">
          Pas de clé ? Crée un compte sur{' '}
          <a
            href="https://console.anthropic.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent-cyan hover:underline"
          >
            console.anthropic.com
          </a>
        </p>
      </div>
    </div>
  );
}
```

### Étape Fonctionnalités

```tsx
// components/onboarding/FeaturesStep.tsx
import { motion } from 'framer-motion';
import { Brain, FileText, MessageSquare, Sparkles } from 'lucide-react';

const features = [
  {
    icon: MessageSquare,
    title: 'Chat intelligent',
    description: 'Discute naturellement avec une IA qui comprend ton contexte',
    color: 'text-accent-cyan',
  },
  {
    icon: Brain,
    title: 'Mémoire persistante',
    description: 'THÉRÈSE se souvient de tes contacts, projets et préférences',
    color: 'text-accent-magenta',
  },
  {
    icon: FileText,
    title: 'Analyse de fichiers',
    description: 'Glisse tes PDF, DOCX pour les résumer ou poser des questions',
    color: 'text-success',
  },
  {
    icon: Sparkles,
    title: 'Extraction auto',
    description: 'Les informations importantes sont automatiquement mémorisées',
    color: 'text-warning',
  },
];

export function FeaturesStep() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-text text-center mb-2">
        Ce que THÉRÈSE peut faire
      </h2>
      <p className="text-text-muted text-center mb-8">
        Une assistante qui grandit avec toi
      </p>

      <div className="grid grid-cols-2 gap-4">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 bg-surface border border-border rounded-xl"
            >
              <Icon className={cn('w-8 h-8 mb-3', feature.color)} />
              <h3 className="font-medium text-text mb-1">{feature.title}</h3>
              <p className="text-sm text-text-muted">{feature.description}</p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
```

### Étape Personnalisation

```tsx
// components/onboarding/PersonalizeStep.tsx
import { User, Briefcase, Code, Palette } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';

const profiles = [
  { id: 'entrepreneur', label: 'Entrepreneur', icon: Briefcase, prompt: 'Tu aides un entrepreneur à gérer son business.' },
  { id: 'developer', label: 'Développeur', icon: Code, prompt: 'Tu aides un développeur avec ses projets techniques.' },
  { id: 'creative', label: 'Créatif', icon: Palette, prompt: 'Tu aides un créatif dans ses projets artistiques.' },
  { id: 'general', label: 'Général', icon: User, prompt: 'Tu es une assistante généraliste polyvalente.' },
];

export function PersonalizeStep() {
  const { updateSettings } = useSettingsStore();
  const [selected, setSelected] = useState('entrepreneur');

  const handleSelect = (profileId: string) => {
    setSelected(profileId);
    const profile = profiles.find((p) => p.id === profileId);
    if (profile) {
      updateSettings({
        systemPrompt: `Tu es THÉRÈSE, une assistante IA française.
${profile.prompt}
Tu mémorises les informations importantes pour les conversations futures.`
      });
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-text text-center mb-2">
        Personnalise THÉRÈSE
      </h2>
      <p className="text-text-muted text-center mb-8">
        Choisis un profil pour adapter son comportement
      </p>

      <div className="grid grid-cols-2 gap-4">
        {profiles.map((profile) => {
          const Icon = profile.icon;
          const isSelected = selected === profile.id;

          return (
            <button
              key={profile.id}
              onClick={() => handleSelect(profile.id)}
              className={cn(
                'p-4 rounded-xl border text-left transition-all',
                isSelected
                  ? 'border-accent-cyan bg-accent-cyan/10'
                  : 'border-border hover:border-accent-cyan/50'
              )}
            >
              <Icon className={cn(
                'w-8 h-8 mb-3',
                isSelected ? 'text-accent-cyan' : 'text-text-muted'
              )} />
              <p className="font-medium text-text">{profile.label}</p>
            </button>
          );
        })}
      </div>

      <p className="mt-6 text-sm text-text-muted text-center">
        Tu pourras modifier cela dans les paramètres plus tard
      </p>
    </div>
  );
}
```

### Étape Finale

```tsx
// components/onboarding/CompleteStep.tsx
import { motion } from 'framer-motion';
import { Rocket, Keyboard, Command } from 'lucide-react';

export function CompleteStep() {
  return (
    <div className="text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', duration: 0.5 }}
        className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-accent-cyan to-accent-magenta flex items-center justify-center"
      >
        <Rocket className="w-10 h-10 text-white" />
      </motion.div>

      <h2 className="text-2xl font-bold text-text mb-2">C'est parti !</h2>
      <p className="text-text-muted mb-8">
        THÉRÈSE est prête. Voici quelques raccourcis utiles :
      </p>

      <div className="max-w-sm mx-auto space-y-3">
        <div className="flex items-center justify-between p-3 bg-surface border border-border rounded-lg">
          <div className="flex items-center gap-3">
            <Command className="w-4 h-4 text-text-muted" />
            <span className="text-text">Command palette</span>
          </div>
          <kbd className="px-2 py-1 bg-surface-elevated rounded text-xs text-text-muted">⌘K</kbd>
        </div>

        <div className="flex items-center justify-between p-3 bg-surface border border-border rounded-lg">
          <div className="flex items-center gap-3">
            <Keyboard className="w-4 h-4 text-text-muted" />
            <span className="text-text">Nouvelle conversation</span>
          </div>
          <kbd className="px-2 py-1 bg-surface-elevated rounded text-xs text-text-muted">⌘N</kbd>
        </div>

        <div className="flex items-center justify-between p-3 bg-surface border border-border rounded-lg">
          <div className="flex items-center gap-3">
            <Keyboard className="w-4 h-4 text-text-muted" />
            <span className="text-text">Envoyer message</span>
          </div>
          <kbd className="px-2 py-1 bg-surface-elevated rounded text-xs text-text-muted">⌘↵</kbd>
        </div>
      </div>

      <p className="mt-8 text-sm text-text-muted">
        Tape <kbd className="px-1.5 py-0.5 bg-surface-elevated rounded text-xs">⌘/</kbd> à tout moment pour voir tous les raccourcis
      </p>
    </div>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Flux

```
┌─────────────────────────────────────────────────────────────┐
│                         ● ● ● ○ ○                           │
│                                                             │
│                           ✨                                │
│                                                             │
│                  Bienvenue sur THÉRÈSE                      │
│                                                             │
│         Ton assistante IA avec de la mémoire.               │
│      Ta mémoire, tes données, ton business.                 │
│                                                             │
│        ○ 100% local   ○ Mémoire   ○ Fait pour toi           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                      [Passer]  [Continuer]  │
└─────────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Détection premier lancement
- [ ] 5 étapes complètes
- [ ] Validation clé API
- [ ] Animation fluide
- [ ] Skip avec warning
- [ ] Progression sauvegardée
- [ ] Tests E2E

---

*Sprint : 3*
*Assigné : Agent Dev Frontend*
