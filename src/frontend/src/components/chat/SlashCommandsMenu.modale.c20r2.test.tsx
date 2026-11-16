import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { CloudConsentDialog } from '../shared/CloudConsentDialog';
import { SlashCommandsMenu } from './SlashCommandsMenu';

it.each(['Tab', 'Enter', 'ArrowDown', 'ArrowUp'])('R2.2 : l’écouteur global laisse %s à la modale', key => {
  HTMLElement.prototype.scrollIntoView = vi.fn();
  const onSelect = vi.fn();
  const onIndexChange = vi.fn();
  const menu = <SlashCommandsMenu isOpen query="/" selectedIndex={0}
    onSelect={onSelect} onClose={vi.fn()} onIndexChange={onIndexChange} />;
  const { rerender } = render(<>{menu}<CloudConsentDialog title="Accord fictif" testId="accord"
    dataCategories={['message']} onCancel={vi.fn()} onConfirm={vi.fn()} /></>);
  fireEvent.keyDown(screen.getByRole('button', { name: 'Annuler' }), { key });
  expect(onSelect).not.toHaveBeenCalled();
  expect(onIndexChange).not.toHaveBeenCalled();
  // L'écouteur reste opérationnel une fois la modale fermée.
  rerender(menu);
  fireEvent.keyDown(window, { key: 'Tab' });
  expect(onSelect).toHaveBeenCalledTimes(1);
});
