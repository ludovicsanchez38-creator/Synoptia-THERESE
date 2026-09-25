/**
 * B-1413 (relevé par la RFC P-121, reproduit ici) : la modale prenait la date
 * du jour par `toISOString()`, en UTC. Un devis créé à 0 h 30 à Paris portait
 * la date de la veille (et une échéance décalée d'autant). Le panneau Facturer
 * lisait déjà la date civile locale ; la modale fait de même.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    listContacts: vi.fn().mockResolvedValue([]),
    getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  };
});

import { InvoiceForm } from './InvoiceForm';

const TZ_INITIAL = process.env.TZ;
afterEach(() => {
  vi.useRealTimers();
  process.env.TZ = TZ_INITIAL;
});

describe('B-1413 : la date du jour est la date civile locale', () => {
  it('à 0 h 30 à Paris, le 26 septembre (pas le 25)', () => {
    process.env.TZ = 'Europe/Paris';
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-09-25T22:30:00Z')); // 26/09 à 0 h 30 à Paris

    render(<InvoiceForm invoice={null} onClose={vi.fn()} onSave={vi.fn()} />);

    expect((screen.getByLabelText(/Date d.émission/) as HTMLInputElement).value).toBe('2026-09-26');
    expect((screen.getByLabelText(/Date d.échéance/) as HTMLInputElement).value).toBe('2026-10-26');
  });
});
