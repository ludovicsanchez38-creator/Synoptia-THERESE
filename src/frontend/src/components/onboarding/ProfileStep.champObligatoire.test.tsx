/**
 * B-198 — un champ déclaré obligatoire doit le dire autrement qu'en peignant
 * une étoile dans son étiquette.
 *
 * L'étiquette annonce « Nom complet * » et la validation refuse bien la
 * soumission, mais le champ ne portait aucun état : ni `aria-required`, ni
 * `aria-invalid`, ni le moindre lien vers le message de refus. Le message
 * existait pourtant, dans un conteneur `role="alert"` sans `id` — rien ne
 * pouvait le désigner. Qui n'a pas l'image entend « zone de texte », tente,
 * se voit refuser, et ne sait pas quel champ est en cause.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { open } from '@tauri-apps/plugin-dialog';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

const apiMocks = vi.hoisted(() => ({
  setProfile: vi.fn(),
  importClaudeMd: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

describe('ProfileStep — le champ obligatoire annonce son état', () => {
  beforeEach(() => vi.clearAllMocks());

  it('se déclare obligatoire dès le rendu, sans être en faute', () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');

    expect(champ).toHaveAttribute('aria-required', 'true');
    expect(champ).not.toHaveAttribute('aria-invalid');
    expect(champ).not.toHaveAttribute('aria-describedby');
  });

  it('se relie à son message de refus quand il est vide, puis s’en délie à la saisie', () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');

    fireEvent.click(screen.getByTestId('onboarding-next-btn'));

    expect(apiMocks.setProfile).not.toHaveBeenCalled();
    expect(champ).toHaveAttribute('aria-invalid', 'true');

    const designe = champ.getAttribute('aria-describedby');
    expect(designe).toBeTruthy();
    const message = designe ? document.getElementById(designe) : null;
    expect(message).not.toBeNull();
    expect(message).toHaveTextContent('Le nom est obligatoire');

    fireEvent.change(champ, { target: { value: 'Camille Martin' } });

    expect(champ).not.toHaveAttribute('aria-invalid');
    expect(champ).not.toHaveAttribute('aria-describedby');
  });

  it('ne reste pas en faute quand un import remplit le champ', async () => {
    // Le nom peut arriver autrement qu'à la frappe. Sans ce cas, le champ
    // restait `aria-invalid` avec un `aria-describedby` qui désigne un message
    // effacé, jusqu'au clic suivant sur « Continuer ».
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');

    fireEvent.click(screen.getByTestId('onboarding-next-btn'));
    expect(champ).toHaveAttribute('aria-invalid', 'true');

    vi.mocked(open).mockResolvedValueOnce('/Users/camille/THÉRÈSE.md' as never);
    apiMocks.importClaudeMd.mockResolvedValueOnce({ name: 'Camille Martin' });
    await act(async () => {
      fireEvent.click(screen.getByText('Importer THÉRÈSE.md'));
    });

    expect(champ).toHaveValue('Camille Martin');
    expect(champ).not.toHaveAttribute('aria-invalid');
    expect(champ).not.toHaveAttribute('aria-describedby');
  });

  it('ne s’approprie pas le message d’une autre action qui échoue', async () => {
    // Le bandeau est partagé. Si le champ garde son lien pendant qu'un import
    // rate, il désigne un message qui ne parle pas de lui : le lecteur d'écran
    // annonce « Nom complet, invalide, Import impossible ».
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');

    fireEvent.click(screen.getByTestId('onboarding-next-btn'));
    expect(champ).toHaveAttribute('aria-invalid', 'true');

    vi.mocked(open).mockRejectedValueOnce(new Error('Import impossible'));
    await act(async () => {
      fireEvent.click(screen.getByText('Importer THÉRÈSE.md'));
    });

    // Le message d'import est bien affiché : sans cette assertion, le test
    // serait vert parce que rien ne s'est passé.
    expect(screen.getByRole('alert')).toHaveTextContent('Import impossible');
    const designe = champ.getAttribute('aria-describedby');
    const message = designe ? document.getElementById(designe) : null;
    expect(message?.textContent ?? '').not.toMatch(/Import impossible/);
  });

  it('ne s’approprie pas non plus le message d’un enregistrement raté', async () => {
    // Chemin complet : refus initial, nom rempli par import, puis échec de
    // sauvegarde. Le champ est valide, le message parle du serveur.
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const champ = screen.getByLabelText('Nom complet *');

    fireEvent.click(screen.getByTestId('onboarding-next-btn'));
    expect(champ).toHaveAttribute('aria-invalid', 'true');

    vi.mocked(open).mockResolvedValueOnce('/Users/camille/THÉRÈSE.md' as never);
    apiMocks.importClaudeMd.mockResolvedValueOnce({ name: 'Camille Martin' });
    await act(async () => {
      fireEvent.click(screen.getByText('Importer THÉRÈSE.md'));
    });

    apiMocks.setProfile.mockRejectedValueOnce(new Error('Sauvegarde indisponible'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('onboarding-next-btn'));
    });

    expect(screen.getByRole('alert')).toHaveTextContent('Sauvegarde indisponible');
    expect(champ).not.toHaveAttribute('aria-invalid');
    expect(champ).not.toHaveAttribute('aria-describedby');
  });
});
