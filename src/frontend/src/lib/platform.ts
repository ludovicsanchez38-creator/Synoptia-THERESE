/**
 * Détection de plateforme desktop centralisée (revue 0.40).
 *
 * Deux implémentations divergentes coexistaient (WindowControls sans détection,
 * OnboardingWizard avec sa propre regex) : celle-ci fait foi partout.
 *
 * navigator.platform est déprécié mais reste le seul signal fiable dans les
 * webviews Tauri (WKWebView macOS, WebView2 Windows, WebKitGTK Linux) :
 * userAgentData n'y est pas exposé de façon homogène.
 */
export function isMacPlatform(): boolean {
  return typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);
}
