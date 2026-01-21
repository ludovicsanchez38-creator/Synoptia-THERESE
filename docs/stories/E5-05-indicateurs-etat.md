# Story E5-05 : Implémenter les indicateurs d'état

## Description

En tant que **utilisateur**,
Je veux **voir clairement l'état du système en temps réel**,
Afin de **comprendre ce que fait THÉRÈSE à tout moment**.

## Contexte technique

- **Composants impactés** : Frontend React
- **Dépendances** : E1-01, E2-03
- **Fichiers concernés** :
  - `src/frontend/src/components/StatusIndicator.tsx` (nouveau)
  - `src/frontend/src/components/ConnectionStatus.tsx` (nouveau)
  - `src/frontend/src/stores/statusStore.ts` (nouveau)

## Critères d'acceptation

- [ ] Indicateur de connexion LLM (vert/orange/rouge)
- [ ] État streaming (en train de répondre)
- [ ] Indicateur de traitement fichier
- [ ] Barre de progression pour opérations longues
- [ ] Notifications toast pour événements
- [ ] État de la mémoire (synchro Qdrant)

## Notes techniques

### Store d'état

```typescript
// stores/statusStore.ts
import { create } from 'zustand';

type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error';
type ActivityState = 'idle' | 'thinking' | 'streaming' | 'processing';

interface StatusStore {
  // Connexion
  connectionState: ConnectionState;
  lastPing: Date | null;
  latency: number | null;

  // Activité
  activityState: ActivityState;
  activityMessage: string | null;

  // Progress
  progress: {
    active: boolean;
    value: number;
    max: number;
    label: string;
  } | null;

  // Notifications
  notifications: Notification[];

  // Actions
  setConnectionState: (state: ConnectionState) => void;
  updatePing: (latency: number) => void;
  setActivity: (state: ActivityState, message?: string) => void;
  setProgress: (value: number, max: number, label: string) => void;
  clearProgress: () => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  dismissNotification: (id: string) => void;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timestamp: Date;
  duration?: number;
}

export const useStatusStore = create<StatusStore>((set, get) => ({
  connectionState: 'connecting',
  lastPing: null,
  latency: null,
  activityState: 'idle',
  activityMessage: null,
  progress: null,
  notifications: [],

  setConnectionState: (connectionState) => set({ connectionState }),

  updatePing: (latency) => set({ lastPing: new Date(), latency }),

  setActivity: (activityState, activityMessage = null) =>
    set({ activityState, activityMessage }),

  setProgress: (value, max, label) =>
    set({ progress: { active: true, value, max, label } }),

  clearProgress: () => set({ progress: null }),

  addNotification: (notification) => {
    const id = Math.random().toString(36).slice(2);
    const newNotification = {
      ...notification,
      id,
      timestamp: new Date(),
    };
    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-dismiss après durée
    if (notification.duration !== 0) {
      setTimeout(() => {
        get().dismissNotification(id);
      }, notification.duration || 5000);
    }
  },

  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
```

### Indicateur de connexion

```tsx
// components/ConnectionStatus.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, Loader } from 'lucide-react';
import { useStatusStore } from '../stores/statusStore';

export function ConnectionStatus() {
  const { connectionState, latency } = useStatusStore();

  const stateConfig = {
    connected: {
      icon: Wifi,
      color: 'text-success',
      bgColor: 'bg-success/10',
      label: 'Connecté',
    },
    connecting: {
      icon: Loader,
      color: 'text-warning',
      bgColor: 'bg-warning/10',
      label: 'Connexion...',
    },
    disconnected: {
      icon: WifiOff,
      color: 'text-text-muted',
      bgColor: 'bg-surface-elevated',
      label: 'Déconnecté',
    },
    error: {
      icon: WifiOff,
      color: 'text-error',
      bgColor: 'bg-error/10',
      label: 'Erreur',
    },
  };

  const config = stateConfig[connectionState];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs',
        config.bgColor
      )}
    >
      <Icon
        className={cn(
          'w-3.5 h-3.5',
          config.color,
          connectionState === 'connecting' && 'animate-spin'
        )}
      />
      <span className={config.color}>{config.label}</span>
      {connectionState === 'connected' && latency && (
        <span className="text-text-muted">{latency}ms</span>
      )}
    </div>
  );
}
```

### Indicateur d'activité

```tsx
// components/ActivityIndicator.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Loader, FileText, Sparkles } from 'lucide-react';
import { useStatusStore } from '../stores/statusStore';

export function ActivityIndicator() {
  const { activityState, activityMessage } = useStatusStore();

  if (activityState === 'idle') return null;

  const stateConfig = {
    thinking: {
      icon: Brain,
      label: 'Réflexion...',
      color: 'text-accent-cyan',
    },
    streaming: {
      icon: Sparkles,
      label: 'En train d\'écrire...',
      color: 'text-accent-magenta',
    },
    processing: {
      icon: FileText,
      label: 'Traitement...',
      color: 'text-warning',
    },
  };

  const config = stateConfig[activityState];
  const Icon = config.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="flex items-center gap-2 px-4 py-2"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        >
          <Icon className={cn('w-4 h-4', config.color)} />
        </motion.div>
        <span className="text-sm text-text-muted">
          {activityMessage || config.label}
        </span>
      </motion.div>
    </AnimatePresence>
  );
}
```

### Barre de progression

```tsx
// components/ProgressBar.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { useStatusStore } from '../stores/statusStore';

export function ProgressBar() {
  const { progress } = useStatusStore();

  if (!progress) return null;

  const percentage = (progress.value / progress.max) * 100;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="fixed top-0 left-0 right-0 z-50"
      >
        {/* Background */}
        <div className="h-1 bg-surface-elevated">
          {/* Progress */}
          <motion.div
            className="h-full bg-gradient-to-r from-accent-cyan to-accent-magenta"
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          />
        </div>

        {/* Label */}
        <div className="absolute top-2 left-1/2 -translate-x-1/2">
          <div className="px-3 py-1 bg-surface border border-border rounded-full text-xs text-text-muted shadow-lg">
            {progress.label} - {Math.round(percentage)}%
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
```

### Notifications Toast

```tsx
// components/Notifications.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useStatusStore } from '../stores/statusStore';

export function Notifications() {
  const { notifications, dismissNotification } = useStatusStore();

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    success: 'border-success bg-success/10',
    error: 'border-error bg-error/10',
    warning: 'border-warning bg-warning/10',
    info: 'border-info bg-info/10',
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      <AnimatePresence>
        {notifications.map((notification) => {
          const Icon = icons[notification.type];

          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              className={cn(
                'flex items-start gap-3 p-4 rounded-xl border shadow-lg backdrop-blur-sm',
                colors[notification.type]
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-text">{notification.title}</p>
                {notification.message && (
                  <p className="text-sm text-text-muted mt-1">{notification.message}</p>
                )}
              </div>
              <button
                onClick={() => dismissNotification(notification.id)}
                className="p-1 hover:bg-surface rounded"
              >
                <X className="w-4 h-4 text-text-muted" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
```

### Hook de santé

```typescript
// hooks/useHealthCheck.ts
import { useEffect } from 'react';
import { useStatusStore } from '../stores/statusStore';

export function useHealthCheck() {
  const { setConnectionState, updatePing } = useStatusStore();

  useEffect(() => {
    let interval: NodeJS.Timer;

    const checkHealth = async () => {
      const start = Date.now();
      try {
        const response = await fetch('/api/health');
        if (response.ok) {
          const latency = Date.now() - start;
          setConnectionState('connected');
          updatePing(latency);
        } else {
          setConnectionState('error');
        }
      } catch {
        setConnectionState('disconnected');
      }
    };

    // Check initial
    checkHealth();

    // Polling toutes les 30s
    interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, [setConnectionState, updatePing]);
}
```

## Estimation

- **Complexité** : XS
- **Points** : 2

## Maquette

```
┌─────────────────────────────────────────────────────────────┐
│ ████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│           Indexation fichiers - 67%                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                      [Chat Area]                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 🧠 En train de réfléchir...                                 │
└─────────────────────────────────────────────────────────────┘
                                        ┌──────────────────────┐
                                        │ ✓ 3 fichiers indexés │
                                        │   Mémoire mise à jour│
                                        └──────────────────────┘
```

## Definition of Done

- [ ] Indicateur connexion visible
- [ ] États d'activité affichés
- [ ] Barre de progression fonctionne
- [ ] Notifications toast
- [ ] Health check automatique
- [ ] Tests unitaires

---

*Sprint : 2*
*Assigné : Agent Dev Frontend*
