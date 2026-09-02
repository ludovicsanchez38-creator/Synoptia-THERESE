/**
 * B-241 - une vue, un titre.
 *
 * La coque `PrototypeUnifiedViewCanvas` pose déjà le titre de la vue
 * (`<h2 id="prototype-unified-view-title">`), qui sert de nom accessible à la
 * région. Chaque panneau embarqué, conçu à l'origine comme surface autonome,
 * reposait le SIEN juste en dessous : la page Projets ne contenait que deux
 * titres, tous deux « Projets », dans l'ordre H2 puis H1 - un plan qui
 * remonte d'un cran, ce qu'aucun lecteur d'écran ne sait interpréter.
 * Contacts, Devis et factures, Agenda, Pipeline, Email, Tâches et Documents
 * montraient le même doublon.
 *
 * Le test lit le plan de titres RÉEL de chacune des neuf vues embarquées,
 * pas la liste des fichiers : une liste se périme au premier panneau ajouté.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PrototypeUnifiedViewCanvas, viewLabels } from './PrototypeUnifiedViewCanvas';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../services/api');
  return {
    ...actual,
    listProjects: vi.fn().mockResolvedValue([]),
    listContacts: vi.fn().mockResolvedValue([]),
    listInvoices: vi.fn().mockResolvedValue([]),
    listTasks: vi.fn().mockResolvedValue([]),
    listDocuments: vi.fn().mockResolvedValue([]),
    listEmailAccounts: vi.fn().mockResolvedValue([]),
    getEmailAccounts: vi.fn().mockResolvedValue([]),
    listFiles: vi.fn().mockResolvedValue([]),
    getCalendars: vi.fn().mockResolvedValue([]),
    listCalendars: vi.fn().mockResolvedValue([]),
  };
});

interface Titre {
  niveau: number;
  texte: string;
}

function planDesTitres(): Titre[] {
  return Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map((element) => ({
    niveau: Number(element.tagName.slice(1)),
    texte: (element.textContent || '').trim(),
  }));
}

const VUES = Object.keys(viewLabels) as (keyof typeof viewLabels)[];

describe('B-241 - chaque vue embarquée a un plan de titres valide', () => {
  it.each(VUES)('« %s » ne nomme la vue qu’une seule fois', async (vue) => {
    render(<PrototypeUnifiedViewCanvas view={vue} onClose={() => {}} />);
    // La coque monte son panneau en `lazy` : attendre que le corps soit là,
    // sinon le test mesure la coque seule et passe pour une mauvaise raison.
    await waitFor(
      () => expect(screen.queryByText('Chargement…')).not.toBeInTheDocument(),
      { timeout: 4000 },
    );

    const libelle = viewLabels[vue];
    const homonymes = planDesTitres().filter((titre) => titre.texte === libelle);
    expect(
      homonymes,
      `plan de « ${libelle} » : ${JSON.stringify(planDesTitres())}`,
    ).toHaveLength(1);
  });

  it.each(VUES)('« %s » ne remonte jamais d’un cran dans les niveaux', async (vue) => {
    render(<PrototypeUnifiedViewCanvas view={vue} onClose={() => {}} />);
    await waitFor(
      () => expect(screen.queryByText('Chargement…')).not.toBeInTheDocument(),
      { timeout: 4000 },
    );

    const plan = planDesTitres();
    const remontees = plan.filter(
      (titre, index) => index > 0 && titre.niveau < plan[index - 1].niveau,
    );
    expect(remontees, `plan de « ${viewLabels[vue]} » : ${JSON.stringify(plan)}`).toEqual([]);
  });
});
