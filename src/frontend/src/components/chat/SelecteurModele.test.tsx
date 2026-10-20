import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { SelecteurModele } from './SelecteurModele';

it('parcourt les modèles au clavier et valide seulement avec Entrée', () => {
  const choisir = vi.fn();
  render(<SelecteurModele modeles={['a', 'b', 'c']} modele="a" onChange={choisir} />);
  fireEvent.click(screen.getByRole('button', { name: 'Modèle de conversation' }));
  const liste = screen.getByRole('listbox');
  fireEvent.keyDown(liste, { key: 'ArrowDown' });
  fireEvent.change(liste, { target: { value: 'c' } });
  expect(choisir).not.toHaveBeenCalled();
  expect(screen.getByRole('listbox')).toBeInTheDocument();
  fireEvent.keyDown(liste, { key: 'Enter' });
  expect(choisir).toHaveBeenCalledWith('c');
  expect(screen.queryByRole('listbox')).toBeNull();
});

it('ferme la liste quand une autre surface prend le focus', () => {
  render(<><SelecteurModele modeles={['a', 'b']} modele="a" onChange={vi.fn()} /><button>Autre surface</button></>);
  fireEvent.click(screen.getByRole('button', { name: 'Modèle de conversation' }));
  const autre = screen.getByRole('button', { name: 'Autre surface' });
  fireEvent.blur(screen.getByRole('listbox'), { relatedTarget: autre });
  expect(screen.queryByRole('listbox')).toBeNull();
});
