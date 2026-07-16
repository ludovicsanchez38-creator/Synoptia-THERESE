import { useState } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { handleRovingFocus } from './rovingFocus';

function RadioHarness() {
  const [selected, setSelected] = useState('premier');
  return (
    <div role="radiogroup" aria-label="Choix de test">
      {['premier', 'deuxième', 'troisième'].map((value) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={selected === value}
          tabIndex={selected === value ? 0 : -1}
          onClick={() => setSelected(value)}
          onKeyDown={(event) => handleRovingFocus(event, '[role="radio"]', 'horizontal')}
        >
          {value}
        </button>
      ))}
    </div>
  );
}

describe('handleRovingFocus', () => {
  it('déplace le focus, active le choix et boucle avec les flèches', () => {
    render(<RadioHarness />);
    const first = screen.getByRole('radio', { name: 'premier' });
    const second = screen.getByRole('radio', { name: 'deuxième' });
    const third = screen.getByRole('radio', { name: 'troisième' });

    first.focus();
    fireEvent.keyDown(first, { key: 'ArrowRight' });
    expect(second).toHaveFocus();
    expect(second).toHaveAttribute('aria-checked', 'true');
    expect(second).toHaveAttribute('tabindex', '0');

    fireEvent.keyDown(second, { key: 'Home' });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: 'ArrowLeft' });
    expect(third).toHaveFocus();
    expect(third).toHaveAttribute('aria-checked', 'true');
  });
});
