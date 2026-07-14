import type { AppView } from '../stores/navigationStore';

const CLASSIC_VIEWS = new Set<AppView>([
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

export type ClassicPanel = 'board' | 'atelier';
export type ClassicAction = 'actions.open' | 'guided.open' | 'prompt-library.open' | 'settings.open';
export type ClassicSettingsTab = 'profile' | 'ai' | 'services' | 'tools' | 'agents' | 'privacy' | 'advanced' | 'about';

const CLASSIC_PANELS = new Set<ClassicPanel>(['board', 'atelier']);
const CLASSIC_ACTIONS = new Set<ClassicAction>(['actions.open', 'guided.open', 'prompt-library.open', 'settings.open']);
const CLASSIC_SETTINGS_TABS = new Set<ClassicSettingsTab>([
  'profile', 'ai', 'services', 'tools', 'agents', 'privacy', 'advanced', 'about',
]);
const CLASSIC_PROMPT_HANDOFF_KEY = 'therese:classic-prompt-handoff';

function prepareClassicUrl(currentHref: string): URL {
  const url = new URL(currentHref);
  url.searchParams.set('interface', 'classic');
  url.searchParams.delete('prototype');
  url.searchParams.delete('scenario');
  url.searchParams.delete('panel');
  url.searchParams.delete('action');
  url.searchParams.delete('prompt');
  url.searchParams.delete('handoff');
  url.searchParams.delete('settings_tab');
  return url;
}

export function resolveClassicView(search: string): AppView | null {
  const value = new URLSearchParams(search).get('view') as AppView | null;
  return value && CLASSIC_VIEWS.has(value) ? value : null;
}

export function resolveClassicPanel(search: string): ClassicPanel | null {
  const value = new URLSearchParams(search).get('panel') as ClassicPanel | null;
  return value && CLASSIC_PANELS.has(value) ? value : null;
}

export function resolveClassicAction(search: string): ClassicAction | null {
  const value = new URLSearchParams(search).get('action') as ClassicAction | null;
  return value && CLASSIC_ACTIONS.has(value) ? value : null;
}

export function resolveClassicPrompt(search: string): string | null {
  const value = new URLSearchParams(search).get('prompt')?.trim();
  return value ? value.slice(0, 4000) : null;
}

export function consumeClassicPrompt(search: string): string | null {
  const params = new URLSearchParams(search);
  if (params.get('handoff') === 'prompt' && typeof window !== 'undefined') {
    try {
      const value = window.sessionStorage.getItem(CLASSIC_PROMPT_HANDOFF_KEY)?.trim();
      window.sessionStorage.removeItem(CLASSIC_PROMPT_HANDOFF_KEY);
      if (value) return value.slice(0, 4000);
    } catch {
      return null;
    }
  }
  // Compatibilité avec les anciens liens locaux. Aucun nouveau lien n'est généré ainsi.
  return resolveClassicPrompt(search);
}

export function resolveClassicSettingsTab(search: string): ClassicSettingsTab | null {
  const value = new URLSearchParams(search).get('settings_tab') as ClassicSettingsTab | null;
  return value && CLASSIC_SETTINGS_TABS.has(value) ? value : null;
}

export function buildClassicViewHref(currentHref: string, view: AppView): string {
  const url = prepareClassicUrl(currentHref);
  url.searchParams.set('view', view);
  return url.toString();
}

export function openClassicView(view: AppView): void {
  window.location.assign(buildClassicViewHref(window.location.href, view));
}

export function buildClassicPanelHref(currentHref: string, panel: ClassicPanel): string {
  const url = prepareClassicUrl(currentHref);
  url.searchParams.set('view', 'chat');
  url.searchParams.set('panel', panel);
  return url.toString();
}

export function openClassicPanel(panel: ClassicPanel): void {
  window.location.assign(buildClassicPanelHref(window.location.href, panel));
}

export function buildClassicActionHref(
  currentHref: string,
  action: ClassicAction,
  options?: { settingsTab?: ClassicSettingsTab },
): string {
  const url = prepareClassicUrl(currentHref);
  url.searchParams.set('view', 'chat');
  url.searchParams.set('action', action);
  if (action === 'settings.open' && options?.settingsTab) {
    url.searchParams.set('settings_tab', options.settingsTab);
  }
  return url.toString();
}

export function openClassicAction(
  action: ClassicAction,
  options?: { settingsTab?: ClassicSettingsTab },
): void {
  window.location.assign(buildClassicActionHref(window.location.href, action, options));
}

export function buildClassicPromptHref(currentHref: string, prompt: string): string {
  const url = prepareClassicUrl(currentHref);
  url.searchParams.set('view', 'chat');
  if (prompt.trim()) url.searchParams.set('handoff', 'prompt');
  return url.toString();
}

export function openClassicPrompt(prompt: string): void {
  const cleanPrompt = prompt.trim().slice(0, 4000);
  if (cleanPrompt) window.sessionStorage.setItem(CLASSIC_PROMPT_HANDOFF_KEY, cleanPrompt);
  window.location.assign(buildClassicPromptHref(window.location.href, cleanPrompt));
}
