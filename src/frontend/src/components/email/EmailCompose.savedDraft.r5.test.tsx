import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { EmailCompose } from './EmailCompose';
import { useEmailStore } from '../../stores/emailStore';
import * as api from '../../services/api';
vi.mock('../../services/api', async original => ({ ...(await original<typeof import('../../services/api')>()), createDraft: vi.fn().mockResolvedValue({ id: 'remplacement' }) }));
it('remplace le brouillon sauvegardé seulement au geste de sauvegarde et ne persiste pas son corps', async () => {
  useEmailStore.getState().clearDraft();
  useEmailStore.setState({ currentAccountId: 'compte', editingDraftId: 'brouillon-source', isComposing: true,
    draftRecipients: ['fictif@example.test'], draftSubject: 'Objet fictif', draftBody: 'SENTINELLE_R5_COMPOSEUR' });
  render(<EmailCompose />);
  expect(api.createDraft).not.toHaveBeenCalled();
  expect(localStorage.getItem('therese-email-store') || '').not.toContain('SENTINELLE_R5_COMPOSEUR');
  fireEvent.click(screen.getByRole('button', { name: 'Sauvegarder brouillon' }));
  await waitFor(() => expect(api.createDraft).toHaveBeenCalledWith('compte', expect.objectContaining({ body: 'SENTINELLE_R5_COMPOSEUR' }), undefined, 'brouillon-source'));
});
