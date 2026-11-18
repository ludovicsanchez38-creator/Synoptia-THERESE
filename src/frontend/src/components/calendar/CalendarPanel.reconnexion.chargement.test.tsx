import { vi } from 'vitest';

// Rejoue le scénario existant lorsque l'ouverture du navigateur prend du temps.
vi.mock('@tauri-apps/plugin-shell', () => ({
  open: vi.fn(() => new Promise<void>(resolve => setTimeout(resolve, 100))),
}));

await import('./CalendarPanel.reconnexion.test');
