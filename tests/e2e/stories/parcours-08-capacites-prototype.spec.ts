import { expect, test, type Page, type Route } from '@playwright/test';

async function json(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function installReadOnlyShell(page: Page) {
  await page.route('http://127.0.0.1:17293/**', async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/api/auth/token') return json(route, { token: 'test-session-token' });
    if (pathname === '/api/config/onboarding-complete') {
      return json(route, { completed: true, completed_at: '2026-07-13T08:00:00Z' });
    }
    if (pathname === '/health') return json(route, { status: 'ok', version: '0.32.1' });
    if (pathname === '/api/config/stats') {
      return json(route, {
        entities: { contacts: 1, projects: 1, conversations: 0, messages: 0, files: 0 },
        uptime_seconds: 60, data_dir: '/tmp/therese-test', db_path: '/tmp/therese-test.db',
      });
    }
    if (pathname === '/api/config/profile') {
      return json(route, {
        name: 'Ludovic Sanchez', nickname: 'Ludo', company: 'Synoptïa', role: null,
        context: null, email: null, location: null, address: null, siren: null,
        tva_intra: null, siret: null, code_ape: null, nda: null, display_name: 'Ludo',
      });
    }
    if (pathname === '/api/chat/conversations') {
      return json(route, [{
        id: 'conversation-history', title: 'Conversation réellement enregistrée', summary: null,
        message_count: 2, created_at: '2026-07-12T08:00:00Z', updated_at: '2026-07-13T09:00:00Z',
      }]);
    }
    if (pathname === '/api/chat/conversations/conversation-history/messages') {
      return json(route, [
        { id: 'message-1', conversation_id: 'conversation-history', role: 'user', content: 'Question enregistrée', tokens_in: null, tokens_out: null, model: null, created_at: '2026-07-13T09:00:00Z' },
        { id: 'message-2', conversation_id: 'conversation-history', role: 'assistant', content: 'Réponse enregistrée', tokens_in: null, tokens_out: null, model: null, created_at: '2026-07-13T09:01:00Z' },
      ]);
    }
    if (pathname === '/api/dashboard/today') {
      return json(route, {
        date: '2026-07-13', events: [], urgent_tasks: [], overdue_invoices: [], stale_prospects: [],
        summary: { events_count: 0, tasks_count: 0, invoices_count: 0, prospects_count: 0 },
      });
    }
    if (pathname === '/api/calc/roi') {
      return json(route, {
        investment: 10000, gain: 15000, roi_percent: 50, profit: 5000,
        interpretation: 'Très bon ROI de 50 %.',
      });
    }
    if (pathname === '/api/images/status') {
      return json(route, {
        openai_available: true, gemini_available: false, fal_available: false,
        active_provider: 'gpt-image-2',
      });
    }
    if (pathname === '/api/images/list') {
      return json(route, { images: [], total: 0 });
    }
    if (pathname === '/api/images/generate') {
      return json(route, {
        id: 'image-generated', provider: 'gpt-image-2', file_name: 'visuel.png', file_size: 1200,
        mime_type: 'image/png', created_at: '2026-07-14T10:00:00Z', prompt: 'Portrait éditorial de Thérèse',
        download_url: '/api/images/download/image-generated',
      });
    }
    if (pathname === '/api/follow-ups') {
      return json(route, [{
        id: 'follow-up-1', email_message_id: 'email-1', contact_id: 'contact-1',
        due_date: '2026-07-15T09:00:00Z', note: 'Valider la prochaine étape', status: 'pending',
        created_at: '2026-07-13T09:00:00Z', email_subject: 'Proposition accompagnement',
        email_from: 'camille@example.com', contact_name: 'Camille Martin',
      }]);
    }
    if (pathname === '/api/voice/local/status') {
      return json(route, {
        stt_available: true, tts_available: true, ready: true,
        whisper_models: {}, default_whisper_model: 'small', active_whisper_model: 'small',
        models_downloaded: { small: true }, tts_voice: 'fr', tts_voice_downloaded: true,
        setup: { state: 'done', step: '', error: '' },
      });
    }
    if (pathname === '/api/actions') {
      return json(route, [{
        id: 'rapport-hebdo', name: 'Rapport hebdomadaire',
        description: 'Prépare une synthèse vérifiable de la semaine.',
        icon: 'FileBarChart', category: 'organisation', steps_count: 3,
        tools: [], params: [{
          id: 'periode', label: 'Période', type: 'text', required: true,
          placeholder: 'Cette semaine', options: [],
        }],
      }]);
    }
    if (pathname === '/api/memory/projects') {
      return json(route, [{
        id: 'project-1', name: 'Accompagnement Camille', description: 'Projet réel', contact_id: 'contact-1',
        status: 'active', budget: 5000, notes: null, tags: [], created_at: '2026-07-01', updated_at: '2026-07-12',
      }]);
    }
    if (pathname === '/api/crm/deliverables') {
      return json(route, [
        { id: 'deliverable-1', project_id: 'project-1', title: 'Diagnostic IA', description: 'Version à relire', status: 'en_cours', due_date: '2026-07-20T10:00:00Z', completed_at: null, created_at: '2026-07-01', updated_at: '2026-07-12' },
        { id: 'deliverable-2', project_id: 'project-1', title: 'Plan d’action', description: null, status: 'valide', due_date: null, completed_at: '2026-07-10T10:00:00Z', created_at: '2026-07-01', updated_at: '2026-07-12' },
      ]);
    }
    if (pathname === '/api/memory/contacts' || pathname === '/api/memory/contacts/contact-1') {
      const contact = {
        id: 'contact-1', first_name: 'Camille', last_name: 'Martin', company: 'Client réel', email: 'camille@example.com',
        phone: null, notes: null, tags: [], stage: 'active', score: 0, source: 'local', last_interaction: null,
        created_at: '2026-07-01', updated_at: '2026-07-12',
      };
      return json(route, pathname.endsWith('/contact-1') ? contact : [contact]);
    }
    if (pathname === '/api/tasks') {
      return json(route, [{
        id: 'task-1', title: 'Relire le diagnostic', description: null, status: 'todo', priority: 'high', due_date: null,
        project_id: 'project-1', tags: [], completed_at: null, created_at: '2026-07-01', updated_at: '2026-07-12',
      }]);
    }
    if (pathname === '/api/invoices') {
      return json(route, [{
        id: 'invoice-1', invoice_number: 'F-2026-001', contact_id: 'contact-1', document_type: 'facture',
        tva_applicable: true, currency: 'EUR', issue_date: '2026-07-01', due_date: '2026-07-30', status: 'sent',
        subtotal_ht: 1000, total_tax: 200, total_ttc: 1200, notes: null, payment_terms: null, payment_method: null,
        late_penalty_rate: null, legal_mentions: null, converted_from_id: null, validite_jours: null, payment_date: null,
        created_at: '2026-07-01', updated_at: '2026-07-12', lines: [],
      }]);
    }
    if (pathname.includes('/commands')) {
      return json(route, []);
    }
    return json(route, {});
  });
}

async function chooseCapability(page: Page, name: string) {
  await page.getByRole('button', { name: 'Capacités' }).click();
  const dialog = page.getByRole('dialog', { name: 'Capacités de Thérèse' });
  await expect(dialog).toBeVisible();
  await dialog.getByPlaceholder(/Chercher une capacité/).fill(name);
  await dialog.getByRole('button', { name: new RegExp(`^${name}`) }).click();
  await expect(page.getByText(`Capacité : ${name}`)).toBeVisible();
}

test.describe('Prototype conversationnel - parcours unifiés des capacités', () => {
  test.beforeEach(async ({ page }) => {
    await installReadOnlyShell(page);
    await page.goto('/?prototype=conversation-canvas&scenario=today');
    await expect(page.getByTestId('conversation-canvas-prototype')).toBeVisible();
  });

  test('Tâches ouvre la vraie vue dans la coquille unifiée', async ({ page }) => {
    await chooseCapability(page, 'Tâches');
    await page.getByRole('button', { name: 'Ouvrir le parcours réel' }).click();

    await expect(page.getByTestId('prototype-unified-view')).toHaveAttribute('data-view', 'tasks');
    await expect(page.getByText('Relire le diagnostic', { exact: true })).toBeVisible();
    const url = new URL(page.url());
    expect(url.searchParams.get('prototype')).toBe('conversation-canvas');
    expect(url.searchParams.has('interface')).toBe(false);
  });

  test('Modèles et providers ouvre directement les réglages IA', async ({ page }) => {
    await chooseCapability(page, 'Modèles et providers');
    await page.getByRole('button', { name: 'Ouvrir le parcours réel' }).click();

    await expect(page.getByTestId('settings-tab-ai')).toBeVisible();
    const url = new URL(page.url());
    expect(url.searchParams.get('prototype')).toBe('conversation-canvas');
    expect(url.searchParams.has('interface')).toBe(false);
    expect(url.searchParams.has('action')).toBe(false);
    expect(url.searchParams.has('settings_tab')).toBe(false);
  });

  test('Personnalisation ouvre les réglages avancés réels', async ({ page }) => {
    await chooseCapability(page, 'Personnalisation');
    await page.getByRole('button', { name: 'Ouvrir le parcours réel' }).click();

    await expect(page.getByTestId('settings-modal')).toHaveAttribute('data-requested-tab', 'advanced');
    await expect(page.getByTestId('settings-modal')).toHaveAttribute('data-active-tab', 'advanced');
    await expect(page.getByTestId('settings-tab-advanced')).toBeVisible();
    await expect(page.getByTestId('settings-tab-advanced')).toHaveClass(/text-accent-cyan/);
    await expect(page.getByText('Comportement au lancement', { exact: true })).toBeVisible();
    await expect(page.getByTestId('ux-mode-toggle')).toBeVisible();
    const url = new URL(page.url());
    expect(url.searchParams.get('prototype')).toBe('conversation-canvas');
    expect(url.searchParams.has('interface')).toBe(false);
    expect(url.searchParams.has('action')).toBe(false);
    expect(url.searchParams.has('settings_tab')).toBe(false);
  });

  test('Références juridiques transmet la demande sans l’exposer dans l’URL', async ({ page }) => {
    await chooseCapability(page, 'Références juridiques');
    const composer = page.getByPlaceholder(/Demande à Thérèse/);
    await composer.fill('Analyse cette clause confidentielle avec le corpus vérifié.');
    await page.getByRole('button', { name: 'Poursuivre dans le chat' }).click();

    await expect(page.getByTestId('prototype-chat-surface')).toBeVisible();
    await expect(page.getByTestId('chat-message-input')).toHaveValue('Analyse cette clause confidentielle avec le corpus vérifié.');
    const url = new URL(page.url());
    expect(url.searchParams.has('prompt')).toBe(false);
    expect(url.searchParams.has('handoff')).toBe(false);
    expect(page.url()).not.toContain('confidentielle');
  });

  test('une demande libre poursuit la vraie conversation sans classement approximatif', async ({ page }) => {
    const composer = page.getByPlaceholder(/Demande à Thérèse/);
    await composer.fill('Compare précisément ces deux options confidentielles.');
    await page.getByRole('button', { name: 'Poursuivre dans le chat' }).click();

    await expect(page.getByTestId('prototype-chat-surface')).toBeVisible();
    await expect(page.getByTestId('chat-message-input')).toHaveValue('Compare précisément ces deux options confidentielles.');
    expect(page.url()).not.toContain('confidentielles');
  });

  test('le tiroir affiche et ouvre uniquement les conversations réellement enregistrées', async ({ page }) => {
    await page.getByRole('button', { name: 'Conversations' }).click();
    const drawer = page.getByTestId('prototype-conversation-drawer');

    await expect(drawer.getByText('Conversation réellement enregistrée')).toBeVisible();
    await expect(drawer.getByText('2 messages')).toBeVisible();
    await expect(drawer.getByText(/PROPULSER|Programme parrainage|12 conversations/)).toHaveCount(0);

    await drawer.getByText('Conversation réellement enregistrée').click();
    await expect(page.getByTestId('prototype-chat-surface')).toBeVisible();
    await expect(page.getByText('Réponse enregistrée')).toBeVisible();
    expect(new URL(page.url()).searchParams.has('interface')).toBe(false);
  });

  test('Word, PowerPoint et Excel ouvre la production guidée réelle', async ({ page }) => {
    await chooseCapability(page, 'Word, PowerPoint et Excel');
    await expect(page.getByTestId('capability-destination-message')).toContainText('surface fonctionnelle réelle');
    await page.getByRole('button', { name: 'Ouvrir le parcours réel' }).click();

    await expect(page.getByTestId('prototype-chat-surface')).toBeVisible();
    await expect(page.getByTestId('chat-message-input')).toHaveValue('Aide-moi à produire un document (DOCX, PPTX ou XLSX) :');
  });

  test('Calculateurs appelle le vrai moteur local et affiche son résultat', async ({ page }, testInfo) => {
    await chooseCapability(page, 'Calculateurs');
    await page.getByRole('button', { name: 'Ouvrir les calculateurs' }).click();
    const canvas = page.getByTestId('calculator-workspace-canvas');
    await expect(canvas).toBeVisible();
    await canvas.getByLabel('Investissement').fill('10000');
    await canvas.getByLabel('Gain total').fill('15000');
    await canvas.getByRole('button', { name: 'Calculer avec le moteur local' }).click();
    await expect(canvas.getByTestId('calculator-result')).toContainText('50 %');
    await page.screenshot({ path: testInfo.outputPath('calculateurs-roi.png'), fullPage: true });
  });

  test('Images ouvre le studio réel et exige une confirmation avant génération', async ({ page }) => {
    const generations: string[] = [];
    page.on('request', (request) => {
      if (request.method() === 'POST' && new URL(request.url()).pathname === '/api/images/generate') {
        generations.push(request.postData() || '');
      }
    });

    await chooseCapability(page, 'Images');
    await page.getByRole('button', { name: 'Ouvrir le studio Images' }).click();
    const canvas = page.getByTestId('images-workspace-canvas');
    await expect(canvas).toBeVisible();
    await canvas.getByLabel('Description du visuel').fill('Portrait éditorial de Thérèse');
    await canvas.getByRole('button', { name: 'Préparer la génération' }).click();
    expect(generations).toEqual([]);

    await canvas.getByRole('button', { name: 'Confirmer et générer' }).click();
    await expect(canvas.getByTestId('selected-generated-image')).toContainText('Portrait éditorial de Thérèse');
    expect(generations).toHaveLength(1);
    expect(new URL(page.url()).searchParams.has('interface')).toBe(false);
  });

  test('Relances et alertes ouvre les échéances réellement enregistrées', async ({ page }) => {
    await chooseCapability(page, 'Relances et alertes');
    await page.getByRole('button', { name: 'Ouvrir les relances' }).click();

    const canvas = page.getByTestId('follow-ups-workspace-canvas');
    await expect(canvas).toBeVisible();
    await expect(canvas.getByText('Proposition accompagnement', { exact: true })).toBeVisible();
    await expect(canvas.getByText('Camille Martin', { exact: true })).toBeVisible();
    await expect(canvas.getByText('Valider la prochaine étape', { exact: true })).toBeVisible();
  });

  test('Voix ouvre la transcription de fichier et la synthèse locale', async ({ page }) => {
    await chooseCapability(page, 'Voix et transcription');
    await page.getByRole('button', { name: 'Ouvrir l’espace Voix' }).click();

    const canvas = page.getByTestId('voice-workspace-canvas');
    await expect(canvas).toBeVisible();
    await expect(canvas.getByText('Whisper local')).toBeVisible();
    await expect(canvas.getByRole('button', { name: 'Générer l’audio local' })).toBeDisabled();
    await canvas.getByLabel('Texte à lire').fill('Bonjour Ludo.');
    await expect(canvas.getByRole('button', { name: 'Générer l’audio local' })).toBeEnabled();
  });

  test('Actions et relances ouvre le panneau d’exécution existant dans la coque', async ({ page }) => {
    await chooseCapability(page, 'Actions et relances');
    await page.getByRole('button', { name: 'Ouvrir le parcours réel' }).click();

    const actionPanel = page.getByRole('heading', { name: 'Actions' });
    await expect(actionPanel).toBeVisible();
    await expect(page.getByText('Rapport hebdomadaire', { exact: true })).toBeVisible();
    await expect(page.getByText('Prépare une synthèse vérifiable de la semaine.', { exact: true })).toBeVisible();
  });

  test('Livrables agrège le suivi réel en lecture seule', async ({ page }, testInfo) => {
    const mutations: string[] = [];
    page.on('request', (request) => {
      if (request.url().startsWith('http://127.0.0.1:17293/') && request.method() !== 'GET') {
        mutations.push(`${request.method()} ${new URL(request.url()).pathname}`);
      }
    });
    await chooseCapability(page, 'Livrables et suivi client');
    await page.getByRole('button', { name: 'Ouvrir le suivi client' }).click();

    const canvas = page.getByTestId('deliverables-workspace-canvas');
    await expect(canvas).toBeVisible();
    await expect(canvas.getByRole('heading', { name: 'Accompagnement Camille' })).toBeVisible();
    await expect(canvas.getByText('Diagnostic IA', { exact: true })).toBeVisible();
    await expect(canvas.getByText('Plan d’action', { exact: true })).toBeVisible();
    await expect(canvas.getByText('Relire le diagnostic', { exact: true })).toBeVisible();
    await expect(canvas.getByText('Facture F-2026-001', { exact: true })).toBeVisible();
    await expect(canvas).toContainText('La facturation est reliée au contact du projet');
    expect(mutations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath('livrables-suivi-client.png'), fullPage: true });
  });
});
