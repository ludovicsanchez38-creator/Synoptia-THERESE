import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { MemoryProfileBranch } from '../../components/memory/MemoryProfileBranch';
vi.mock('../../components/settings/SettingsModal', () => ({ SettingsModal: () => null }));
it('B-1093 : le profil emploie le bouton secondaire commun', () => {
  render(<MemoryProfileBranch />);
  expect(screen.getByRole('button', { name: 'Modifier mon profil et mes consignes' })).toHaveClass('px-4', 'hover:bg-surface-2', 'disabled:opacity-50');
});
