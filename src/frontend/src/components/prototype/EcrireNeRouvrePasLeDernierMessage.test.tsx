/**
 * B-061 - « Écrire » ouvre une rédaction vierge, même après une lecture.
 *
 * Constat du 02/09/2026 (reproduction RP11) : le commentaire du composant
 * l'affirme depuis l'entrée 10 — « en rédaction libre, il n'y a pas de message
 * d'origine à relire : seulement le brouillon à écrire ». La garde
 * d'affichage, elle, ne testait que `resource?.status === 'ready'`, sans
 * `!nouvelleRedaction` ; et le préremplissage (useEffect) ignorait lui aussi
 * la rédaction libre.
 *
 * Conséquence : si un message avait déjà été ouvert dans la session,
 * « Écrire » réaffichait ce message en entier (objet, expéditeur, corps) et
 * préremplissait le brouillon avec son adresse et « Re: <objet> ». Le
 * parcours l'entretient : `chooseScenario('email')` pose `redactionLibre` sans
 * vider la ressource, et `usePrototypeEmailData` ne remet jamais
 * `messageResource` à null.
 *
 * `EcrireOuvreUnBrouillon.test.tsx` ne couvrait que `resource={null}` : c'est
 * exactement l'angle mort. Ici la ressource est CHARGÉE, comme après une
 * lecture.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// Le parcours complet (dernier bloc) monte la coque, qui lit la boîte réelle.
vi.mock('../../services/api/email', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/email')>()),
  getEmailAuthStatus: vi.fn(),
  listEmailMessages: vi.fn(),
  getEmailMessage: vi.fn(),
}));

import { EmailMessageCanvas } from './EmailConversationCard';
import type { EmailMessage } from '../../services/api/email';
import type { ReadResource } from './usePrototypeReadData';

const MESSAGE_DEJA_LU = {
  id: 'msg-vernet',
  subject: 'Facture retard chantier Vernet',
  from_email: 'compta@vernet-btp.fr',
  from_name: 'Compta Vernet BTP',
  snippet: 'Bonjour, la facture 2026-118 reste impayée…',
  body_plain: 'Bonjour, la facture 2026-118 reste impayée depuis 45 jours.',
  date: '2026-08-29T09:12:00Z',
  is_read: true,
} as unknown as EmailMessage;

const RESSOURCE_CHARGEE: ReadResource<EmailMessage> = {
  status: 'ready',
  data: MESSAGE_DEJA_LU,
  error: null,
};

function rendreEnRedactionLibre() {
  return render(
    <EmailMessageCanvas
      resource={RESSOURCE_CHARGEE}
      nouvelleRedaction
      onRetry={vi.fn()}
      onGenerateDraft={vi.fn()}
      onSaveDraft={vi.fn()}
      onOpenClassic={vi.fn()}
    />,
  );
}

describe('B-061 - une rédaction libre ne rouvre pas le dernier message lu', () => {
  it('n’affiche aucun message d’origine, même si une ressource est encore chargée', () => {
    rendreEnRedactionLibre();

    expect(screen.queryByText(MESSAGE_DEJA_LU.body_plain as string)).toBeNull();
    expect(screen.queryByText('Facture retard chantier Vernet')).toBeNull();
  });

  it('laisse le destinataire et l’objet vides, sans « Re: » hérité', () => {
    rendreEnRedactionLibre();

    const destinataire = screen.getByLabelText(/destinataire du brouillon/i) as HTMLInputElement;
    const objet = screen.getByLabelText(/objet du brouillon/i) as HTMLInputElement;

    expect(destinataire.value).toBe('');
    expect(objet.value).toBe('');
  });

  it('témoin : hors rédaction libre, le message d’origine reste bien affiché', () => {
    // Sans ce témoin, vider la surface en toutes circonstances passerait au
    // vert : la lecture d'un message reçu doit continuer de fonctionner.
    render(
      <EmailMessageCanvas
        resource={RESSOURCE_CHARGEE}
        onRetry={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSaveDraft={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText(MESSAGE_DEJA_LU.body_plain as string)).toBeInTheDocument();
    const destinataire = screen.getByLabelText(/destinataire du brouillon/i) as HTMLInputElement;
    expect(destinataire.value).toBe('compta@vernet-btp.fr');
  });
});

/**
 * L'autre moitié du parcours : ouvrir un message DOIT quitter la rédaction libre.
 *
 * Relecture adversariale du correctif ci-dessus. `chooseScenario('email')` pose
 * `redactionLibre = true` (ConversationCanvasPrototype.tsx:1245), et
 * `onOpenMessage` (:1652) ne le remet JAMAIS à false. Tant que la garde
 * d'affichage ne testait que `resource?.status === 'ready'`, le message
 * s'affichait quand même - par accident. Avec la garde juste, il ne
 * s'afficherait plus : « Écrire » une fois dans la session, et toute lecture de
 * mail rendrait une rédaction vierge.
 *
 * C'est le motif consigné dans `docs/known-patterns.md` : une remédiation cache
 * sa propre régression. On mesure donc le parcours complet, dans la coque
 * montée, et pas seulement le composant.
 */
describe('B-061 - ouvrir un message quitte la rédaction libre', () => {
  it('après « Écrire », cliquer un message affiche bien ce message', async () => {
    const { act, fireEvent, screen: ecran } = await import('@testing-library/react');
    const { useChatStore } = await import('../../stores/chatStore');
    const { useNavigationStore } = await import('../../stores/navigationStore');
    const { usePersonalisationStore } = await import('../../stores/personalisationStore');
    const { _clearEscapeHandlers } = await import('../../lib/escapeStack');
    const { useEmailStore } = await import('../../stores/emailStore');
    const { getEmailAuthStatus, listEmailMessages, getEmailMessage } =
      await import('../../services/api/email');
    const { ConversationCanvasPrototype } = await import('./ConversationCanvasPrototype');

    const compte = {
      id: 'account-1', email: 'ludo@example.test', provider: 'imap', scopes: [],
      created_at: '2026-09-01', last_sync: null,
    };
    vi.mocked(getEmailAuthStatus).mockResolvedValue({ connected: true, accounts: [compte] } as never);
    vi.mocked(listEmailMessages).mockResolvedValue({ messages: [MESSAGE_DEJA_LU], total: 1 } as never);
    vi.mocked(getEmailMessage).mockResolvedValue(MESSAGE_DEJA_LU as never);

    // Grand écran : sous le seuil xl le canevas RECOUVRE la colonne, qui passe
    // alors `aria-hidden` - la boîte de réception sort de l'arbre
    // d'accessibilité et aucune requête par rôle ne peut plus l'atteindre.
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes('min-width: 1280px'),
      media: query, onchange: null,
      addListener: vi.fn(), removeListener: vi.fn(),
      addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia;

    _clearEscapeHandlers();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    usePersonalisationStore.setState({ skipDashboard: false });
    useEmailStore.setState({ accounts: [], currentAccountId: null, messages: [] } as never);
    window.history.replaceState({}, '', '/?interface=conversation-canvas');

    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });

    // 1. « Écrire » : rédaction libre, aucun message d'origine (correctif ci-dessus).
    await act(async () => { fireEvent.click(ecran.getByRole('button', { name: /Écrire/ })); });
    expect(await ecran.findByLabelText(/destinataire du brouillon/i)).toHaveValue('');

    // 2. Puis on clique un message de la boîte : on relit, on ne rédige plus.
    const entree = await ecran.findByRole('button', { name: /Facture retard chantier Vernet/ });
    await act(async () => { fireEvent.click(entree); });

    expect(
      await ecran.findByText(MESSAGE_DEJA_LU.body_plain as string),
      'le message ouvert doit être affiché : la rédaction libre n’a pas été quittée',
    ).toBeInTheDocument();
    expect(ecran.getByLabelText(/destinataire du brouillon/i)).toHaveValue('compta@vernet-btp.fr');
    // Délai explicite : ce cas monte la coque ENTIÈRE et attend deux chargements
    // asynchrones. Il tient en ~2 s seul, mais frôlait les 5 s par défaut quand
    // la suite complète tourne en parallèle - un rouge intermittent aurait été
    // pire qu'inutile.
  }, 20_000);
});
