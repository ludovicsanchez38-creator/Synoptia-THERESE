// Onglet Accessibilité (A11Y) - Paramètres THÉRÈSE
// Animations réduites, taille de police, contraste élevé, raccourcis clavier

import { Accessibility } from 'lucide-react';
import { useAccessibilityStore } from '../../stores/accessibilityStore';

export function AccessibilityTab() {
  const {
    reduceMotion,
    setReduceMotion,
    fontSize,
    setFontSize,
    highContrast,
    setHighContrast,
    showKeyboardHints,
    setShowKeyboardHints,
  } = useAccessibilityStore();

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
          <Accessibility className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="font-medium text-text">Accessibilité</h3>
          <p className="text-xs text-text-muted">
            Personnalisez l'interface pour vos besoins
          </p>
        </div>
      </div>

      {/* Réduire les animations (US-A11Y-04) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="reduce-motion" className="text-sm font-medium text-text">
              Réduire les animations
            </label>
            <p className="text-xs text-text-muted">
              Désactive les animations pour les utilisateurs photosensibles
            </p>
          </div>
          <button
            id="reduce-motion"
            role="switch"
            aria-checked={reduceMotion}
            onClick={() => setReduceMotion(!reduceMotion)}
            className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              reduceMotion ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                reduceMotion ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Taille de police */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-text">Taille de police</label>
        <div className="flex gap-2" role="radiogroup" aria-label="Taille de police">
          {(['small', 'medium', 'large'] as const).map((size) => (
            <button
              key={size}
              role="radio"
              aria-checked={fontSize === size}
              onClick={() => setFontSize(size)}
              className={`flex-1 py-2 px-3 rounded-lg border text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan ${
                fontSize === size
                  ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan'
                  : 'bg-background/40 border-border/30 text-text-muted hover:border-border'
              }`}
            >
              {size === 'small' ? 'Petite' : size === 'medium' ? 'Moyenne' : 'Grande'}
            </button>
          ))}
        </div>
      </div>

      {/* Contraste élevé (US-A11Y-03) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="high-contrast" className="text-sm font-medium text-text">
              Contraste élevé
            </label>
            <p className="text-xs text-text-muted">
              Augmente le contraste pour une meilleure lisibilité
            </p>
          </div>
          <button
            id="high-contrast"
            role="switch"
            aria-checked={highContrast}
            onClick={() => setHighContrast(!highContrast)}
            className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              highContrast ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                highContrast ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Raccourcis clavier (US-A11Y-01, US-A11Y-05) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="keyboard-hints" className="text-sm font-medium text-text">
              Afficher les raccourcis clavier
            </label>
            <p className="text-xs text-text-muted">
              Affiche les indications de raccourcis dans l'interface
            </p>
          </div>
          <button
            id="keyboard-hints"
            role="switch"
            aria-checked={showKeyboardHints}
            onClick={() => setShowKeyboardHints(!showKeyboardHints)}
            className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              showKeyboardHints ? 'bg-accent-cyan' : 'bg-border'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                showKeyboardHints ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Boîte d'information */}
      <div className="p-3 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg">
        <div className="flex items-start gap-2">
          <Accessibility className="w-4 h-4 text-accent-cyan mt-0.5" />
          <div className="text-sm text-accent-cyan">
            <p className="font-medium">Raccourcis clavier disponibles</p>
            <ul className="mt-1 text-xs space-y-0.5 text-accent-cyan/80">
              <li>⌘+K : Palette de commandes</li>
              <li>⌘+B : Conversations</li>
              <li>⌘+M : Mémoire</li>
              <li>⌘+D : Board de décision</li>
              <li>Tab / Shift+Tab : Navigation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
