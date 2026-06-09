import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { SetupChecklist } from './SetupChecklist';

describe('SetupChecklist', () => {
  it('ne rend rien quand tout est branché', () => {
    const { container } = render(
      <SetupChecklist status={{ has_calendar: true, has_email: true, billing_complete: true }} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('affiche seulement les étapes non faites', () => {
    const { queryByText } = render(
      <SetupChecklist status={{ has_calendar: false, has_email: true, billing_complete: false }} />
    );
    expect(queryByText('Connecter votre agenda')).toBeTruthy();
    expect(queryByText('Compléter le profil de facturation')).toBeTruthy();
    expect(queryByText('Connecter votre messagerie')).toBeNull();
  });
});
