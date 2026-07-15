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
  isExplicitDevelopmentBuild,
  ...options
}: ResolveRuntimeInterfaceModeOptions): InterfaceMode {
  // Garde-fou pré-bêta : deux preuves indépendantes sont nécessaires. Un
  // `vite build --mode development` pose DEV mais pas le flag de dev explicite.
  if (!isDevelopment || !isExplicitDevelopmentBuild) {
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
    isExplicitDevelopmentBuild: __THERESE_DEV_BUILD__,
    search: window.location.search,
    buildMode: import.meta.env.VITE_THERESE_INTERFACE_MODE,
    storedMode,
  });
}
