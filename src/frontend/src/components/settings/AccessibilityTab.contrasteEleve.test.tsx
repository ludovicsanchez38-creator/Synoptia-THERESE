/** B-608 (Jean, c4) : le contraste élevé impose un fond noir sans le dire, et « Clair » reste coché. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { AccessibilityTab } from './AccessibilityTab';

describe('AccessibilityTab : le contraste élevé annonce son effet sur le thème', () => {
  it('prévient que le fond noir prend le pas sur le thème choisi', () => {
    useAccessibilityStore.setState({ highContrast: true, theme: 'light' });
    render(<AccessibilityTab />);
    expect(screen.getByText(/impose un fond noir/i)).toBeInTheDocument();
  });

  it('ne dit rien quand le contraste élevé est éteint', () => {
    useAccessibilityStore.setState({ highContrast: false, theme: 'light' });
    render(<AccessibilityTab />);
    expect(screen.queryByText(/impose un fond noir/i)).not.toBeInTheDocument();
  });
});
