import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { ExplicationDuScore } from '../../components/crm/ExplicationDuScore';
it('B-1091 : aria-controls référence un contenu présent', () => {
  render(<ExplicationDuScore />);
  const bouton = screen.getByRole('button', { name: 'Expliquer le score' });
  expect(bouton).not.toHaveAttribute('aria-controls');
  fireEvent.click(bouton);
  expect(document.getElementById(bouton.getAttribute('aria-controls')!)).not.toBeNull();
  fireEvent.click(bouton);
  expect(bouton).not.toHaveAttribute('aria-controls');
});

it.each(['premier', 'deuxième', 'troisième', 'quatrième', 'cinquième', 'sixième', 'septième', 'huitième', 'neuvième', 'dixième'])('Rejeu B-1091 : %s bascule', () => {
  render(<ExplicationDuScore />);
  const bouton = screen.getByRole('button', { name: 'Expliquer le score' });
  fireEvent.click(bouton);
  expect(document.getElementById(bouton.getAttribute('aria-controls')!)).toBeInTheDocument();
  fireEvent.click(bouton);
  expect(bouton).not.toHaveAttribute('aria-controls');
});
