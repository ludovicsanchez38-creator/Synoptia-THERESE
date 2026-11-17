// Interface minimale pour exercer la même garde sans importer Playwright.
export interface RouteLectureSeule {
  request(): { url(): string; method(): string };
  continue(): Promise<void>;
  fulfill(reponse: { status: number; contentType: string; body: string }): Promise<void>;
}

interface PageLectureSeule {
  route(motif: string, gestionnaire: (route: RouteLectureSeule) => Promise<void>): Promise<void>;
}

export async function json(route: RouteLectureSeule, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

export async function installReadOnlyShell(page: PageLectureSeule, backendUrl: string) {
  await page.route(`${backendUrl}/**`, async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const methode = route.request().method();
    // Ce calcul est pur : il ne touche ni à la base ni à un fournisseur.
    if (methode === 'POST' && pathname === '/api/calc/roi') return route.continue();
    // Tester la méthode avant les lectures bouchonnées, sinon un POST peut
    // recevoir un succès factice sans être autorisé par le scénario.
    if (methode !== 'GET') {
      return route.fulfill({
        status: 405,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'ECRITURE_REFUSEE', message: pathname }),
      });
    }
    // 02/09/2026 : `/api/auth/token` n'est PLUS bouchonne. Un faux jeton etait
    // sans consequence tant que le repli repondait a tout, mais depuis que les
    // lectures non prevues atteignent le vrai backend jetable, celui-ci les
    // verifie (main.py, en-tete X-Therese-Token, compare_digest) : chacune
    // repartait en 401. La mise en route se pose desormais sur le vrai backend,
    // par `passerLaMiseEnRoute`, plutot que d'etre mimee ici.
    // Les statistiques viennent du moteur jetable : App doit recevoir son
    // identité réelle avant de monter le canevas et d'enregistrer les accords.
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
        // due_follow_ups manquait : le bouchon mentait sur le contrat, et
        // l'application tombait sur son ecran d'erreur. Elle se defend
        // desormais, mais un bouchon doit dire la verite du serveur.
        date: '2026-07-13', events: [], urgent_tasks: [], due_follow_ups: [],
        overdue_invoices: [], stale_prospects: [],
        summary: {
          events_count: 0, tasks_count: 0, follow_ups_count: 0,
          invoices_count: 0, prospects_count: 0,
        },
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

    // 01/09/2026. Le repli renvoyait `{}` a TOUTE route non prevue. Chaque
    // route ajoutee a l'application cassait donc ce fichier : un composant qui
    // attend une liste recevait un objet, `.filter` sur `undefined` remontait
    // au garde-fou de React, et les treize tests voyaient l'ecran « Oups ! »
    // au lieu de la coque. Un bouchon exhaustif est une liste a tenir a jour
    // pour toujours : personne ne le fait.
    //
    // La garantie que ce fichier doit apporter n'est pas « le backend est
    // fige », c'est « AUCUNE ECRITURE ne part ». On fige donc ce que les
    // scenarios controlent, on REFUSE bruyamment les ecritures, et on laisse
    // les lectures restantes atteindre le vrai backend jetable.
    return route.continue();
  });
}

