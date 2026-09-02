import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { TodayDashboard } from '../../services/api/dashboard';
import { TodayDashboardCard } from './TodayDashboardCard';

function dashboard(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: '2026-07-13',
    events: [],
    urgent_tasks: [],
    due_follow_ups: [],
    overdue_invoices: [],
    stale_prospects: [],
    indisponibles: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
    ...overrides,
  };
}

describe('TodayDashboardCard', () => {
  it('affiche les données réelles et ouvre leur vue classique', () => {
    const onOpenView = vi.fn();
    render(
      <TodayDashboardCard
        resource={{
          status: 'ready',
          error: null,
          data: dashboard({
            events: [{
              id: 'e1', summary: 'Rendez-vous réel', start_datetime: null,
              start_date: '2026-07-13', end_datetime: null, location: null, all_day: true,
              attendees_count: 1, crm_contact_ids: [],
            }],
          }),
        }}
        onRetry={vi.fn()}
        onOpenView={onOpenView}
      />,
    );

    expect(screen.getByText('Rendez-vous réel')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Un point mérite ton attention' })).toBeInTheDocument();
    expect(screen.getByText('1 élément issu de tes données')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Rendez-vous réel'));
    expect(onOpenView).toHaveBeenCalledWith('calendar');
  });

  it('distingue les états erreur et vide', () => {
    const retry = vi.fn();
    const { rerender } = render(
      <TodayDashboardCard
        resource={{ status: 'error', data: null, error: 'Indisponible.' }}
        onRetry={retry}
        onOpenView={vi.fn()}
      />,
    );
    expect(screen.getByTestId('today-dashboard-error')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(retry).toHaveBeenCalledTimes(1);

    rerender(
      <TodayDashboardCard
        resource={{ status: 'ready', data: dashboard(), error: null }}
        onRetry={retry}
        onOpenView={vi.fn()}
      />,
    );
    expect(screen.getByTestId('today-dashboard-empty')).toBeInTheDocument();
  });
});

describe('L’état vide honnête (B1, 0.48)', () => {
  const setup = (has_email: boolean) => ({
    has_calendar: true,
    has_email,
    billing_complete: true, has_invoices: false,
    has_llm_key: true, indisponibles: []
  });

  it('sans compte email : invite à brancher les mails, avec le bouton', () => {
    const onSetupEmail = vi.fn();
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard() }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={setup(false)}
        onSetupEmail={onSetupEmail}
      />,
    );

    expect(
      screen.getByText('Branche tes mails pour que je te prépare la journée'),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Brancher mes mails' }));
    expect(onSetupEmail).toHaveBeenCalledTimes(1);
  });

  it('branché et vide : le message positif réel', () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard() }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={setup(true)}
        onSetupEmail={vi.fn()}
      />,
    );

    expect(screen.getByText('Rien d’urgent pour le moment')).toBeInTheDocument();
    expect(
      screen.queryByText('Branche tes mails pour que je te prépare la journée'),
    ).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Entrée 11 du plan du 28/08 : la mise en route sortait de l'accueil fantôme.
//
// La liste complète de ce qui reste à brancher — clé IA, agenda, messagerie,
// profil de facturation — ne vivait que dans `HomeView`, un second accueil
// derrière le vrai, joignable uniquement par « Voir les autres ». Le brief, lui,
// ne parlait que des mails.
//
// L'inventaire de parité a montré que c'est le SEUL bloc de cet écran qui
// n'existe nulle part ailleurs : le retirer sans le déplacer aurait fait
// perdre la mise en route.
// ---------------------------------------------------------------------------

describe('Entrée 11 : ce qui reste à brancher se voit sur le brief', () => {
  it('annonce toutes les étapes manquantes, pas seulement les mails', () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard() }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={{
          has_llm_key: false,
          has_calendar: false,
          has_email: false,
          billing_complete: false, has_invoices: false,
          indisponibles: [],
        }}
        onSetupEmail={vi.fn()}
      />,
    );

    expect(screen.getByText(/Configurer une clé IA/)).toBeInTheDocument();
    expect(screen.getByText(/Connecter ton agenda/)).toBeInTheDocument();
    expect(screen.getByText(/Compléter le profil de facturation/)).toBeInTheDocument();
  });

  it('tout est branché : la liste disparaît, le brief reprend sa place', () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: dashboard() }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={{
          has_llm_key: true,
          has_calendar: true,
          has_email: true,
          billing_complete: true, has_invoices: false,
          indisponibles: [],
        }}
        onSetupEmail={vi.fn()}
      />,
    );

    expect(screen.queryByText(/Configurer une clé IA/)).toBeNull();
    expect(screen.getByText('Rien d’urgent pour le moment')).toBeInTheDocument();
  });
})

describe('Entrée 11b : plus aucune sortie vers l’accueil fantôme', () => {
  it('le trop-plein se déroule sur place au lieu de changer d’écran', () => {
    const onOpenView = vi.fn();
    const beaucoup = dashboard({
      urgent_tasks: Array.from({ length: 9 }, (_, i) => ({
        id: `t${i}`, title: `Tâche ${i}`, due_date: '2026-07-13', priority: 'high', status: 'todo',
      })) as never,
      summary: { events_count: 0, tasks_count: 9, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
    });
    render(
      <TodayDashboardCard
        resource={{ status: 'ready', error: null, data: beaucoup }}
        onRetry={vi.fn()}
        onOpenView={onOpenView}
        setup={{
          has_llm_key: true,
          has_calendar: true,
          has_email: true,
          billing_complete: true, has_invoices: false,
          indisponibles: [],
        }}
        onSetupEmail={vi.fn()}
      />,
    );

    const deroule = screen.getByRole('button', { name: /autres éléments/ });
    fireEvent.click(deroule);

    // Le trop-plein s'affiche ici : on ne quitte pas le brief pour le lire.
    expect(onOpenView).not.toHaveBeenCalled();
    expect(screen.getByText('Tâche 8')).toBeInTheDocument();
  });

  it('l’erreur ne propose plus d’ouvrir l’accueil depuis l’accueil', () => {
    render(
      <TodayDashboardCard
        resource={{ status: 'error', error: 'panne', data: null }}
        onRetry={vi.fn()}
        onOpenView={vi.fn()}
        setup={{
          has_llm_key: true,
          has_calendar: true,
          has_email: true,
          billing_complete: true, has_invoices: false,
          indisponibles: [],
        }}
        onSetupEmail={vi.fn()}
      />,
    );

    expect(screen.queryByRole('button', { name: 'Ouvrir l’accueil' })).toBeNull();
    // Ce qui reste utile en cas de panne : réessayer.
    expect(screen.getByRole('button', { name: /Réessayer/ })).toBeInTheDocument();
  });
});
