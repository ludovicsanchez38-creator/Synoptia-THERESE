import { useEffect, useState, useCallback } from 'react';
import { ChatLayout } from './components/chat/ChatLayout';
import { PanelWindow } from './components/panels/PanelWindow';
import { Notifications } from './components/ui/Notifications';
import { OnboardingWizard } from './components/onboarding';
import { SplashScreen } from './components/SplashScreen';
import { useHealthCheck } from './hooks/useHealthCheck';
import { useFontSize, useAccessibilityStore } from './stores/accessibilityStore';
import * as api from './services/api';
import type { PanelType } from './services/windowManager';

// Mode production Tauri (sidecar actif) : on attend que le backend soit prêt
const IS_TAURI_PRODUCTION = '__TAURI__' in window && !import.meta.env.DEV;

// Detecter si on est dans une fenetre panel
function getPanelFromUrl(): PanelType | null {
  const params = new URLSearchParams(window.location.search);
  const panel = params.get('panel');
  if (panel && ['email', 'calendar', 'tasks', 'invoices', 'crm'].includes(panel)) {
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

  // Health check du backend
  useHealthCheck();

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

  // Si on est dans une fenetre panel, afficher directement le panel
  if (activePanel) {
    return <PanelWindow panel={activePanel} />;
  }

  // En production Tauri : SplashScreen pendant le démarrage du sidecar
  if (!backendReady) {
    return <SplashScreen onReady={handleBackendReady} />;
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
    <div
      className="h-screen w-screen bg-bg text-text overflow-hidden"
      style={{ fontSize }}
      data-high-contrast={highContrast ? 'true' : undefined}
    >
      <ChatLayout />
      <Notifications />
      <OnboardingWizard
        isOpen={showOnboarding}
        onComplete={handleOnboardingComplete}
      />
    </div>
  );
}

export default App;
