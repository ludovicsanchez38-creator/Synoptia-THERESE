/**
 * Liens profonds de THÉRÈSE.
 *
 * J0b (31/07/2026) : succède à `classicNavigation.ts`, supprimé avec le mode
 * classic. Ce module ne garde que la LECTURE des paramètres d'URL, qui reste
 * utile quelle que soit l'interface (ouvrir l'application sur une vue précise,
 * un panneau, un onglet de réglages). Les fonctions qui poussaient vers
 * l'ancienne interface (`openClassicView`, `buildClassicPanelHref`…) n'ont plus
 * d'objet et disparaissent avec elle.
 *
 * Le prompt transite par `sessionStorage` et jamais par l'URL : décision de
 * confidentialité conservée telle quelle.
 */
import type { AppView } from '../stores/navigationStore';

const VUES = new Set<AppView>([
  'chat',
  'home',
  'memory',
  'crm',
  'email',
  'calendar',
  'tasks',
  'invoices',
  'files',
  'projects',
  'documents',
]);

export type DeepLinkPanel = 'board' | 'atelier';
export type DeepLinkAction = 'actions.open' | 'guided.open' | 'prompt-library.open' | 'settings.open';

/** Onglets des Réglages adressables par lien profond. */
export type SettingsTab =
  | 'profile'
  | 'ai'
  | 'services'
  | 'tools'
  | 'agents'
  | 'privacy'
  | 'advanced'
  | 'about'
  | 'accessibility';

const PANNEAUX = new Set<DeepLinkPanel>(['board', 'atelier']);
const ACTIONS = new Set<DeepLinkAction>([
  'actions.open',
  'guided.open',
  'prompt-library.open',
  'settings.open',
]);
// `accessibility` manquait à l'ancienne liste alors que l'onglet existe :
// il n'était donc pas adressable. Corrigé au passage.
const ONGLETS_REGLAGES = new Set<SettingsTab>([
  'profile', 'ai', 'services', 'tools', 'agents', 'privacy', 'advanced', 'about', 'accessibility',
]);

const CLE_PROMPT = 'therese:prompt-handoff';

export function resolveDeepLinkView(search: string): AppView | null {
  const valeur = new URLSearchParams(search).get('view') as AppView | null;
  return valeur && VUES.has(valeur) ? valeur : null;
}

export function resolveDeepLinkPanel(search: string): DeepLinkPanel | null {
  const valeur = new URLSearchParams(search).get('panel') as DeepLinkPanel | null;
  return valeur && PANNEAUX.has(valeur) ? valeur : null;
}

export function resolveDeepLinkAction(search: string): DeepLinkAction | null {
  const valeur = new URLSearchParams(search).get('action') as DeepLinkAction | null;
  return valeur && ACTIONS.has(valeur) ? valeur : null;
}

export function resolveSettingsTab(search: string): SettingsTab | null {
  const valeur = new URLSearchParams(search).get('settings_tab') as SettingsTab | null;
  return valeur && ONGLETS_REGLAGES.has(valeur) ? valeur : null;
}

/**
 * Retire de l'URL les paramètres de lien profond déjà consommés.
 *
 * Sans ce nettoyage, un lien `?action=settings.open` rouvre les Réglages à
 * CHAQUE rechargement : le paramètre reste dans la barre d'adresse et l'effet
 * de montage le rejoue indéfiniment. L'utilisateur ne peut s'en défaire qu'en
 * éditant l'URL à la main (revue Soso, finding 9).
 *
 * `interface`, qui identifie la coque, n'est pas un lien profond : il reste.
 */
export function nettoyerLiensProfondsConsommes(): void {
  try {
    const url = new URL(window.location.href);
    const consommes = ['view', 'panel', 'action', 'settings_tab', 'handoff', 'prompt'];
    const avant = url.search;
    consommes.forEach((cle) => url.searchParams.delete(cle));
    if (url.search !== avant) {
      window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
    }
  } catch {
    // Une URL exotique ne doit pas empêcher l'application de démarrer.
  }
}

/** Lit le prompt transmis et le consomme (usage unique). */
export function consumeHandoffPrompt(search: string): string | null {
  if (new URLSearchParams(search).get('handoff') !== 'prompt') return null;
  try {
    const valeur = sessionStorage.getItem(CLE_PROMPT);
    sessionStorage.removeItem(CLE_PROMPT);
    return valeur && valeur.trim() ? valeur : null;
  } catch {
    return null;
  }
}
