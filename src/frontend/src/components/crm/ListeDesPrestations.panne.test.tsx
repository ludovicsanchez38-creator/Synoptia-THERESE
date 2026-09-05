/**
 * Une panne du chargement des prestations se dit à l'écran (05/09/2026).
 *
 * Trouvée par la CI du cycle 3 : `recharger` avait un `finally` mais pas de
 * `catch`, la promesse rejetée remontait jusqu'au webview sans rien afficher,
 * et la fiche restait sur « Aucune prestation » comme si la panne était un vide
 * (même famille que B-527 pour les activités).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/prestations', async (importOriginal) => {
  const vrai = await importOriginal<typeof import('../../services/api/prestations')>();
  return {
    ...vrai,
    listerLesPrestations: () => Promise.reject(new Error('Impossible de contacter le serveur')),
  };
});

const { ListeDesPrestations } = await import('./ListeDesPrestations');

describe('ListeDesPrestations : panne du chargement', () => {
  it("affiche une alerte au lieu d'un faux « Aucune prestation »", async () => {
    render(<ListeDesPrestations contactId="c1" />);

    const alerte = await screen.findByRole('alert');
    expect(alerte).toHaveTextContent(/Impossible de charger les prestations/);
    expect(screen.queryByText(/Aucune prestation enregistrée/)).not.toBeInTheDocument();
  });
});
