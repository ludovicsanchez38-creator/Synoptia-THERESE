/**
 * Chantier A-texte (28/08) : l'écran ne doit plus affirmer ce que
 * l'application ne fait pas.
 *
 * Ces assertions viennent de la campagne dix personas. Trois personas sur dix
 * sont partis sur ce motif, et pour deux d'entre eux (avocat, médecin) c'était
 * une ligne rouge professionnelle. La magistrate était venue chercher
 * exactement cet écart : « toute phrase de l'interface qui affirme plus que ce
 * que l'application fait réellement ».
 *
 * On teste le RENDU, pas le fichier source. Une première version lisait le
 * source en retirant les commentaires : contournable (une variable, une chaîne
 * découpée), et elle testait le dépôt plutôt que l'écran. Ici, ce qui est
 * asserté est ce que l'utilisateur lit.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api/rgpd', () => ({
  getPurgeSettings: vi.fn().mockResolvedValue({ enabled: true, months: 36 }),
  updatePurgeSettings: vi.fn().mockResolvedValue({}),
}));

import { PrivacyTab } from './PrivacyTab';

describe('L’onglet Confidentialité ne promet plus ce que l’app ne tient pas', () => {
  it('ne dit plus qu’aucune donnée n’est envoyée à un serveur externe', async () => {
    render(<PrivacyTab />);
    await screen.findByText(/Ce qui peut sortir de ta machine/i);

    // Faux : la recherche web part chez DuckDuckGo sans confirmation, la
    // vérification de mise à jour interroge synoptia.fr, et les modèles se
    // téléchargent depuis HuggingFace — y compris en modèle 100 % local.
    expect(screen.queryByText(/Aucune donnée n'est envoyée à un serveur externe/i)).toBeNull();
  });

  it('dit au contraire ce qui sort, la recherche web comprise', async () => {
    render(<PrivacyTab />);

    // La recherche web part SANS confirmation tant que le lot A-mécanique
    // n'est pas livré. L'écran doit l'avouer plutôt que de le taire.
    // « La recherche web » apparaît à deux endroits depuis qu'on l'a aussi
    // signalée dans le bloc des consentements : on vise la puce de l'encadré
    // Stockage, celle qui porte le contrat.
    const puces = await screen.findAllByText(/La recherche web/i);
    expect(puces.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/vérification de mise à jour/i).length).toBeGreaterThan(0);
  });

  it('ne prétend pas que l’interrupteur coupe TOUTE la recherche web', async () => {
    // Mon propre mensonge, attrapé par la relecture du diff : j'avais écrit
    // « tu peux la couper dans Réglages > Services ». Le réglage
    // `web_search_enabled` n'est lu que par le chat — Board (board.py),
    // recherche approfondie (deep_research.py) et Atelier (agents/tools.py)
    // appellent le service directement : 18 appels, zéro vérification du
    // réglage. Écrire cela dans le chantier « la vérité » aurait été le comble.
    render(<PrivacyTab />);
    const intitules = await screen.findAllByText(/La recherche web/i);
    // findAllByText rend les <strong> ; la phrase entière est dans le <li>.
    const texte = intitules
      .map((n) => (n.closest('li') ?? n).textContent ?? '')
      .join(' ');

    expect(texte).toMatch(/Board|recherche approfondie|Atelier/i);
    // Trou signalé par la revalidation : le chat sous Gemini fait de l'ancrage
    // Google Search SANS passer par l'outil `web_search`
    // (`gemini.py:216`, `enable_grounding=True` par défaut, et
    // `web_search_enabled` n'y est jamais lu). L'interrupteur ne le coupe pas.
    expect(texte).toMatch(/Gemini/i);
  });

  it('ne justifie plus la conservation illimitée par « pas de données personnelles tierces »', async () => {
    render(<PrivacyTab />);
    await screen.findByText(/Ce qui peut sortir de ta machine/i);

    // Le médecin a mis un nom de patiente dans le chat en trente secondes.
    expect(screen.queryByText('Pas de données personnelles tierces')).toBeNull();
  });

  it('ne dit plus que seules les métadonnées des fichiers sont conservées', async () => {
    render(<PrivacyTab />);
    await screen.findByText(/Ce qui peut sortir de ta machine/i);

    // Qdrant stocke le TEXTE extrait, découpé en fragments — pas une
    // métadonnée. Trouvé par la relecture de design, pas par la campagne.
    expect(screen.queryByText(/pas les fichiers eux-mêmes/i)).toBeNull();
  });

  it('ne dit plus que « tout reste local » faute de consentement cloud', async () => {
    // Trouvé en cherchant, sur demande du relecteur, s'il restait des phrases
    // du même type. Celle-ci était dans le MÊME onglet : « Aucun consentement
    // cloud accordé : tout reste local tant que tu n'autorises rien. »
    // Faux : la recherche web et la vérification de mise à jour ne passent par
    // aucun consentement.
    render(<PrivacyTab />);
    await screen.findByText(/Ce qui peut sortir de ta machine/i);

    expect(screen.queryByText(/tout reste local tant que tu n/i)).toBeNull();
  });

  it('dit que la base est chiffrée ET que l’index ne l’est pas', async () => {
    render(<PrivacyTab />);

    // Les deux moitiés comptent : « tout est chiffré » serait le mensonge
    // symétrique de celui qu'on vient de retirer.
    expect(await screen.findByText(/SQLCipher/i)).toBeInTheDocument();
    expect(await screen.findByText(/n'est pas chiffré/i)).toBeInTheDocument();
  });
});
