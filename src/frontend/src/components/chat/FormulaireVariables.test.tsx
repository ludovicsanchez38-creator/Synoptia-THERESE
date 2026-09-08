/** P-049 (Sophie sophie-06, B-634 ; accepté par Ludo le 08/09) : renseigner les variables inconnues d'un prompt sans quitter le composeur. Le formulaire ENREGISTRE des variables (createVariable), il ne réécrit jamais le message : ses valeurs restent des données, résolues par le moteur après les directives (revue COCO, finding 1). */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ createVariable: vi.fn() }));
vi.mock('../../services/api/variables', () => api);

import { FormulaireVariables } from './FormulaireVariables';

describe('FormulaireVariables (P-049)', () => {
  beforeEach(() => { api.createVariable.mockReset(); });

  it('liste exactement les inconnues, dans l’ordre, avec un champ nommé chacune', () => {
    render(<FormulaireVariables inconnues={['prenom', 'nom_client']} onEnregistre={vi.fn()} onFermer={vi.fn()} />);
    const champs = screen.getAllByRole('textbox');
    expect(champs).toHaveLength(2);
    expect(screen.getByLabelText('{prenom}')).toBeInTheDocument();
    expect(screen.getByLabelText('{nom_client}')).toBeInTheDocument();
  });

  it('« Enregistrer » crée une variable texte par champ rempli, ignore les vides, puis prévient le parent', async () => {
    api.createVariable.mockResolvedValue({ name: 'prenom', kind: 'text', value: 'Marie', description: null, updated_at: '' });
    const onEnregistre = vi.fn();
    render(<FormulaireVariables inconnues={['prenom', 'nom_client']} onEnregistre={onEnregistre} onFermer={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('{prenom}'), { target: { value: 'Marie' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme variables' }));
    await waitFor(() => expect(api.createVariable).toHaveBeenCalledTimes(1));
    expect(api.createVariable).toHaveBeenCalledWith('prenom', 'text', 'Marie');
    await waitFor(() => expect(onEnregistre).toHaveBeenCalled());
    expect(screen.getByText(/{prenom} enregistrée/)).toBeInTheDocument();
  });

  it('un champ refusé garde sa saisie et montre son erreur, l’autre est enregistré ; rien n’est remplacé automatiquement', async () => {
    api.createVariable
      .mockImplementationOnce(async () => ({ name: 'prenom', kind: 'text', value: 'Marie', description: null, updated_at: '' }))
      .mockImplementationOnce(async () => { throw new Error('Nom réservé (409)'); });
    render(<FormulaireVariables inconnues={['prenom', 'nom_client']} onEnregistre={vi.fn()} onFermer={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('{prenom}'), { target: { value: 'Marie' } });
    fireEvent.change(screen.getByLabelText('{nom_client}'), { target: { value: 'Dupont' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme variables' }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Nom réservé (409)'));
    expect(screen.getByLabelText('{nom_client}')).toHaveValue('Dupont');
    expect(api.createVariable).toHaveBeenCalledTimes(2);
    expect(api.createVariable).not.toHaveBeenCalledWith('nom_client', 'text', 'Dupont', expect.anything());
  });

  it('Échap ferme le formulaire sans remonter au reste de l’application', () => {
    const onFermer = vi.fn();
    const globale = vi.fn();
    window.addEventListener('keydown', globale);
    render(<FormulaireVariables inconnues={['prenom']} onEnregistre={vi.fn()} onFermer={onFermer} />);
    fireEvent.keyDown(screen.getByLabelText('{prenom}'), { key: 'Escape' });
    expect(onFermer).toHaveBeenCalled();
    expect(globale).not.toHaveBeenCalled();
    window.removeEventListener('keydown', globale);
  });
});
