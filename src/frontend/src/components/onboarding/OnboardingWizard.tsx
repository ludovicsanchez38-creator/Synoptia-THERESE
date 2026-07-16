/**
 * THERESE v2 - Onboarding Wizard
 *
 * Full-screen modal wizard for first-time setup.
 */

import { useState, useEffect, useRef } from 'react';
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
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

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
  const dialogRef = useRef<HTMLDivElement>(null);

  // Window controls
  const handleMinimize = () => getCurrentWindow().minimize();
  const handleMaximize = () => getCurrentWindow().toggleMaximize();
  const handleClose = () => getCurrentWindow().close();
  useDialogFocusTrap(dialogRef, { active: isOpen, onEscape: handleClose, isolateBackground: true });

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

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={`fixed inset-0 ${Z_LAYER.ONBOARDING} flex items-center justify-center p-2 sm:p-4`}
        >
          {/* Backdrop with blur */}
          <motion.div
            data-dialog-backdrop
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-bg/95 backdrop-blur-xl"
          />

          {/* Window Title Bar with controls */}
          <div
            data-tauri-drag-region
            data-dialog-allow
            className={`absolute left-0 right-0 top-0 h-12 ${Z_LAYER.ONBOARDING_TOP} flex items-center px-2 sm:px-4`}
          >
            {/* Window controls (macOS style uniquement) */}
            {isMac && (
              <div className="flex items-center" aria-label="Contrôles de la fenêtre">
                <button
                  onClick={handleClose}
                  className="grid h-11 w-11 place-items-center rounded-full"
                  title="Fermer"
                  aria-label="Fermer la fenêtre"
                ><span className="h-3 w-3 rounded-full bg-red-500" /></button>
                <button
                  onClick={handleMinimize}
                  className="grid h-11 w-11 place-items-center rounded-full"
                  title="Réduire"
                  aria-label="Réduire la fenêtre"
                ><span className="h-3 w-3 rounded-full bg-yellow-500" /></button>
                <button
                  onClick={handleMaximize}
                  className="grid h-11 w-11 place-items-center rounded-full"
                  title="Agrandir"
                  aria-label="Agrandir la fenêtre"
                ><span className="h-3 w-3 rounded-full bg-green-500" /></button>
              </div>
            )}
            {/* Windows/Linux : decorations:false → pas de barre de titre native.
                Afficher un bouton fermer discret pour que la fenêtre soit fermable. */}
            {isDesktopNonMac && (
              <button
                onClick={handleClose}
                className="ml-auto grid h-11 w-11 place-items-center rounded text-text-muted transition-colors hover:bg-surface-elevated/60 hover:text-text"
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
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-title"
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            data-testid="onboarding-wizard"
            className="relative mt-12 flex max-h-[calc(100vh-4rem)] w-full min-w-0 max-w-2xl flex-col overflow-hidden rounded-2xl border border-border/50 bg-surface shadow-2xl"
          >
            <h1 id="onboarding-title" tabIndex={-1} data-dialog-autofocus className="sr-only">
              Configuration initiale de Thérèse
            </h1>
            {/* Progress Header */}
            <div className="border-b border-border/30 px-3 py-3 sm:px-8 sm:py-4">
              {/* Step Indicators */}
              <ol className="grid grid-cols-6 items-center" aria-label="Étapes de configuration">
                {STEPS.map((step, index) => (
                  <li key={step.id} className="flex min-w-0 items-center justify-center" aria-current={index === currentStep ? 'step' : undefined}>
                    <span className="sr-only">{step.title}</span>
                    {/* Step Circle */}
                    <motion.div
                      initial={false}
                      animate={{ scale: index === currentStep ? 1.1 : 1 }}
                      transition={{ duration: 0.2 }}
                      className={`flex h-7 w-7 items-center justify-center rounded-full border-2 sm:h-8 sm:w-8 ${
                        index < currentStep
                          ? 'border-accent-fill bg-accent-fill text-accent-ink'
                          : index === currentStep
                          ? 'border-accent bg-accent-tint text-text'
                          : 'border-border bg-surface-2 text-text-muted'
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
                      <div className="mx-1 hidden h-0.5 w-12 sm:block">
                        <motion.div
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: index < currentStep ? 1 : 0 }}
                          transition={{ duration: 0.3 }}
                          className="h-full bg-accent-cyan origin-left"
                        />
                        <div className="h-full bg-border/30 -mt-0.5" />
                      </div>
                    )}
                  </li>
                ))}
              </ol>

              <div className="mt-1 hidden grid-cols-6 gap-1 text-center text-xs font-medium text-text-muted sm:grid" aria-hidden="true">
                {STEPS.map((step) => <span key={step.id}>{step.title}</span>)}
              </div>
              <p className="mt-2 text-center text-xs font-semibold text-text">
                Étape {currentStep + 1} sur {STEPS.length}, {STEPS[currentStep].title}
              </p>

              {/* Progress Bar */}
              <div
                className="mt-3 h-1 bg-border/20 rounded-full overflow-hidden"
                role="progressbar"
                aria-label="Progression de la configuration"
                aria-valuemin={1}
                aria-valuemax={STEPS.length}
                aria-valuenow={currentStep + 1}
                aria-valuetext={`Étape ${currentStep + 1} sur ${STEPS.length}, ${STEPS[currentStep].title}`}
              >
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
