/**
 * Ne pas demander de brancher ce qu'on n'a pas pu vérifier.
 *
 * La checklist affiche une étape dès que son indicateur est `false`. Or le
 * backend renvoyait `false` aussi bien pour « pas configuré » que pour « la
 * lecture a échoué » : base verrouillée, migration en cours, profil chiffré
 * illisible. L'écran demandait alors de connecter un agenda DÉJÀ connecté,
 * et l'utilisateur partait réparer ce qui n'était pas cassé.
 *
 * Le backend nomme désormais ce qu'il n'a pas pu vérifier ; l'écran doit
 * s'en servir, sinon la correction ne sert à rien.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { SetupChecklist } from './SetupChecklist';
import type { SetupStatus } from '../../services/api/dashboard';

const TOUT_BRANCHE: SetupStatus = {
  has_calendar: true,
  has_email: true,
  billing_complete: true, has_invoices: false,
  has_llm_key: true,
  indisponibles: [],
};

describe('La mise en route ne réclame pas l’invérifiable', () => {
  it('tout est branché : la checklist disparaît', () => {
    const { container } = render(<SetupChecklist status={TOUT_BRANCHE} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('une étape non faite est proposée', () => {
    render(<SetupChecklist status={{ ...TOUT_BRANCHE, has_calendar: false }} />);

    expect(screen.getByRole('button', { name: /agenda/i })).toBeInTheDocument();
  });

  it('une étape INVÉRIFIABLE n’est pas présentée comme non faite', () => {
    render(
      <SetupChecklist
        status={{ ...TOUT_BRANCHE, has_calendar: false, indisponibles: ['calendrier'] }}
      />,
    );

    expect(screen.queryByRole('button', { name: /Connecter ton agenda/i })).toBeNull();
  });

  it('elle est dite invérifiable, plutôt que passée sous silence', () => {
    render(
      <SetupChecklist
        status={{ ...TOUT_BRANCHE, has_calendar: false, indisponibles: ['calendrier'] }}
      />,
    );

    expect(screen.getByText(/n’a pas pu être vérifié/i)).toBeInTheDocument();
  });
});
