/**
 * B-1417 (contrôle Chrome de P-134, cycle 13) : revenir dans l'application et
 * cliquer un point du brief ne faisait rien. Le retour de focus relance la
 * lecture (B-317) ; pendant cette relecture, la carte remplaçait ses lignes
 * par des squelettes alors que les données précédentes étaient gardées
 * (B-426). Le bouton appuyé disparaissait avant le relâchement : clic perdu.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { TodayDashboard } from '../../services/api/dashboard';
import { TodayDashboardCard } from './TodayDashboardCard';

const brief: TodayDashboard = {
  date: '2026-09-25', events: [], due_follow_ups: [], overdue_invoices: [], stale_prospects: [], indisponibles: [],
  urgent_tasks: [{ id: 't1', title: 'Rappeler Julien Garnier', status: 'todo', priority: 'medium', due_date: '2026-09-25T08:00:00', project_id: null, contact_id: 'c-julien' }],
  summary: { events_count: 0, tasks_count: 1, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
};

describe('B-1417 : la relecture du brief garde ses lignes', () => {
  it('pendant une relecture, la ligne reste le même nœud et reste cliquable', () => {
    const onOpenItem = vi.fn();
    const { rerender } = render(
      <TodayDashboardCard resource={{ status: 'ready', error: null, data: brief }} onRetry={vi.fn()} onOpenView={vi.fn()} onOpenItem={onOpenItem} />,
    );
    const ligne = screen.getByRole('button', { name: 'Rappeler Julien Garnier' });
    fireEvent.mouseDown(ligne);
    rerender(
      <TodayDashboardCard resource={{ status: 'loading', error: null, data: brief }} onRetry={vi.fn()} onOpenView={vi.fn()} onOpenItem={onOpenItem} />,
    );
    expect(ligne.isConnected).toBe(true);
    expect(screen.queryByText('Je rassemble ta journée…')).toBeNull();
    fireEvent.click(ligne);
    expect(onOpenItem).toHaveBeenCalledWith(expect.objectContaining({ title: 'Rappeler Julien Garnier' }));
  });

  it('un premier chargement sans données garde son indicateur', () => {
    render(<TodayDashboardCard resource={{ status: 'loading', error: null, data: null }} onRetry={vi.fn()} onOpenView={vi.fn()} />);
    expect(screen.getByText('Je rassemble ta journée…')).toBeInTheDocument();
  });
});
