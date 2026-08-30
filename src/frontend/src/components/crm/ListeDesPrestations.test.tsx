/**
 * Les prestations d'une personne, à l'écran (tranche C du 29/08).
 *
 * Une liste, pas un Kanban : le Kanban des contacts a sept colonnes qui ne
 * parlent que de vente, alors que Ludo suit aussi ce qui est en cours.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const prestations: unknown[] = [];
const creees: unknown[] = [];
const phasesChangees: unknown[] = [];

vi.mock('../../services/api/prestations', async (importOriginal) => {
  const vrai = await importOriginal<typeof import('../../services/api/prestations')>();
  return {
    ...vrai,
    listerLesPrestations: () => Promise.resolve(prestations),
    creerUnePrestation: (c: unknown) => {
      creees.push(c);
      return Promise.resolve({ ...(c as object), id: 'p-neuve' });
    },
    changerLaPhase: (id: string, phase: string) => {
      phasesChangees.push({ id, phase });
      return Promise.resolve({ id, phase });
    },
  };
});

const { ListeDesPrestations } = await import('./ListeDesPrestations');

function servir(...p: unknown[]) {
  prestations.length = 0;
  prestations.push(...p);
}

const FORGER = {
  id: 'p1', contact_id: 'c1', intitule: 'FORGER', montant_ht: 490,
  phase: 'proposition', created_at: '2026-08-01T10:00:00Z', updated_at: '2026-08-01T10:00:00Z',
};

describe('Les prestations à l’écran', () => {
  it("montre l'intitulé, le montant et la phase en toutes lettres", async () => {
    servir(FORGER);
    render(<ListeDesPrestations contactId="c1" />);

    expect(await screen.findByText('FORGER')).toBeInTheDocument();
    expect(screen.getByText(/490/)).toBeInTheDocument();
    // Pas une pastille de couleur : le mot, et un contrôle nommé. C'est la
    // plainte de la campagne (« des petits dessins sans nom, je n'ose pas »).
    const phase = screen.getByLabelText(/phase de FORGER/i) as HTMLSelectElement;
    expect(phase.value).toBe('proposition');
    expect(phase.options[phase.selectedIndex].text).toBe('Proposition envoyée');
  });

  it("n'invente pas un montant quand il n'y en a pas", async () => {
    servir({ ...FORGER, montant_ht: null });
    render(<ListeDesPrestations contactId="c1" />);

    await screen.findByText('FORGER');
    expect(screen.queryByText(/0[,.]00/)).not.toBeInTheDocument();
    expect(screen.getByText(/montant non renseign/i)).toBeInTheDocument();
  });

  it('dit clairement quand il n’y a rien, sans prétendre le contraire', async () => {
    servir();
    render(<ListeDesPrestations contactId="c1" />);

    expect(await screen.findByText(/aucune prestation/i)).toBeInTheDocument();
  });

  it('laisse poser une prestation à la main', async () => {
    servir();
    creees.length = 0;
    render(<ListeDesPrestations contactId="c1" />);

    fireEvent.change(await screen.findByLabelText(/intitulé/i), {
      target: { value: 'PROPULSER' },
    });
    fireEvent.change(screen.getByLabelText(/où ça en est/i), {
      target: { value: 'en_cours' },
    });
    fireEvent.click(screen.getByRole('button', { name: /ajouter/i }));

    await waitFor(() => expect(creees).toHaveLength(1));
    expect((creees[0] as { intitule: string }).intitule).toBe('PROPULSER');
  });

  it("envoie TOUJOURS une phase : sans elle l'API refuse la creation", async () => {
    // Défaut livré en 0.59.0 : l'API a rendu la phase obligatoire, l'écran a
    // continué d'envoyer {contact_id, intitule, montant_ht}. Le bouton
    // « Ajouter » ne créait plus rien, et ce test — qui mockait l'appel sans
    // regarder le corps — restait vert.
    servir();
    creees.length = 0;
    render(<ListeDesPrestations contactId="c1" />);

    fireEvent.change(await screen.findByLabelText(/intitulé/i), {
      target: { value: 'Depannage fuite' },
    });
    fireEvent.click(screen.getByRole('button', { name: /ajouter/i }));

    await waitFor(() => expect(creees).toHaveLength(1));
    const corps = creees[0] as { phase?: string };
    expect(corps.phase).toBeTruthy();
    expect(['piste', 'proposition', 'gagne', 'perdue', 'en_cours', 'terminee'])
      .toContain(corps.phase);
  });

  it("ne choisit pas la phase en silence : elle est visible avant d'ajouter", async () => {
    servir();
    render(<ListeDesPrestations contactId="c1" />);

    // Le choix est à l'écran, nommé, pas caché dans le code.
    expect(await screen.findByLabelText(/où ça en est/i)).toBeInTheDocument();
  });

  it('refuse d’envoyer un intitulé vide', async () => {
    servir();
    creees.length = 0;
    render(<ListeDesPrestations contactId="c1" />);

    fireEvent.click(await screen.findByRole('button', { name: /ajouter/i }));

    await waitFor(() => expect(creees).toHaveLength(0));
  });
});
