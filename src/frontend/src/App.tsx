import { useEffect, useState } from 'react';
import { ChatLayout } from './components/chat/ChatLayout';
import { PanelWindow } from './components/panels/PanelWindow';
import { Notifications } from './components/ui/Notifications';
import { OnboardingWizard } from './components/onboarding';
import { useHealthCheck } from './hooks/useHealthCheck';
import * as api from './services/api';
import type { PanelType } from './services/windowManager';

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
  const [isReady, setIsReady] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);

  // Health check du backend
  useHealthCheck();

  // SEC-010: Initialize auth token at startup then check onboarding
  useEffect(() => {
    async function initAndCheckOnboarding() {
      // First, initialize auth token
      await api.initializeAuth();

      // Small delay to ensure backend is ready
      await new Promise(resolve => setTimeout(resolve, 300));

      // Then check onboarding status
      try {
        const status = await api.getOnboardingStatus();
        setShowOnboarding(!status.completed);
      } catch (err) {
        // If API fails, assume onboarding needed
        console.error('Failed to check onboarding status:', err);
        setShowOnboarding(true);
      } finally {
        setCheckingOnboarding(false);
      }
    }

    initAndCheckOnboarding();
  }, []);

  useEffect(() => {
    // Ready once onboarding check is complete
    if (!checkingOnboarding) {
      setIsReady(true);
    }
  }, [checkingOnboarding]);

  function handleOnboardingComplete() {
    setShowOnboarding(false);
  }

  // Si on est dans une fenetre panel, afficher directement le panel
  if (activePanel) {
    return <PanelWindow panel={activePanel} />;
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
    <div className="h-screen w-screen bg-bg text-text overflow-hidden">
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
