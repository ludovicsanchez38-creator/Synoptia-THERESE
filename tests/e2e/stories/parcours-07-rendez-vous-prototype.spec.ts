import { expect, test, type APIRequestContext, type Page, type Route } from '@playwright/test';
import { BACKEND_URL } from './helpers/backend';
import { passerLaMiseEnRoute } from './helpers/surfaces';

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

/**
 * Le bouchon du scénario « rendez-vous ».
 *
 * 02/09/2026. Il répondait `{}` à TOUTE route non prévue et les deux tests
 * voyaient l'écran « Oups ! Cannot read properties of undefined (reading
 * 'filter') » : un composant attendait une liste et recevait un objet. C'est
 * exactement le défaut fermé la veille dans parcours-08 (B-136) — un bouchon
 * exhaustif est une liste à tenir à jour pour toujours, et personne ne le fait.
 *
 * La garantie que ce fichier doit apporter n'est pas « le backend est figé »,
 * c'est « AUCUNE ÉCRITURE ne part ». On fige donc les seules lectures dont le
 * scénario contrôle le contenu, on REFUSE bruyamment les écritures en les
 * consignant, et on laisse les lectures restantes atteindre le vrai backend
 * jetable.
 *
 * Corollaire : `/api/auth/token` n'est plus bouchonné. Un faux jeton était
 * sans conséquence tant que rien ne passait, mais le backend le vérifie
 * (`main.py`, en-tête `X-Therese-Token`, `compare_digest`) : chaque lecture
 * laissée passer serait repartie en 401. La mise en route est posée sur le
 * vrai backend, par `passerLaMiseEnRoute`, plutôt que mimée dans le bouchon.
 */
async function installerLeBackendDeControle(page: Page) {
  const writes: string[] = [];

  await page.route(`${BACKEND_URL}/**`, async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());

    if (request.method() !== 'GET') {
      writes.push(`${request.method()} ${pathname}`);
      await json(route, { detail: 'Écriture non autorisée par ce scénario de contrôle.' }, 409);
      return;
    }

    // Les seules lectures que le scénario contrôle : ce sont elles que les
    // assertions nomment.
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

    return route.continue();
  });

  return writes;
}

async function ouvrirLeScenarioRendezVous(page: Page, requete: APIRequestContext) {
  await passerLaMiseEnRoute(requete);
  const writes = await installerLeBackendDeControle(page);
  await page.goto('/?prototype=conversation-canvas&scenario=meeting');
  return writes;
}

test.describe('Prototype conversationnel - Rendez-vous', () => {
  test('affiche uniquement le contexte réel relié sans aucune écriture', async ({
    page,
    request,
  }) => {
    const writes = await ouvrirLeScenarioRendezVous(page, request);

    await expect(page.getByTestId('meeting-agenda-card')).toBeVisible();
    await expect(page.getByText('Point PROPULSER avec Camille Martin').first()).toBeVisible();
    await expect(page.getByTestId('meeting-event-preparation')).toBeVisible();
    await expect(page.getByText('Atelier Martin · client · camille@example.fr')).toBeVisible();
    await expect(page.getByText(/Aucun contexte absent n’est inventé/)).toBeVisible();
    expect(writes).toEqual([]);
  });

  test('prépare la confirmation de création sans appeler le backend', async ({
    page,
    request,
  }, testInfo) => {
    const writes = await ouvrirLeScenarioRendezVous(page, request);
    await expect(page.getByTestId('meeting-agenda-card')).toBeVisible();

    await page.getByRole('button', { name: 'Nouvel événement' }).click();
    const form = page.getByTestId('meeting-new-event-form');
    await expect(form).toBeVisible();
    await form.getByLabel('Titre').fill('Revue offre PROPULSER');
    // Le champ du lieu portait un `aria-label="Lieu du rendez-vous"` qui
    // ÉCRASAIT son libellé visible « Lieu ou lien » : un nom accessible qui ne
    // contient pas le texte affiché casse la commande vocale (WCAG 2.5.3
    // « Label in Name »). Constat RE34-C2, corrigé côté application par le lot
    // RE35 (B-263, commit 0a1b181b) — le champ se désigne désormais par ce que
    // l'utilisateur lit.
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
