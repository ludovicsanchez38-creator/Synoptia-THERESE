/**
 * Cycle 6, lecteurs #187 et #188 (LimitsTab.tsx).
 * - #187 : un échec de lecture ou d'enregistrement ne faisait qu'un
 *   console.error ; l'onglet restait vide, ou gardait des valeurs non
 *   enregistrées, sans un mot.
 * - #188 : un budget mensuel à 0 s'affichait « 50 » (repli `|| 50`) pendant
 *   que la barre divisait par zéro.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getEscalationStatus: vi.fn(),
  getTokenLimits: vi.fn(),
  setTokenLimits: vi.fn(),
}));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...api };
});

import { LimitsTab } from './LimitsTab';

const limites = {
  max_input_tokens: 1000, max_output_tokens: 1000, daily_input_limit: 100000,
  daily_output_limit: 100000, monthly_budget_eur: 50, warn_at_percentage: 80,
};
const statut = (cout: number, budget: number) => ({
  daily_usage: { date: '2026-09-10', input_tokens: 1000, output_tokens: 500, total_tokens: 1500, cost_eur: 0.1, input_limit: 100000 },
  monthly_usage: { month: '2026-09', input_tokens: 10000, output_tokens: 5000, total_tokens: 15000, cost_eur: cout, budget_eur: budget },
  limits: limites,
  recent_history_count: 0,
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe('#187 : les pannes de l’onglet Limites sont dites', () => {
  it('une lecture en panne affiche une alerte avec reprise, et la reprise relit', async () => {
    api.getEscalationStatus.mockRejectedValueOnce(new Error('boom')).mockResolvedValue(statut(1, 50));
    api.getTokenLimits.mockResolvedValue(limites);
    render(<LimitsTab />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/n’ont pas pu être lues/);
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
    expect(await screen.findByText('Limites configurables')).toBeInTheDocument();
  });

  it('un enregistrement en panne affiche une alerte', async () => {
    api.getEscalationStatus.mockResolvedValue(statut(1, 50));
    api.getTokenLimits.mockResolvedValue(limites);
    api.setTokenLimits.mockRejectedValue(new Error('boom'));
    render(<LimitsTab />);
    fireEvent.click(await screen.findByRole('button', { name: 'Sauver' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/n’ont pas pu être enregistrées/);
  });
});

describe('#188 : un budget à zéro reste un zéro', () => {
  it('affiche 0 et une barre à 0 %, ni 50 ni NaN', async () => {
    api.getEscalationStatus.mockResolvedValue(statut(3, 0));
    api.getTokenLimits.mockResolvedValue({ ...limites, monthly_budget_eur: 0 });
    render(<LimitsTab />);
    // Le libellé de la barre (pas celui du champ « Budget mensuel ($) » plus bas).
    await screen.findByText('Limites configurables');
    const libelle = await screen.findByText(/Budget mensuel \(0 /);
    expect(libelle.parentElement).toHaveTextContent(/\b0%/);
    expect(libelle.parentElement).not.toHaveTextContent(/NaN|Infinity|100%/);
  });
});
