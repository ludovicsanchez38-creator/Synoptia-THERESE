/**
 * BUG-125 (rouvert) - la page de garde doit montrer une VRAIE alerte pour les
 * tâches en retard. Le backend les renvoyait déjà, mais TodayPanels les rendait
 * en dernier, sans badge ni couleur : visuellement identiques à une tâche due
 * aujourd'hui, noyées derrière factures et prospects.
 *
 * Spec : bloc « Urgences » en tête de « À traiter » (tâches en retard + factures
 * impayées), badge « En retard » + date d'échéance, calcul du retard par DATE
 * CIVILE (le formulaire enregistre des échéances à minuit : comparer les heures
 * marquerait « en retard » une tâche due aujourd'hui dès 00h01).
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TodayPanels } from './TodayPanels';
import type { TodayDashboard } from '../../services/api/dashboard';

const TODAY = '2026-07-10';

function makeData(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: TODAY,
    events: [],
    urgent_tasks: [],
    overdue_invoices: [],
    stale_prospects: [],
    summary: { events_count: 0, tasks_count: 0, invoices_count: 0, prospects_count: 0 },
    ...overrides,
  };
}

function task(id: string, title: string, dueDate: string) {
  return {
    id,
    title,
    status: 'todo',
    priority: 'normal',
    due_date: dueDate,
    project_id: null,
  };
}

describe('BUG-125 - urgences visibles sur la page de garde', () => {
  it('une tâche en retard apparaît dans un bloc Urgences avec badge « En retard » et sa date', () => {
    render(
      <TodayPanels
        data={makeData({
          urgent_tasks: [task('t1', 'Relancer le devis Dupont', '2026-07-05T00:00:00')],
        })}
      />
    );

    expect(screen.getByText('Urgences')).toBeInTheDocument();
    expect(screen.getByText('Relancer le devis Dupont')).toBeInTheDocument();
    expect(screen.getByText('En retard')).toBeInTheDocument();
    expect(screen.getByText('05/07')).toBeInTheDocument();
  });

  it("une tâche due aujourd'hui à minuit n'est PAS marquée en retard (date civile, pas horaire)", () => {
    render(
      <TodayPanels
        data={makeData({
          urgent_tasks: [task('t1', 'Tâche du jour', `${TODAY}T00:00:00`)],
        })}
      />
    );

    expect(screen.getByText('Tâche du jour')).toBeInTheDocument();
    expect(screen.queryByText('En retard')).not.toBeInTheDocument();
    expect(screen.queryByText('Urgences')).not.toBeInTheDocument();
  });

  it('les urgences (tâche en retard + facture impayée) sont rendues AVANT les prospects', () => {
    render(
      <TodayPanels
        data={makeData({
          urgent_tasks: [task('t1', 'Tâche très en retard', '2026-07-01T00:00:00')],
          overdue_invoices: [
            {
              id: 'inv1',
              invoice_number: 'F-2026-042',
              contact_id: 'c1',
              total_ttc: 1200,
              currency: 'EUR',
              due_date: '2026-06-01',
              status: 'sent',
            },
          ],
          stale_prospects: [
            {
              id: 'p1',
              name: 'Prospect Durand',
              company: null,
              stage: 'contact',
              email: null,
              last_interaction: null,
            },
          ],
        })}
      />
    );

    const taskEl = screen.getByText('Tâche très en retard');
    const invoiceEl = screen.getByText(/F-2026-042/);
    const prospectEl = screen.getByText(/Prospect Durand/);
    // Ordre DOM : urgences (tâche en retard, facture) avant le prospect.
    expect(
      taskEl.compareDocumentPosition(prospectEl) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(
      invoiceEl.compareDocumentPosition(prospectEl) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });

  it('signale les tâches urgentes masquées par le top 3 (« +N »)', () => {
    render(
      <TodayPanels
        data={makeData({
          urgent_tasks: [
            task('t1', 'Retard 1', '2026-07-01T00:00:00'),
            task('t2', 'Retard 2', '2026-07-02T00:00:00'),
            task('t3', 'Retard 3', '2026-07-03T00:00:00'),
            task('t4', 'Retard 4', '2026-07-04T00:00:00'),
            task('t5', 'Retard 5', '2026-07-05T00:00:00'),
          ],
        })}
      />
    );

    expect(screen.getByText(/\+2/)).toBeInTheDocument();
    expect(screen.queryByText('Retard 4')).not.toBeInTheDocument();
  });
});
