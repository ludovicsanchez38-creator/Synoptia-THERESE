/**
 * Sélecteur réversible de l'interface THÉRÈSE.
 *
 * La 0.40 peut être testée sans remplacer l'interface stable :
 * 1. le paramètre d'URL est prioritaire ;
 * 2. puis la variable de build ;
 * 3. puis le choix bêta conservé localement ;
 * 4. l'interface classique reste la valeur sûre par défaut.
 */

export type InterfaceMode = 'classic' | 'conversation-canvas';

export const INTERFACE_MODE_STORAGE_KEY = 'therese-interface-mode';

interface ResolveInterfaceModeOptions {
  search?: string;
  buildMode?: string;
  storedMode?: string | null;
}

interface ResolveRuntimeInterfaceModeOptions extends ResolveInterfaceModeOptions {
  isDevelopment: boolean;
}

function parseMode(value: string | null | undefined): InterfaceMode | null {
  if (value === 'classic' || value === 'conversation-canvas') {
    return value;
  }
  return null;
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

  return parseMode(buildMode) ?? parseMode(storedMode) ?? 'classic';
}

export function resolveRuntimeInterfaceMode({
  isDevelopment,
  ...options
}: ResolveRuntimeInterfaceModeOptions): InterfaceMode {
  // Garde-fou pré-bêta : aucun build distribuable ne peut ouvrir le prototype.
  if (!isDevelopment) {
    return 'classic';
  }

  return resolveInterfaceMode(options);
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
    search: window.location.search,
    buildMode: import.meta.env.VITE_THERESE_INTERFACE_MODE,
    storedMode,
  });
}
