/**
 * Cycle 6, lecteur #143 (EmailPriorityBadge.tsx) : sans `showText` (le cas
 * de la liste des e-mails), la priorité n'était qu'une pastille colorée
 * `aria-hidden` : rien pour un lecteur d'écran, rien sans la couleur.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EmailPriorityBadge } from './EmailPriorityBadge';

describe('#143 : la priorité a un nom même sans texte visible', () => {
  it.each([['high', 'Urgent'], ['medium', 'Important'], ['low', 'Normal']] as const)(
    '%s : « %s » est présent pour les technologies d’assistance',
    (priority, libelle) => {
      render(<EmailPriorityBadge priority={priority} />);
      const texte = screen.getByText(libelle);
      expect(texte).toHaveClass('sr-only');
    },
  );
});
