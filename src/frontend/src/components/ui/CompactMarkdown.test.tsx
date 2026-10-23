import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CompactMarkdown } from './CompactMarkdown';

describe('CompactMarkdown', () => {
  it('rend la structure Markdown sans afficher ses marqueurs', () => {
    const { container } = render(
      <CompactMarkdown>{'### Priorités\n\n- **Relancer Camille**\n- Vérifier le devis'}</CompactMarkdown>,
    );

    expect(screen.getByRole('heading', { name: 'Priorités', level: 3 })).toBeInTheDocument();
    expect(screen.getByText('Relancer Camille').tagName).toBe('STRONG');
    expect(container.querySelectorAll('li')).toHaveLength(2);
    expect(container).not.toHaveTextContent('###');
    expect(container).not.toHaveTextContent('**');
  });

  it('neutralise les URL dangereuses, le HTML brut et les images distantes', () => {
    const { container } = render(
      <CompactMarkdown>
        {'[ouvrir](javascript:prompt(1)) <script>contenu indésirable</script> ![pixel](https://tracker.test/x.gif)'}
      </CompactMarkdown>,
    );

    expect(screen.getByText('ouvrir').closest('a')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
    expect(screen.getByText(/Image non affichée : pixel/)).toBeInTheDocument();
  });
});

it('B-1084 : le bloc de code peut défiler et ne reçoit pas le style de puce en ligne', () => {
  const { container } = render(<CompactMarkdown>{'```python\n' + 'chaine = "' + 'x'.repeat(120) + '"\n```\n\n`code court`'}</CompactMarkdown>);
  const pre = container.querySelector('pre');
  expect(pre).toHaveClass('overflow-x-auto', 'max-w-full');
  expect(pre?.querySelector('code')).toHaveClass('block');
  expect(screen.getByText('code court')).toHaveClass('px-1');
});
