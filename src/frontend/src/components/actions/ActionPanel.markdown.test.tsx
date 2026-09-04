import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/actions', () => ({
  fetchActions: vi.fn().mockResolvedValue([]),
  runAction: vi.fn(),
  fetchTask: vi.fn(),
  cancelTask: vi.fn(),
}));

import { useActionsStore } from '../../stores/actionsStore';
import { ActionPanel } from './ActionPanel';

describe('B-321 : résultat d’une action', () => {
  beforeEach(() => {
    useActionsStore.setState({
      agents: [{
        id: 'relance-clients', name: 'Relance clients', description: '', icon: 'UserCheck',
        category: 'commercial', steps_count: 1, tools: ['crm'], params: [],
      }],
      selectedAgent: null,
      isPanelOpen: true,
      activeTask: {
        task_id: 'task-b321', agent_id: 'relance-clients', agent_name: 'Relance clients',
        status: 'completed', params: {}, result: '', progress: 1,
        created_at: '2026-09-04T08:00:00Z', started_at: '2026-09-04T08:00:00Z',
        completed_at: '2026-09-04T08:01:00Z', error: null,
        steps: [{
          step_id: 'scan', label: 'Scan CRM', status: 'completed',
          content: '### Priorités\n\n- **Camille**\n- Nora',
          started_at: '2026-09-04T08:00:00Z', completed_at: '2026-09-04T08:01:00Z',
          error: null,
        }],
      },
    });
  });

  it('affiche titres, listes et gras comme du contenu structuré', () => {
    const { container } = render(<ActionPanel />);

    expect(screen.getByRole('heading', { name: 'Priorités' })).toBeInTheDocument();
    expect(screen.getByText('Camille').tagName).toBe('STRONG');
    expect(container.querySelectorAll('li')).toHaveLength(2);
    expect(container).not.toHaveTextContent('###');
    expect(container).not.toHaveTextContent('**');
  });
});
