import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SetupChecklist } from './SetupChecklist';

describe('SetupChecklist', () => {
  it('ne rend rien quand tout est branché', () => {
    const { container } = render(
      <SetupChecklist
        status={{ has_calendar: true, has_email: true, billing_complete: true, has_invoices: false, has_llm_key: true, indisponibles: [] }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('affiche seulement les étapes non faites', () => {
    const { queryByText } = render(
      <SetupChecklist
        status={{ has_calendar: false, has_email: true, billing_complete: false, has_invoices: false, has_llm_key: true, indisponibles: [] }}
      />
    );
    expect(queryByText('Connecter ton agenda')).toBeTruthy();
    expect(queryByText('Compléter le profil de facturation')).toBeTruthy();
    expect(queryByText('Connecter ta messagerie')).toBeNull();
  });

  it('US-012 : sans clé LLM, la checklist rappelle cette étape', () => {
    const { queryByText } = render(
      <SetupChecklist
        status={{ has_calendar: true, has_email: true, billing_complete: true, has_invoices: false, has_llm_key: false, indisponibles: [] }}
      />
    );
    expect(queryByText('Configurer une clé IA (ou Ollama)')).toBeTruthy();
  });
});

describe('SetupChecklist (DA lot 2)', () => {
  const status = { has_calendar: false, has_email: true, billing_complete: true, has_invoices: false, has_llm_key: true, indisponibles: [] };
  it('titre en h2 par défaut, en h3 quand une carte porte déjà le h2', () => {
    const { rerender } = render(<SetupChecklist status={status} />);
    expect(screen.getByRole('heading', { level: 2, name: 'Mise en route' })).toBeInTheDocument();
    rerender(<SetupChecklist status={status} niveau="h3" />);
    expect(screen.queryByRole('heading', { level: 2 })).toBeNull();
    expect(screen.getByRole('heading', { level: 3, name: 'Mise en route' })).toBeInTheDocument();
  });
});
