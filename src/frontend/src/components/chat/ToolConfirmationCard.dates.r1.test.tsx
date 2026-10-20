import { render, screen } from '@testing-library/react';
import { beforeEach, expect, it } from 'vitest';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { ToolConfirmationCard } from './ToolConfirmationCard';

beforeEach(() => useToolConfirmationStore.getState().clear());

it('présente une date civile française avec le jour sans décaler une heure sans fuseau', () => {
  useToolConfirmationStore.getState().add({ confirmation_id: 'date', tool_name: 'create_calendar_event', arguments: {
    summary: 'Point', start: '2026-10-22T10:00:00', end: '2026-10-22T11:00:00', timezone: 'Europe/Paris',
  } });
  render(<ToolConfirmationCard />);
  expect(screen.getByText('jeudi 22 octobre 2026 à 10:00')).toBeInTheDocument();
  expect(screen.getByText('jeudi 22 octobre 2026 à 11:00')).toBeInTheDocument();
});

it('convertit une date UTC dans le fuseau annoncé pour la tâche', () => {
  useToolConfirmationStore.getState().add({ confirmation_id: 'date', tool_name: 'create_task', arguments: {
    title: 'Appeler', due_date: '2026-10-22T08:00:00Z',
  } });
  render(<ToolConfirmationCard />);
  expect(screen.getByText('jeudi 22 octobre 2026 à 10:00')).toBeInTheDocument();
});
