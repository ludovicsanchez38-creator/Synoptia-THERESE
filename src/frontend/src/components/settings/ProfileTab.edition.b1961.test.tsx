import { fireEvent, render, screen, within } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { ProfileTab, type ProfileFormData } from './ProfileTab';
import * as api from '../../services/api';

vi.mock('../../services/api', async (original) => ({
  ...(await original<typeof import('../../services/api')>()),
  getThereseMd: vi.fn().mockResolvedValue({ content: '# Profil de test', path: '/profil-fictif/THERESE.md' }),
  saveThereseMd: vi.fn().mockResolvedValue({}),
}));

const vide: ProfileFormData = {
  name: '', nickname: '', company: '', role: '', email: '', location: '', address: '',
  siren: '', tva_intra: '', siret: '', code_ape: '', nda: '', context: '', regime_tva: 'normal',
};

it('B-1961 : le dialogue annonce la modification et sauvegarde le texte saisi', async () => {
  render(<ProfileTab profileForm={vide} setProfileForm={vi.fn()} profile={null}
    saving={false} setError={vi.fn()} onSave={vi.fn()} onImport={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Voir THERESE.md' }));
  const champ = await screen.findByRole('textbox', { name: 'Contenu du profil THERESE.md' });
  const dialogue = screen.getByRole('dialog');
  expect(dialogue).toHaveAccessibleName('Modifier THERESE.md');
  fireEvent.change(champ, { target: { value: '# Profil modifié' } });
  fireEvent.click(within(dialogue).getByRole('button', { name: 'Sauvegarder' }));
  expect(await within(dialogue).findByRole('status')).toHaveTextContent('Sauvegardé');
  expect(api.saveThereseMd).toHaveBeenCalledWith('# Profil modifié');
  fireEvent.click(within(dialogue).getByRole('button', { name: 'Fermer l’éditeur THERESE.md' }));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});
