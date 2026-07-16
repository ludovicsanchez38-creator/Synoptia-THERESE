/**
 * THERESE v2 - Onboarding Wizard
 *
 * Full-screen modal wizard for first-time setup.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check } from 'lucide-react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { WelcomeStep } from './WelcomeStep';
import { ProfileStep } from './ProfileStep';
import { LLMStep } from './LLMStep';
import { SecurityStep } from './SecurityStep';
import { WorkingDirStep } from './WorkingDirStep';
import { CompleteStep } from './CompleteStep';
import type { LLMProvider } from '../../services/api';
import { Z_LAYER } from '../../styles/z-layers';

interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: () => void;
}

const STEPS = [
  { id: 'welcome', title: 'Bienvenue' },
  { id: 'profile', title: 'Profil' },
  { id: 'llm', title: 'LLM' },
  { id: 'security', title: 'Sécurité' },
  { id: 'workingDir', title: 'Dossier' },
  { id: 'complete', title: 'Terminé' },
];

export function OnboardingWizard({ isOpen, onComplete }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = backward
  const [configuredProvider, setConfiguredProvider] = useState<LLMProvider | null>(null);

  // Window controls
  const handleMinimize = () => getCurrentWindow().minimize();
  const handleMaximize = () => getCurrentWindow().toggleMaximize();
  const handleClose = () => getCurrentWindow().close();

  // BUG-traffic-lights : afficher les traffic lights uniquement sur macOS
  // navigator.platform est déprécié mais reste le seul moyen fiable sous WKWebView (Tauri macOS)
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);
  // Sur Windows + Linux : tauri.conf.json a decorations:false → pas de barre de titre native
  // On affiche un bouton fermer minimaliste pour que la fenêtre soit fermable
  const isDesktopNonMac = typeof navigator !== 'undefined' && !isMac;

  // Reset on open
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      setDirection(1);
      setConfiguredProvider(null);
    }
  }, [isOpen]);

  function goNext() {
    setDirection(1);
    setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
  }

  function goBack() {
    setDirection(-1);
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  }

  function completeLlmStep(provider: LLMProvider | null) {
    setConfiguredProvider(provider);
    goNext();
  }

  function handleComplete() {
    onComplete();
  }

  // Keyboard navigation
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        // Only allow escape on welcome step to close
        if (currentStep === 0) {
          // Could close, but better to force completion
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStep]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={`fixed inset-0 ${Z_LAYER.ONBOARDING} flex items-center justify-center`}
        >
          {/* Backdrop with blur */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-bg/95 backdrop-blur-xl"
          />

          {/* Window Title Bar with controls */}
          <div
            data-tauri-drag-region
            className={`absolute top-0 left-0 right-0 h-10 ${Z_LAYER.ONBOARDING_TOP} flex items-center px-4`}
          >
            {/* Window controls (macOS style uniquement) */}
            {isMac && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleClose}
                  className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-600 transition-colors"
                  title="Fermer"
                />
                <button
                  onClick={handleMinimize}
                  className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-600 transition-colors"
                  title="Réduire"
                />
                <button
                  onClick={handleMaximize}
                  className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-600 transition-colors"
                  title="Agrandir"
                />
              </div>
            )}
            {/* Windows/Linux : decorations:false → pas de barre de titre native.
                Afficher un bouton fermer discret pour que la fenêtre soit fermable. */}
            {isDesktopNonMac && (
              <button
                onClick={handleClose}
                className="ml-auto p-1 rounded hover:bg-surface-elevated/60 transition-colors text-text-muted hover:text-text"
                title="Fermer (Échap)"
                aria-label="Fermer"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </button>
            )}
          </div>

          {/* Modal Container */}
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-title"
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            data-testid="onboarding-wizard"
            className="relative w-full max-w-2xl max-h-[90vh] bg-surface border border-border/50 rounded-2xl shadow-2xl flex flex-col mt-10"
          >
            {/* Progress Header */}
            <div className="px-8 py-4 border-b border-border/30">
              {/* Step Indicators */}
              <div className="flex items-center justify-between">
                {STEPS.map((step, index) => (
                  <div key={step.id} className="flex items-center">
                    {/* Step Circle */}
                    <motion.div
                      initial={false}
                      animate={{
                        scale: index === currentStep ? 1.1 : 1,
                        backgroundColor:
                          index < currentStep
                            ? 'rgb(34 211 238)' // accent-cyan
                            : index === currentStep
                            ? 'rgba(34, 211, 238, 0.2)'
                            : 'rgba(255, 255, 255, 0.05)',
                        borderColor:
                          index <= currentStep
                            ? 'rgb(34 211 238)'
                            : 'rgba(255, 255, 255, 0.1)',
                      }}
                      transition={{ duration: 0.2 }}
                      className={`w-8 h-8 rounded-full border-2 flex items-center justify-center ${
                        index < currentStep
                          ? 'text-white' // sur le fond cyan vif plein : blanc lisible dans les 2 themes
                          : index === currentStep
                          ? 'text-text' // sur le fond cyan teinte (20%) : texte token lisible (clair/sombre)
                          : 'text-text-muted'
                      }`}
                    >
                      {index < currentStep ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <span className="text-xs font-medium">{index + 1}</span>
                      )}
                    </motion.div>

                    {/* Connector Line */}
                    {index < STEPS.length - 1 && (
                      <div className="w-12 h-0.5 mx-1">
                        <motion.div
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: index < currentStep ? 1 : 0 }}
                          transition={{ duration: 0.3 }}
                          className="h-full bg-accent-cyan origin-left"
                        />
                        <div className="h-full bg-border/30 -mt-0.5" />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Progress Bar */}
              <div className="mt-3 h-1 bg-border/20 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
                  transition={{ duration: 0.3 }}
                  className="h-full bg-accent-cyan"
                />
              </div>
            </div>

            {/* Step Content */}
            <div className="flex-1 overflow-y-auto relative">
              <AnimatePresence mode="wait" custom={direction}>
                <motion.div
                  key={currentStep}
                  custom={direction}
                  initial={{ opacity: 0, x: direction * 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: direction * -50 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  {currentStep === 0 && <div data-testid="onboarding-step-0"><WelcomeStep onNext={goNext} /></div>}
                  {currentStep === 1 && <div data-testid="onboarding-step-1"><ProfileStep onNext={goNext} onBack={goBack} /></div>}
                  {currentStep === 2 && <div data-testid="onboarding-step-2"><LLMStep onNext={completeLlmStep} onBack={goBack} /></div>}
                  {currentStep === 3 && <div data-testid="onboarding-step-3"><SecurityStep provider={configuredProvider} onNext={goNext} onBack={goBack} /></div>}
                  {currentStep === 4 && <div data-testid="onboarding-step-4"><WorkingDirStep onNext={goNext} onBack={goBack} /></div>}
                  {currentStep === 5 && <div data-testid="onboarding-step-5"><CompleteStep onComplete={handleComplete} onBack={goBack} /></div>}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
