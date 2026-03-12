import { useEffect, useState, useCallback, lazy, Suspense } from 'react';
import { ChatLayout } from './components/chat/ChatLayout';
import { Notifications } from './components/ui/Notifications';
import { GlobalErrorBoundary } from './components/ui/GlobalErrorBoundary';
import { useHealthCheck } from './hooks/useHealthCheck';
import { useFontSize, useAccessibilityStore } from './stores/accessibilityStore';
import * as api from './services/api';
import type { PanelType } from './services/windowManager';

// Lazy-loaded : panneaux secondaires et ecrans non-critiques (UltraJury perf)
const PanelWindow = lazy(() => import('./components/panels/PanelWindow').then(m => ({ default: m.PanelWindow })));
const OnboardingWizard = lazy(() => import('./components/onboarding').then(m => ({ default: m.OnboardingWizard })));
const SplashScreen = lazy(() => import('./components/SplashScreen').then(m => ({ default: m.SplashScreen })));

// Mode production Tauri (sidecar actif) : on attend que le backend soit prêt
const IS_TAURI_PRODUCTION = '__TAURI__' in window && !import.meta.env.DEV;

// Detecter si on est dans une fenetre panel
function getPanelFromUrl(): PanelType | null {
  const params = new URLSearchParams(window.location.search);
  const panel = params.get('panel');
  if (panel && ['email', 'calendar', 'tasks', 'invoices', 'crm', 'memory'].includes(panel)) {
    return panel as PanelType;
  }
  return null;
}

const activePanel = getPanelFromUrl();

function App() {
  const [backendReady, setBackendReady] = useState(!IS_TAURI_PRODUCTION);
  const [isReady, setIsReady] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);

  // Accessibilité : taille de police et contraste élevé
  const fontSize = useFontSize();
  const highContrast = useAccessibilityStore((state) => state.highContrast);

  // Health check du backend (seulement quand le backend est confirmé prêt)
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

      // Si toutes les tentatives échouent, vérifier le cache localStorage
      // avant de forcer l'onboarding
      const cached = localStorage.getItem('therese-onboarding-done');
      if (cached === 'true') {
        setShowOnboarding(false);
      } else {
        setShowOnboarding(true);
      }
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

  // Si on est dans une fenetre panel, afficher directement le panel
  if (activePanel) {
    return (
      <Suspense fallback={lazyFallback}>
        <PanelWindow panel={activePanel} />
      </Suspense>
    );
  }

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
      <div
        className="h-screen w-screen bg-bg text-text overflow-hidden"
        style={{ fontSize }}
        data-high-contrast={highContrast ? 'true' : undefined}
      >
        {/* Skip link accessibilite (visible uniquement au focus clavier) */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-3 focus:bg-accent-cyan focus:text-bg focus:rounded"
        >
          Aller au contenu principal
        </a>
        <ChatLayout />
        <Notifications />
        <Suspense fallback={null}>
          <OnboardingWizard
            isOpen={showOnboarding}
            onComplete={handleOnboardingComplete}
          />
        </Suspense>
      </div>
    </GlobalErrorBoundary>
  );
}

export default App;
