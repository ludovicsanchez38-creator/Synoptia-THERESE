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

export function resolveClassicView(search: string): AppView | null {
  const value = new URLSearchParams(search).get('view') as AppView | null;
  return value && CLASSIC_VIEWS.has(value) ? value : null;
}

export function buildClassicViewHref(currentHref: string, view: AppView): string {
  const url = new URL(currentHref);
  url.searchParams.set('interface', 'classic');
  url.searchParams.set('view', view);
  url.searchParams.delete('prototype');
  url.searchParams.delete('scenario');
  return url.toString();
}

export function openClassicView(view: AppView): void {
  window.location.assign(buildClassicViewHref(window.location.href, view));
}
