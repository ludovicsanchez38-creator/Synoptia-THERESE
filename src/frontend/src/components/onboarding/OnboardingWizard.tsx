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

interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: () => void;
}

const STEPS = [
  { id: 'welcome', title: 'Bienvenue' },
  { id: 'profile', title: 'Profil' },
  { id: 'llm', title: 'LLM' },
  { id: 'security', title: 'Securite' },
  { id: 'workingDir', title: 'Dossier' },
  { id: 'complete', title: 'Termine' },
];

export function OnboardingWizard({ isOpen, onComplete }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = backward

  // Window controls
  const handleMinimize = () => getCurrentWindow().minimize();
  const handleMaximize = () => getCurrentWindow().toggleMaximize();
  const handleClose = () => getCurrentWindow().close();

  // Reset on open
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      setDirection(1);
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
          className="fixed inset-0 z-[100] flex items-center justify-center"
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
            className="absolute top-0 left-0 right-0 h-10 z-[101] flex items-center px-4"
          >
            {/* Window controls (macOS style) */}
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
                        index <= currentStep ? 'text-white' : 'text-text-muted'
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
                  {currentStep === 0 && <WelcomeStep onNext={goNext} />}
                  {currentStep === 1 && <ProfileStep onNext={goNext} onBack={goBack} />}
                  {currentStep === 2 && <LLMStep onNext={goNext} onBack={goBack} />}
                  {currentStep === 3 && <SecurityStep onNext={goNext} onBack={goBack} />}
                  {currentStep === 4 && <WorkingDirStep onNext={goNext} onBack={goBack} />}
                  {currentStep === 5 && <CompleteStep onComplete={handleComplete} onBack={goBack} />}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
