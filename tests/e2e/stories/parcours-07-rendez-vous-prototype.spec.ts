import { expect, test, type Page, type Route } from '@playwright/test';

const calendar = {
  id: 'calendar-local',
  account_id: null,
  summary: 'Agenda Synoptïa',
  description: 'Calendrier local',
  timezone: 'Europe/Paris',
  primary: true,
  provider: 'local',
  synced_at: '2026-07-13T08:00:00Z',
};

const event = {
  id: 'event-propulser',
  calendar_id: calendar.id,
  summary: 'Point PROPULSER avec Camille Martin',
  description: 'Valider les usages prioritaires et les prochaines étapes.',
  location: 'Visioconférence',
  start_datetime: '2026-07-15T09:30:00+02:00',
  end_datetime: '2026-07-15T10:15:00+02:00',
  start_date: null,
  end_date: null,
  all_day: false,
  attendees: ['camille@example.fr'],
  recurrence: null,
  status: 'confirmed',
  synced_at: '2026-07-13T08:00:00Z',
};

const contact = {
  id: 'contact-camille',
  first_name: 'Camille',
  last_name: 'Martin',
  company: 'Atelier Martin',
  email: 'camille@example.fr',
  phone: null,
  notes: 'Souhaite automatiser le suivi commercial sans perdre la relation humaine.',
  tags: ['PROPULSER'],
  stage: 'client',
  score: 82,
  source: 'réseau',
  last_interaction: '2026-07-10T12:00:00Z',
  created_at: '2026-06-01T08:00:00Z',
  updated_at: '2026-07-10T12:00:00Z',
};

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function installReadOnlyMeetingBackend(page: Page) {
  const writes: string[] = [];

  await page.addInitScript(() => {
    localStorage.setItem('onboarding_complete', 'true');
  });

  await page.route('http://127.0.0.1:17293/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const { pathname } = url;

    if (request.method() !== 'GET') {
      writes.push(`${request.method()} ${pathname}`);
      await json(route, { detail: 'Écriture non autorisée par ce scénario de contrôle.' }, 409);
      return;
    }
    if (pathname === '/api/auth/token') return json(route, { token: 'test-session-token' });
    if (pathname === '/api/config/onboarding-complete') {
      return json(route, { completed: true, completed_at: '2026-07-13T08:00:00Z' });
    }
    if (pathname === '/api/email/auth/status') return json(route, { connected: false, accounts: [] });
    if (pathname === '/api/memory/contacts') return json(route, [contact]);
    if (pathname === '/api/calendar/calendars') return json(route, [calendar]);
    if (pathname === '/api/calendar/events') return json(route, [event]);
    if (pathname === '/api/crm/activities') {
      return json(route, [{
        id: 'activity-1',
        contact_id: contact.id,
        type: 'note',
        title: 'Cadrage initial',
        description: 'Le besoin a été confirmé lors du premier échange.',
        extra_data: null,
        created_at: '2026-07-10T12:00:00Z',
      }]);
    }
    if (pathname === '/health') return json(route, { status: 'ok', version: '0.32.1' });
    return json(route, {});
  });

  return writes;
}

test.describe('Prototype conversationnel - Rendez-vous', () => {
  test('affiche uniquement le contexte réel relié sans aucune écriture', async ({ page }) => {
    const writes = await installReadOnlyMeetingBackend(page);
    await page.goto('/?prototype=conversation-canvas&scenario=meeting');

    await expect(page.getByTestId('meeting-agenda-card')).toBeVisible();
    await expect(page.getByText('Point PROPULSER avec Camille Martin').first()).toBeVisible();
    await expect(page.getByTestId('meeting-event-preparation')).toBeVisible();
    await expect(page.getByText('Atelier Martin · client · camille@example.fr')).toBeVisible();
    await expect(page.getByText(/Aucun contexte absent n’est inventé/)).toBeVisible();
    expect(writes).toEqual([]);
  });

  test('prépare la confirmation de création sans appeler le backend', async ({ page }, testInfo) => {
    const writes = await installReadOnlyMeetingBackend(page);
    await page.goto('/?prototype=conversation-canvas&scenario=meeting');
    await expect(page.getByTestId('meeting-agenda-card')).toBeVisible();

    await page.getByRole('button', { name: 'Nouvel événement' }).click();
    const form = page.getByTestId('meeting-new-event-form');
    await expect(form).toBeVisible();
    await form.getByLabel('Titre').fill('Revue offre PROPULSER');
    await form.getByLabel('Lieu ou lien').fill('Visioconférence');
    await form.getByLabel(/Participants/).fill('camille@example.fr');
    await form.getByRole('button', { name: 'Vérifier avant création' }).click();

    const confirmButton = form.getByRole('button', { name: 'Confirmer la création' });
    await expect(confirmButton).toBeVisible();
    await expect(form.getByText(/Créer « Revue offre PROPULSER ».*Agenda Synoptïa/)).toBeVisible();
    await expect(form.getByText(/Aucune donnée n’est écrite avant la confirmation finale/)).toBeVisible();
    expect(writes).toEqual([]);

    await confirmButton.scrollIntoViewIfNeeded();
    await page.screenshot({ path: testInfo.outputPath('rendez-vous-confirmation.png'), fullPage: true });
  });
});
