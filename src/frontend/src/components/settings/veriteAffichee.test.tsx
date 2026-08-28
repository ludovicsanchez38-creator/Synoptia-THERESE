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
    expect(await screen.findByText(/La recherche web/i)).toBeInTheDocument();
    expect(await screen.findByText(/vérification de mise à jour/i)).toBeInTheDocument();
  });

  it('ne prétend pas que l’interrupteur coupe TOUTE la recherche web', async () => {
    // Mon propre mensonge, attrapé par la relecture du diff : j'avais écrit
    // « tu peux la couper dans Réglages > Services ». Le réglage
    // `web_search_enabled` n'est lu que par le chat — Board (board.py),
    // recherche approfondie (deep_research.py) et Atelier (agents/tools.py)
    // appellent le service directement : 18 appels, zéro vérification du
    // réglage. Écrire cela dans le chantier « la vérité » aurait été le comble.
    render(<PrivacyTab />);
    const intitule = await screen.findByText(/La recherche web/i);
    // findByText rend le <strong> ; la phrase entière est dans le <li> parent.
    const texte = (intitule.closest('li') ?? intitule).textContent ?? '';

    expect(texte).toMatch(/Board|recherche approfondie|Atelier/i);
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

  it('dit que la base est chiffrée ET que l’index ne l’est pas', async () => {
    render(<PrivacyTab />);

    // Les deux moitiés comptent : « tout est chiffré » serait le mensonge
    // symétrique de celui qu'on vient de retirer.
    expect(await screen.findByText(/SQLCipher/i)).toBeInTheDocument();
    expect(await screen.findByText(/n'est pas chiffré/i)).toBeInTheDocument();
  });
});
