import { useEffect, useState, useCallback, lazy, Suspense } from 'react';
import { MotionConfig } from 'framer-motion';
import { ChatLayout } from './components/chat/ChatLayout';
import { CommonToolConfirmationLayer } from './components/app/CommonToolConfirmationLayer';
import { PrototypeExternalActionConfirmationProvider } from './components/app/ExternalActionConfirmation';
import { ActionPanel } from './components/actions';
import { Notifications } from './components/ui/Notifications';
import { UpdateBanner } from './components/ui/UpdateBanner';
import { GlobalErrorBoundary } from './components/ui/GlobalErrorBoundary';
import { useHealthCheck } from './hooks/useHealthCheck';
import { useFontSize, useAccessibilityStore } from './stores/accessibilityStore';
import { prefersReducedMotion, onReducedMotionChange } from './lib/accessibility';
import * as api from './services/api';
import { Z_LAYER } from './styles/z-layers';
import { getInterfaceMode } from './lib/interfaceMode';
import { useAccessibilityRoot } from './hooks/useAccessibilityRoot';

// Lazy-loaded : ecrans non-critiques (UltraJury perf)
const OnboardingWizard = lazy(() => import('./components/onboarding').then(m => ({ default: m.OnboardingWizard })));
const SplashScreen = lazy(() => import('./components/SplashScreen').then(m => ({ default: m.SplashScreen })));
const ConversationCanvasPrototype = lazy(() =>
  import('./components/prototype/ConversationCanvasPrototype').then(m => ({ default: m.ConversationCanvasPrototype }))
);

// Mode production Tauri (sidecar actif) : on attend que le backend soit prêt
const IS_TAURI_PRODUCTION = '__TAURI__' in window && !import.meta.env.DEV;

// Phase 1 (revue produit) : plus de fenêtres-panels détachées. Email/Agenda/Tâches/
// Factures/CRM/Mémoire sont des vues/panneaux de la fenêtre principale (content-swap).

function ApplicationBootstrap() {
  const interfaceMode = getInterfaceMode();
  const [backendReady, setBackendReady] = useState(!IS_TAURI_PRODUCTION);
  const [isReady, setIsReady] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);

  // Accessibilite : taille de police et contraste eleve
  const fontSize = useFontSize();
  const highContrast = useAccessibilityStore((state) => state.highContrast);
  const theme = useAccessibilityStore((state) => state.theme);
  const setReduceMotion = useAccessibilityStore((state) => state.setReduceMotion);
  // US-013 : MotionConfig global
  const reduceMotion = useAccessibilityStore((state) => state.reduceMotion);
  useAccessibilityRoot(fontSize, reduceMotion);

  // Refonte DA : applique le theme clair/sombre sur <html> pour que tout le
  // document (body, #root, chrome de fenetre) suive les variables de couleur.
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // US-012 : Detecter la preference systeme reduced-motion au premier lancement
  // et synchroniser avec le store. Ecoute aussi les changements en temps reel.
  useEffect(() => {
    // Initialiser avec la preference systeme si le store n'a pas ete modifie manuellement
    const stored = localStorage.getItem('therese-accessibility');
    if (!stored) {
      // Premier lancement : utiliser la preference systeme
      setReduceMotion(prefersReducedMotion());
    }

    // Ecouter les changements systeme en temps reel
    const unsubscribe = onReducedMotionChange((reduced) => {
      setReduceMotion(reduced);
    });

    return unsubscribe;
  }, [setReduceMotion]);

  // Health check du backend (seulement quand le backend est confirme pret)
  useHealthCheck(backendReady);

  // Callback quand le SplashScreen détecte le backend prêt
  const handleBackendReady = useCallback(() => {
    setBackendReady(true);
  }, []);

  // SEC-010: Initialize auth token at startup then check onboarding
  // (seulement quand le backend est prêt)
  useEffect(() => {
    if (!backendReady) return;

    async function initAndCheckOnboarding() {
      // Retry loop : le backend peut mettre un instant à démarrer
      const maxRetries = 5;
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          // Récupérer le token de session
          await api.initializeAuth();

          // Vérifier le statut onboarding
          const status = await api.getOnboardingStatus();
          setShowOnboarding(!status.completed);
          setCheckingOnboarding(false);
          return;
        } catch (err) {
          console.warn(`Tentative ${attempt}/${maxRetries} échouée:`, err);
          if (attempt < maxRetries) {
            // Attendre un peu plus à chaque tentative
            await new Promise(resolve => setTimeout(resolve, attempt * 500));
          }
        }
      }

      // Si toutes les tentatives echouent : NE PAS montrer l'onboarding
      // pour eviter d'ecraser une DB existante (BUG perte de donnees v0.6.2)
      console.error('Impossible de verifier le statut onboarding apres 5 tentatives');
      setShowOnboarding(false);
      setCheckingOnboarding(false);
    }

    initAndCheckOnboarding();
  }, [backendReady]);

  useEffect(() => {
    // Ready once onboarding check is complete
    if (!checkingOnboarding) {
      setIsReady(true);
    }
  }, [checkingOnboarding]);

  function handleOnboardingComplete() {
    setShowOnboarding(false);
    localStorage.setItem('therese-onboarding-done', 'true');
  }

  // Fallback de chargement pour les composants lazy
  const lazyFallback = (
    <div className="h-screen w-screen bg-bg flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent">
          THERESE
        </h1>
        <p className="text-text-muted mt-2 text-sm">Chargement...</p>
      </div>
    </div>
  );

  // En production Tauri : SplashScreen pendant le démarrage du sidecar
  if (!backendReady) {
    return (
      <Suspense fallback={lazyFallback}>
        <SplashScreen onReady={handleBackendReady} />
      </Suspense>
    );
  }

  if (!isReady) {
    return (
      <div className="h-screen w-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent">
            THERESE
          </h1>
          <p className="text-text-muted mt-2 text-sm">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <GlobalErrorBoundary>
      {/* US-013 : MotionConfig global - reduceMotion (réglage utilisateur)
          coupe TOUTES les animations framer-motion d'un coup ; 'user' suit
          prefers-reduced-motion système. Complété par le @media CSS. */}
      <MotionConfig reducedMotion={reduceMotion ? 'always' : 'user'}>
      <div
        className="relative h-screen w-screen bg-bg text-text overflow-hidden"
        data-testid="app-main"
        data-interface-mode={interfaceMode}
        data-theme={theme}
        data-high-contrast={highContrast ? 'true' : undefined}
      >
        <UpdateBanner />
        {/* Skip link accessibilite (visible uniquement au focus clavier) */}
        <a
          href="#main-content"
          className={`sr-only focus:not-sr-only focus:absolute focus:${Z_LAYER.MODAL} focus:p-3 focus:bg-accent-cyan focus:text-bg focus:rounded`}
        >
          Aller au contenu principal
        </a>
        {interfaceMode === 'conversation-canvas' ? (
          <Suspense fallback={<div className="h-screen w-screen bg-bg" />}>
            <PrototypeExternalActionConfirmationProvider>
              <ConversationCanvasPrototype />
            </PrototypeExternalActionConfirmationProvider>
          </Suspense>
        ) : (
          <ChatLayout />
        )}

        {/* Le suivi des actions appartient à la coquille commune. Une action
            lancée depuis l’interface unifiée reste donc visible sans bascule. */}
        <ActionPanel />

        {/* Les confirmations sensibles appartiennent à la coquille commune :
            elles restent visibles quelle que soit l'interface active. */}
        <CommonToolConfirmationLayer />
        <Notifications />
        <Suspense fallback={null}>
          <OnboardingWizard
            isOpen={showOnboarding}
            onComplete={handleOnboardingComplete}
          />
        </Suspense>
      </div>
      </MotionConfig>
    </GlobalErrorBoundary>
  );
}

function App() {
  return <ApplicationBootstrap />;
}

export default App;
