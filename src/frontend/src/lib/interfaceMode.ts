/**
 * Sélecteur réversible de l'interface THÉRÈSE.
 *
 * En production, le choix utilisateur conservé localement est appliqué s'il
 * est valide. En développement, l'URL et la variable de build permettent aussi
 * de forcer ponctuellement un mode. La coque conversationnelle est le défaut.
 */

export type InterfaceMode = 'classic' | 'conversation-canvas';

export const INTERFACE_MODE_STORAGE_KEY = 'therese-interface-mode';

// Constante injectée par vite.config.ts à partir de la commande Vite, donc
// indépendante de import.meta.env.DEV et du nom de mode passé à `vite build`.
declare const __THERESE_DEV_BUILD__: boolean;

interface ResolveInterfaceModeOptions {
  search?: string;
  buildMode?: string;
  storedMode?: string | null;
}

interface ResolveRuntimeInterfaceModeOptions extends ResolveInterfaceModeOptions {
  isDevelopment: boolean;
  isExplicitDevelopmentBuild: boolean;
}

function parseMode(value: string | null | undefined): InterfaceMode | null {
  if (value === 'classic' || value === 'conversation-canvas') {
    return value;
  }
  return null;
}

export function hasExplicitInterfaceModeChoice(
  storedMode: string | null | undefined,
): boolean {
  return parseMode(storedMode) !== null;
}

export function resolveInterfaceMode({
  search = '',
  buildMode,
  storedMode,
}: ResolveInterfaceModeOptions = {}): InterfaceMode {
  const params = new URLSearchParams(search);
  const requestedMode = parseMode(params.get('interface'));

  if (requestedMode) {
    return requestedMode;
  }

  // Compatibilité avec l'URL utilisée pendant la revue du prototype.
  if (params.get('prototype') === 'conversation-canvas') {
    return 'conversation-canvas';
  }

  return parseMode(buildMode) ?? parseMode(storedMode) ?? 'conversation-canvas';
}

export function resolveRuntimeInterfaceMode({
  isDevelopment,
  isExplicitDevelopmentBuild,
  search,
  buildMode,
  storedMode,
}: ResolveRuntimeInterfaceModeOptions): InterfaceMode {
  // L'URL et la variable Vite sont des outils de développement. Le flag
  // explicite évite qu'un `vite build --mode development` les expose dans un
  // build distribuable, sans bloquer le choix mémorisé par l'utilisateur.
  if (isDevelopment && isExplicitDevelopmentBuild) {
    return resolveInterfaceMode({ search, buildMode, storedMode });
  }

  return parseMode(storedMode) ?? 'conversation-canvas';
}

export function getInterfaceMode(): InterfaceMode {
  let storedMode: string | null = null;

  try {
    storedMode = window.localStorage.getItem(INTERFACE_MODE_STORAGE_KEY);
  } catch {
    // Le stockage peut être indisponible dans certains contextes WebView privés.
  }

  return resolveRuntimeInterfaceMode({
    isDevelopment: import.meta.env.DEV,
    isExplicitDevelopmentBuild: __THERESE_DEV_BUILD__,
    search: window.location.search,
    buildMode: import.meta.env.VITE_THERESE_INTERFACE_MODE,
    storedMode,
  });
}
