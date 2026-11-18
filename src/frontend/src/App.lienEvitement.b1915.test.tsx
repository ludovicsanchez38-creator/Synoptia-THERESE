import { render, screen } from '@testing-library/react';
import { Scanner } from '@tailwindcss/oxide';
import { transform } from 'lightningcss';
import { compile } from 'tailwindcss';
import { expect, it, vi } from 'vitest';

vi.mock('./components/onboarding', () => ({ OnboardingWizard: () => null }));
vi.mock('./components/prototype/ConversationCanvasPrototype', () => ({
  ConversationCanvasPrototype: () => <main id="main-content" />,
}));
vi.mock('./components/actions', () => ({ ActionPanel: () => null }));
vi.mock('./components/app/CommonToolConfirmationLayer', () => ({ CommonToolConfirmationLayer: () => null }));
vi.mock('./components/app/ExternalActionConfirmation', () => ({
  PrototypeExternalActionConfirmationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock('./components/ui/Notifications', () => ({ Notifications: () => null }));
vi.mock('./components/ui/UpdateBanner', () => ({ UpdateBanner: () => null }));
vi.mock('./components/ui/SidecarStatusBanner', () => ({ SidecarStatusBanner: () => null }));
vi.mock('./hooks/useHealthCheck', () => ({ useHealthCheck: vi.fn() }));
vi.mock('./lib/capacites/generation', () => ({ controlerGenerationAuDemarrage: vi.fn().mockResolvedValue(undefined) }));
vi.mock('./lib/profileStorageIsolation', () => ({ isolateDataProfilePersistence: vi.fn(() => 'unchanged') }));
vi.mock('./lib/consentSync', () => ({ synchroniserConsentements: vi.fn().mockResolvedValue(undefined) }));
vi.mock('./services/api', async (importOriginal) => ({
  ...await importOriginal<typeof import('./services/api')>(),
  initializeAuth: vi.fn().mockResolvedValue(undefined),
  getStats: vi.fn().mockResolvedValue({ data_dir: '/profils/test' }),
  getOnboardingStatus: vi.fn().mockResolvedValue({ completed: true }),
}));

import App from './App';

it('B-1915 : le lien focalisé est au-dessus du chrome avec le CSS produit par Tailwind', async () => {
  render(<App />);
  const lien = await screen.findByRole('link', { name: 'Aller au contenu principal' });
  const scanner = new Scanner({ sources: [{ base: process.cwd(), pattern: 'src/**/*.{ts,tsx}', negated: false }] });
  const classesProduites = new Set(scanner.scan());
  const classesDuLien = [...lien.classList].filter((classe) => classe.includes('z-') && classesProduites.has(classe));
  const tailwind = await compile('@tailwind utilities;');
  const css = tailwind.build(classesDuLien);
  const style = document.createElement('style');
  style.textContent = transform({ filename: 'test.css', code: Buffer.from(css), targets: { chrome: 90 << 16 } }).code.toString();
  document.head.append(style);
  try {
    lien.focus();
    expect(lien).toHaveFocus();
    expect(Number(getComputedStyle(lien).zIndex)).toBeGreaterThanOrEqual(50);
    expect(lien).toHaveAttribute('href', '#main-content');
  } finally {
    style.remove();
  }
});
