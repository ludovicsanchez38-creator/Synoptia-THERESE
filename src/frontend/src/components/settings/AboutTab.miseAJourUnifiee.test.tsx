import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const check = vi.fn();

vi.mock('@tauri-apps/plugin-updater', () => ({ check }));
vi.mock('../../hooks/useBackend', () => ({
  useBackendStore: (selector: (state: { version: string }) => unknown) => selector({ version: '0.69.0' }),
}));
vi.mock('../../services/api', () => ({ checkHealth: vi.fn() }));

import { AboutTab } from './AboutTab';

describe('AboutTab - BUG-178', () => {
  beforeEach(() => {
    check.mockReset();
    Object.assign(window, { __TAURI__: {} });
  });

  it('vérifie avec le plugin Tauri plutôt que les releases GitHub', async () => {
    check.mockResolvedValue({ available: true, version: '0.70.0' });
    render(<AboutTab />);

    fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));

    await waitFor(() => expect(check).toHaveBeenCalledOnce());
    expect(await screen.findByText('Nouvelle version disponible : 0.70.0')).toBeVisible();
  });
});
