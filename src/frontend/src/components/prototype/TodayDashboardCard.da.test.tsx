/**
 * DA « Application affinée », lot 2 : la carte du brief prend la forme de la
 * maquette (`docs/plans/2026-09-10-da-lot2-accueil-design.md`, § 7).
 * Mêmes données, mêmes états, mêmes destinations.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { DashboardTask, TodayDashboard } from '../../services/api/dashboard';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { TodayDashboardCard } from './TodayDashboardCard';

const JOUR = '2026-09-10';
const tache = (id: string, title: string, due_date: string): DashboardTask => ({ id, title, status: 'todo', priority: 'high', due_date, project_id: null });
function dashboard(overrides: Partial<TodayDashboard> = {}): TodayDashboard {
  return {
    date: JOUR, events: [], urgent_tasks: [], due_follow_ups: [], overdue_invoices: [], stale_prospects: [], indisponibles: [],
    summary: { events_count: 0, tasks_count: 0, follow_ups_count: 0, invoices_count: 0, prospects_count: 0 },
    ...overrides,
  };
}
const QUATRE = dashboard({
  urgent_tasks: [tache('t1', 'Relancer Claire Roux pour la facture de juillet', '2026-09-08'), tache('t2', 'Relancer Paul Durand pour le devis', '2026-09-09'), tache('t3', 'Préparer la séance 2', JOUR)],
  overdue_invoices: [{ id: 'f1', invoice_number: 'FACT-2026-002', contact_id: 'c1', contact_name: 'Claire Roux', total_ttc: 1440, currency: 'EUR', due_date: '2026-08-25', status: 'sent' }],
});
const TROIS_SANS_RETARD = dashboard({ urgent_tasks: [tache('a', 'A', JOUR), tache('b', 'B', JOUR), tache('c', 'C', JOUR)] });
const SOLO = dashboard({ events: [{ id: 'e1', summary: 'Casse-croûte', start_datetime: null, start_date: JOUR, end_datetime: null, location: null, all_day: true, attendees_count: 0, crm_contact_ids: [] }] });
const setup = (has_email: boolean, has_calendar = true) => ({ has_calendar, has_email, billing_complete: true, has_invoices: true, has_llm_key: true, indisponibles: [] });

type Ressource = Parameters<typeof TodayDashboardCard>[0]['resource'];
const ready = (data: TodayDashboard): Ressource => ({ status: 'ready', data, error: null });
const afficher = (resource: Ressource, extra: Partial<Parameters<typeof TodayDashboardCard>[0]> = {}) =>
  render(<TodayDashboardCard resource={resource} onRetry={vi.fn()} onOpenView={vi.fn()} {...extra} />);
const carte = () => screen.getByTestId('today-dashboard-card');
const reessayer = () => within(carte()).queryAllByRole('button', { name: 'Réessayer' }).length;

beforeEach(() => { installLocalStorageStub(); });

describe('Lot 2 DA : les lignes du brief sont des Ligne', () => {
  it('une ligne = une commande, grille 2rem 1fr auto, badge en étiquette', () => {
    afficher(ready(QUATRE));
    const ligne = screen.getByRole('button', { name: 'Relancer Claire Roux pour la facture de juillet' });
    const rangee = ligne.closest('[class*="grid-cols-[2rem_1fr_auto]"]') as HTMLElement;
    expect(rangee).not.toBeNull();
    expect(within(rangee).getAllByRole('button')).toHaveLength(1);
    const badge = rangee.querySelector('[data-etiquette]') as HTMLElement;
    expect(badge).not.toBeNull();
    expect(badge.className).toMatch(/text-error/);
    const facture = screen.getByRole('button', { name: /FACT-2026-002/ }).closest('[class*="grid-cols-[2rem_1fr_auto]"]') as HTMLElement;
    expect((facture.querySelector('[data-etiquette]') as HTMLElement).className).toMatch(/text-warning/);
  });
});

describe('Lot 2 DA : le geste principal', () => {
  it('ouvre le premier élément comme sa ligne, avec onOpenItem', () => {
    const onOpenItem = vi.fn();
    afficher(ready(QUATRE), { onOpenItem });
    fireEvent.click(screen.getByRole('button', { name: /^Commencer : Relancer Claire Roux/ }));
    expect(onOpenItem).toHaveBeenCalledTimes(1);
    expect(onOpenItem.mock.calls[0][0]).toMatchObject({ id: expect.stringContaining('t1') });
  });

  it('sans onOpenItem, appelle onOpenView avec la vue de la première ligne', () => {
    const onOpenView = vi.fn();
    afficher(ready(QUATRE), { onOpenView });
    fireEvent.click(screen.getByRole('button', { name: /^Commencer :/ }));
    const [vueGeste] = onOpenView.mock.calls[0];
    fireEvent.click(screen.getByRole('button', { name: 'Relancer Claire Roux pour la facture de juillet' }));
    expect(onOpenView.mock.calls[1][0]).toBe(vueGeste);
  });

  it('n’existe ni sur le vide, ni en chargement', () => {
    const { rerender } = afficher(ready(dashboard()));
    expect(screen.queryByRole('button', { name: /^Commencer :/ })).toBeNull();
    rerender(<TodayDashboardCard resource={{ status: 'loading', data: null, error: null }} onRetry={vi.fn()} onOpenView={vi.fn()} />);
    expect(screen.queryByRole('button', { name: /^Commencer :/ })).toBeNull();
  });
});

describe('Lot 2 DA : la tête', () => {
  it('la section garde son nom accessible par le h2', () => {
    afficher(ready(QUATRE));
    const id = carte().getAttribute('aria-labelledby') as string;
    const titre = document.getElementById(id) as HTMLElement;
    expect(titre.tagName).toBe('H2');
    expect(titre.textContent).toBe('Ton attention aujourd’hui');
  });

  it('la meta compte les éléments et les retards, exactement', () => {
    const { rerender } = afficher(ready(QUATRE));
    expect(screen.getByText('4 éléments, dont 3 en retard')).toBeInTheDocument();
    rerender(<TodayDashboardCard resource={ready(TROIS_SANS_RETARD)} onRetry={vi.fn()} onOpenView={vi.fn()} />);
    expect(screen.getByText('3 éléments')).toBeInTheDocument();
  });

  it('la meta nomme la panne en suffixe', () => {
    afficher(ready({ ...QUATRE, indisponibles: ['calendrier'] }));
    expect(screen.getByText('4 éléments, dont 3 en retard · Agenda indisponible')).toBeInTheDocument();
  });

  it('le vide constaté titre « Rien ne presse aujourd’hui »', () => {
    afficher(ready(dashboard()), { setup: setup(true) });
    expect(screen.getByRole('heading', { level: 2, name: 'Rien ne presse aujourd’hui' })).toBeInTheDocument();
    expect(screen.getByText('Aucune échéance, aucune facture en attente')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Ta journée est dégagée.' })).toBeInTheDocument();
  });
});

describe('Lot 2 DA : le pied « Lu dans »', () => {
  it('une étiquette par source présente, la panne nommée', () => {
    afficher(ready({ ...QUATRE, indisponibles: ['calendrier'] }));
    const pied = screen.getByText('Lu dans').parentElement as HTMLElement;
    const etiquettes = Array.from(pied.querySelectorAll('[data-etiquette]')).map((e) => e.textContent);
    expect(etiquettes).toEqual(['Tâches', 'Factures', 'Agenda indisponible']);
  });

  it('n’existe pas sans aucune source ni panne, existe sur un rendez-vous solo', () => {
    const { rerender } = afficher(ready(dashboard()), { setup: setup(true) });
    expect(screen.queryByText('Lu dans')).toBeNull();
    rerender(<TodayDashboardCard resource={ready(SOLO)} onRetry={vi.fn()} onOpenView={vi.fn()} setup={setup(true)} />);
    expect(screen.getByText('Lu dans')).toBeInTheDocument();
    expect(screen.getByText('Agenda')).toHaveAttribute('data-etiquette');
  });
});

describe('Lot 2 DA : chargement, panne, Réessayer', () => {
  it('le chargement montre des squelettes muets et un statut', () => {
    afficher({ status: 'loading', data: null, error: null });
    expect(within(carte()).getByRole('status')).toHaveTextContent('Je rassemble ta journée…');
    expect(carte().querySelectorAll('[aria-hidden="true"]').length).toBeGreaterThanOrEqual(3);
    expect(reessayer()).toBe(0);
  });

  it('la panne partielle est une alerte qui nomme la source, un seul Réessayer', () => {
    afficher(ready({ ...QUATRE, indisponibles: ['calendrier'] }));
    expect(within(carte()).getByRole('alert')).toHaveTextContent(/Agenda/);
    expect(reessayer()).toBe(1);
  });

  it('exactement un Réessayer sur erreur, vide non constaté et sans messagerie avec panne', () => {
    const { rerender } = afficher({ status: 'error', data: null, error: 'Indisponible.' });
    expect(reessayer()).toBe(1);
    rerender(<TodayDashboardCard resource={ready({ ...dashboard(), indisponibles: ['calendrier'] })} onRetry={vi.fn()} onOpenView={vi.fn()} setup={setup(true)} />);
    expect(screen.getByTestId('today-dashboard-incomplet')).toBeInTheDocument();
    expect(reessayer()).toBe(1);
    rerender(<TodayDashboardCard resource={ready({ ...dashboard(), indisponibles: ['calendrier'] })} onRetry={vi.fn()} onOpenView={vi.fn()} setup={setup(false)} />);
    expect(screen.getByTestId('today-dashboard-setup-email')).toBeInTheDocument();
    expect(within(carte()).getByRole('alert')).toHaveTextContent(/Agenda/);
    expect(reessayer()).toBe(1);
  });

  it('aucun Réessayer ni alerte sur la liste saine, le vide constaté et sans messagerie sans panne', () => {
    const { rerender } = afficher(ready(QUATRE));
    expect(reessayer()).toBe(0);
    rerender(<TodayDashboardCard resource={ready(dashboard())} onRetry={vi.fn()} onOpenView={vi.fn()} setup={setup(true)} />);
    expect(reessayer()).toBe(0);
    expect(within(carte()).queryByRole('alert')).toBeNull();
    rerender(<TodayDashboardCard resource={ready(dashboard())} onRetry={vi.fn()} onOpenView={vi.fn()} setup={setup(false)} />);
    expect(reessayer()).toBe(0);
    expect(screen.getByRole('button', { name: 'Brancher mes mails' })).toBeInTheDocument();
  });

  it('la mise en route passe en h3 sous l’état vide', () => {
    afficher(ready(dashboard()), { setup: setup(true, false) });
    expect(screen.getByRole('heading', { level: 3, name: 'Mise en route' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 2, name: 'Mise en route' })).toBeNull();
  });
});
