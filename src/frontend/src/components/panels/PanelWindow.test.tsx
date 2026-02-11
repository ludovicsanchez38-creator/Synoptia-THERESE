/**
 * THÉRÈSE v2 - PanelWindow Tests
 *
 * Vérifie que PanelWindow initialise API_BASE avant auth,
 * gère les erreurs, et affiche l'Error Boundary si besoin.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

// Mock API
const mockInitApiBase = vi.fn();
const mockInitializeAuth = vi.fn();
const mockGetEmailAuthStatus = vi.fn();

vi.mock('../../services/api', () => ({
  initApiBase: (...args: unknown[]) => mockInitApiBase(...args),
  initializeAuth: (...args: unknown[]) => mockInitializeAuth(...args),
  getEmailAuthStatus: (...args: unknown[]) => mockGetEmailAuthStatus(...args),
}));

// Mock email store
const mockSetAccounts = vi.fn();
const mockSetCurrentAccount = vi.fn();

vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    setAccounts: mockSetAccounts,
    setCurrentAccount: mockSetCurrentAccount,
    currentAccountId: null,
  }),
}));

// Mock panel components
vi.mock('../email', () => ({
  EmailPanel: ({ standalone }: { standalone?: boolean }) => (
    <div data-testid="email-panel">EmailPanel standalone={String(standalone)}</div>
  ),
}));

vi.mock('../calendar', () => ({
  CalendarPanel: ({ standalone }: { standalone?: boolean }) => (
    <div data-testid="calendar-panel">CalendarPanel standalone={String(standalone)}</div>
  ),
}));

vi.mock('../tasks', () => ({
  TasksPanel: ({ standalone }: { standalone?: boolean }) => (
    <div data-testid="tasks-panel">TasksPanel standalone={String(standalone)}</div>
  ),
}));

vi.mock('../invoices', () => ({
  InvoicesPanel: ({ standalone }: { standalone?: boolean }) => (
    <div data-testid="invoices-panel">InvoicesPanel standalone={String(standalone)}</div>
  ),
}));

vi.mock('../crm', () => ({
  CRMPanel: ({ standalone }: { standalone?: boolean }) => (
    <div data-testid="crm-panel">CRMPanel standalone={String(standalone)}</div>
  ),
}));

vi.mock('../../services/windowManager', () => ({
  // type export only
}));

describe('PanelWindow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockInitApiBase.mockResolvedValue(undefined);
    mockInitializeAuth.mockResolvedValue(undefined);
    mockGetEmailAuthStatus.mockResolvedValue({ accounts: [] });
  });

  it('doit appeler initApiBase AVANT initializeAuth', async () => {
    const callOrder: string[] = [];
    mockInitApiBase.mockImplementation(async () => {
      callOrder.push('initApiBase');
    });
    mockInitializeAuth.mockImplementation(async () => {
      callOrder.push('initializeAuth');
    });

    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="tasks" />);

    await waitFor(() => {
      expect(callOrder).toEqual(['initApiBase', 'initializeAuth']);
    });
  });

  it('doit afficher un spinner pendant le chargement', async () => {
    // Bloquer initApiBase pour maintenir l'état "loading"
    mockInitApiBase.mockImplementation(
      () => new Promise<void>(() => { /* ne résout jamais */ })
    );

    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="email" />);

    expect(screen.getByText('Chargement...')).toBeTruthy();
  });

  it('doit afficher une erreur si initApiBase échoue', async () => {
    mockInitApiBase.mockRejectedValue(new Error('Port indisponible'));

    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="tasks" />);

    await waitFor(() => {
      expect(screen.getByText('Erreur de connexion au backend')).toBeTruthy();
    });
  });

  it('doit afficher une erreur si initializeAuth échoue', async () => {
    mockInitializeAuth.mockRejectedValue(new Error('Token invalide'));

    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="tasks" />);

    await waitFor(() => {
      expect(screen.getByText('Erreur de connexion au backend')).toBeTruthy();
    });
  });

  it('doit rendre le TasksPanel après init réussie', async () => {
    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="tasks" />);

    await waitFor(() => {
      expect(screen.getByTestId('tasks-panel')).toBeTruthy();
    });
  });

  it('doit pré-charger les comptes email pour le panel email', async () => {
    mockGetEmailAuthStatus.mockResolvedValue({
      accounts: [{ id: 'acc-1', email: 'test@test.com' }],
    });

    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="email" />);

    await waitFor(() => {
      expect(mockGetEmailAuthStatus).toHaveBeenCalled();
      expect(mockSetAccounts).toHaveBeenCalledWith([{ id: 'acc-1', email: 'test@test.com' }]);
      expect(mockSetCurrentAccount).toHaveBeenCalledWith('acc-1');
    });
  });

  it('ne doit PAS pré-charger les comptes pour le panel CRM', async () => {
    const { PanelWindow } = await import('./PanelWindow');
    render(<PanelWindow panel="crm" />);

    await waitFor(() => {
      expect(screen.getByTestId('crm-panel')).toBeTruthy();
    });

    expect(mockGetEmailAuthStatus).not.toHaveBeenCalled();
  });
});
