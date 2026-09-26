/** B-1621 (décision de Ludo, 26/09) : en démo, supprimer ou anonymiser un
 * contact depuis la liste n'ouvre aucune confirmation (fiche réelle). */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api';

const api = vi.hoisted(() => ({
  listContacts: vi.fn(), deleteContactWithCascade: vi.fn(), anonymizeContact: vi.fn(),
  exportContactRGPD: vi.fn(), renewContactConsent: vi.fn(),
}));
vi.mock('../../services/api/memory', async () => ({
  ...await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory'),
  listContacts: api.listContacts,
}));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  ...api,
  getRGPDStats: vi.fn().mockResolvedValue(null),
}));
// Préserver les vrais hooks, notamment useDialogFocusTrap. Seul le masquage
// des noms est neutralisé, comme dans les fixtures Contacts existantes.
vi.mock('../../hooks', async () => ({
  ...await vi.importActual<typeof import('../../hooks')>('../../hooks'),
  useDemoMask: () => ({ enabled: false, maskContact: (c: Contact) => c, populateMap: vi.fn() }),
}));

import { MemoryPanel } from './MemoryPanel';
import { useDemoStore } from '../../stores/demoStore';

const contact: Contact = {
  id: 'contact-c10', first_name: 'Sophie', last_name: 'Garcia', company: null,
  email: 'sophie@example.fr', phone: null, address: null, notes: null, tags: [],
  stage: 'contact', score: 0, source: null, last_interaction: null, scope: 'global',
  created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

describe('B-1621 : en démo, les gestes destructifs de la liste des contacts sont bloqués', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset());
    api.listContacts.mockResolvedValue([contact]);
    useDemoStore.setState({ enabled: true } as never);
  });
  afterEach(() => {
    cleanup();
    useDemoStore.setState({ enabled: false } as never);
  });

  it('Supprimer n’ouvre pas la confirmation', async () => {
    render(<MemoryPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: 'Supprimer Sophie Garcia' }));
    expect(screen.queryByRole('dialog', { name: 'Supprimer le contact ?' })).toBeNull();
    expect(api.deleteContactWithCascade).not.toHaveBeenCalled();
  });

  it('Anonymiser n’ouvre pas la confirmation', async () => {
    render(<MemoryPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: 'Actions RGPD' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Anonymiser (Art. 17)' }));
    expect(screen.queryByRole('heading', { name: 'Anonymisation RGPD' })).toBeNull();
    expect(api.anonymizeContact).not.toHaveBeenCalled();
  });
});
