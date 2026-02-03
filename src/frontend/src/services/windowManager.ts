/**
 * THERESE v2 - Window Manager
 *
 * Gestion des fenetres separees pour les panels (Email, Calendrier, Taches, Factures, CRM).
 * Utilise WebviewWindow de Tauri 2.0 pour creer des fenetres natives macOS.
 */

import { WebviewWindow } from '@tauri-apps/api/webviewWindow';

export type PanelType = 'email' | 'calendar' | 'tasks' | 'invoices' | 'crm';

// Runtime whitelist for panel names (SEC-018)
// TypeScript types are erased at runtime - this ensures validation at runtime too
const VALID_PANELS: ReadonlySet<string> = new Set<PanelType>([
  'email', 'calendar', 'tasks', 'invoices', 'crm',
]);

export function isValidPanel(value: string): value is PanelType {
  return VALID_PANELS.has(value);
}

interface PanelConfig {
  title: string;
  width: number;
  height: number;
  minWidth: number;
  minHeight: number;
}

const PANEL_CONFIGS: Record<PanelType, PanelConfig> = {
  email: {
    title: 'THERESE - Email',
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 500,
  },
  calendar: {
    title: 'THERESE - Calendrier',
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 500,
  },
  tasks: {
    title: 'THERESE - Taches',
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 500,
  },
  invoices: {
    title: 'THERESE - Factures',
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 500,
  },
  crm: {
    title: 'THERESE - CRM',
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
  },
};

// Tracking des fenetres ouvertes
const openWindows = new Map<PanelType, WebviewWindow>();

/**
 * Ouvre un panel dans une fenetre macOS separee.
 * Si la fenetre existe deja, elle prend le focus.
 */
export async function openPanelWindow(panel: PanelType): Promise<void> {
  // Runtime whitelist check (SEC-018) - defense against dynamic values
  if (!isValidPanel(panel)) {
    console.error(`[Security] Invalid panel name rejected: ${panel}`);
    return;
  }

  // Verifier si la fenetre existe deja
  const existing = openWindows.get(panel);
  if (existing) {
    try {
      // Tenter de focus la fenetre existante
      await existing.setFocus();
      return;
    } catch {
      // La fenetre a ete fermee, on la retire du tracking
      openWindows.delete(panel);
    }
  }

  const config = PANEL_CONFIGS[panel];
  const label = `panel-${panel}`;

  const webview = new WebviewWindow(label, {
    url: `index.html?panel=${panel}`,
    title: config.title,
    width: config.width,
    height: config.height,
    minWidth: config.minWidth,
    minHeight: config.minHeight,
    center: true,
    resizable: true,
    decorations: true,
    shadow: true,
    focus: true,
  });

  // Tracker la fenetre
  openWindows.set(panel, webview);

  // Nettoyage APRES destruction - on n'utilise PAS onCloseRequested
  // car il bloque la fermeture native (croix rouge macOS).
  // once('tauri://destroyed') se declenche apres que la fenetre est detruite.
  webview.once('tauri://destroyed', () => {
    openWindows.delete(panel);
  });
}

/**
 * Verifie si un panel est ouvert dans une fenetre separee.
 */
export function isPanelWindowOpen(panel: PanelType): boolean {
  return openWindows.has(panel);
}

/**
 * Ferme la fenetre d'un panel.
 */
export async function closePanelWindow(panel: PanelType): Promise<void> {
  const win = openWindows.get(panel);
  if (win) {
    openWindows.delete(panel);
    try {
      await win.destroy();
    } catch {
      // Ignore si deja fermee
    }
  }
}
