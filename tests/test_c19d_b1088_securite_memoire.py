"""Phrases professionnelles, secrets factices et motifs de refus sans payload."""
import pytest
from app.services.memory_card_security import contient_sensible, motif_sensible


@pytest.mark.parametrize('texte', [
    'Rendez-vous de 14h avec Paul Martin', 'Secrétaire de direction',
    'Je vous prie de bien vouloir', 'Traitement de la commande 42',
    'Parti en congés', 'Diagnostic de performance énergétique', 'Fournisseur de FO',
])
def test_phrases_professionnelles(texte):
    assert not contient_sensible(texte)


@pytest.mark.parametrize('texte', [
    'FR76 3000 6000 0112 3456 7890 189', 'DE89 3704 0044 0532 0130 00',
    'GB82 WEST 1234 5698 7654 32', 'FR76-3000-6000-0112-3456-7890-189',
    'mot de passe : exemple-factice', 'clé API : exemple-factice',
    'clé secrète : exemple-factice', 'smtp_passwd', 'crm_access_token',
    'sk-factice1234567890', 'AKIAABCDEFGHIJKLMNOP',
    'Santé : diabète', 'Opinion politique', 'Religion catholique', 'Syndicat CGT',
])
def test_protections_maintenues(texte):
    assert contient_sensible(texte)


@pytest.mark.asyncio
async def test_refus_explicite_sans_restituer_le_secret(db_session):
    from app.services.memory_cards import RefusMemoire, _ecrire
    with pytest.raises(RefusMemoire) as refus:
        await _ecrire(db_session, {'title': 'mot de passe : exemple-factice'},
                      automatique=False, scope='global', scope_id=None,
                      conversation_id=None, message_id=None)
    assert 'mot de passe' in str(refus.value).lower()
    assert 'exemple-factice' not in str(refus.value)


# Rejeu inventé APRÈS le correctif : dix entrées distinctes du corpus initial.
@pytest.mark.parametrize(('texte', 'refuse'), [
    ('Secrétariat général : appeler Léa jeudi', False),
    ('Je vous prie de trouver le devis joint', False),
    ('Paul est parti en congés lundi', False),
    ('Diagnostic de performance énergétique du local', False),
    ('Traitement de la commande 678', False),
    ('BE68 5390 0754 7034', True),
    ('NL91 ABNA 0417 1643 00', True),
    ('Mot de passe : NouveauFactice!83', True),
    ('api_key : une-valeur-factice', True),
    ('refresh_token : encore-factice', True),
])
def test_rejeu_apres_correctif(texte, refuse):
    assert contient_sensible(texte) is refuse


@pytest.mark.parametrize('iban', [
    'ES91 2100 0418 4502 0005 1332', 'IT60 X054 2811 1010 0000 0123 456',
    'CH93 0076 2011 6238 5295 7', 'LU28 0019 4006 4475 0000',
    'PT50 0002 0123 1234 5678 9015 4', 'BE68 5390 0754 7034',
    'NL91 ABNA 0417 1643 00', 'DE89 3704 0044 0532 0130 00',
    'GB82 WEST 1234 5698 7654 32', 'ＦＲ７６３０００６００００１１２３４５６７８９０１８９',
])
def test_formats_des_dix_pays_maintenus(iban):
    assert contient_sensible(iban)


@pytest.mark.asyncio
@pytest.mark.parametrize('phrase', [
    'Rendez-vous de 14h avec Paul Martin', 'Secrétaire de direction',
    'Je vous prie de bien vouloir', 'Traitement de la commande 42',
    'Parti en congés', 'Diagnostic de performance énergétique', 'Fournisseur de FO',
])
async def test_la_fiche_professionnelle_est_enregistree(db_session, phrase):
    from app.services.memory_cards import ecrire
    fiche = await ecrire({'kind': 'preference', 'subject': 'organisation',
                          'title': 'Organisation du travail', 'content': phrase})
    assert fiche['content'] == phrase


@pytest.mark.parametrize('nom', ['smtpToken', 'clientSecret', 'SMTPTOKEN', 'MYAPIKEY'])
def test_identifiants_de_secrets_sans_separateur(nom):
    assert contient_sensible(nom)


def test_limite_de_consommation_sans_secret():
    assert not contient_sensible('Régler token_limits pour limiter la consommation')


# Rejeu inventé après l'ajustement des identifiants de secrets.
@pytest.mark.parametrize(('texte', 'refuse'), [
    ('mailboxAccessToken', True), ('calendarClientSecret', True),
    ('CUSTOMTOKEN', True), ('SUPPORTAPIKEY', True), ('smtpPasswd', True),
    ('Secrétaire du comité', False), ('Secrétariat du chantier', False),
    ('Rendez-vous de 16h avec Nina Dupont', False),
    ('Je vous prie de confirmer la visite', False), ('token_limits', False),
])
def test_rejeu_identifiants_apres_ajustement(texte, refuse):
    assert contient_sensible(texte) is refuse


@pytest.mark.parametrize('separateur', ['/', '_', ':', ','])
def test_coordonnees_bancaires_avec_ponctuation(separateur):
    coordonnee = separateur.join(['FR76', '3000', '6000', '0112', '3456', '7890', '189'])
    assert motif_sensible(coordonnee) == 'une coordonnée bancaire (IBAN)'


@pytest.mark.parametrize('coordonnee', [
    'be68539007547034',  # Pays en minuscules, malgré une clé correcte.
    'ZZ22ABCDEFGHIJKLMNOP',  # Modulo 97 correct, pays absent du registre.
    'BE10ABCDEFGHIJKLMNOP',  # Modulo 97 correct, mauvaise longueur belge.
    'BE68 5390 0754 7035',  # Longueur correcte, clé incorrecte.
    'BE685390075470340',  # Un caractère supplémentaire, sans espace.
])
def test_iban_exige_pays_majuscules_longueur_nationale_et_cle(coordonnee):
    from app.services.memory_card_security import _contient_iban
    assert not _contient_iban(coordonnee)


# Dix variantes inventées après la correction des séparateurs bancaires.
@pytest.mark.parametrize(('texte', 'refuse'), [
    ('DE89:3704:0044:0532:0130:00', True), ('BE68,5390,0754,7034', True),
    ('GB82/WEST/1234/5698/7654/32', True), ('NL91_ABNA_0417_1643_00', True),
    ('FR76;3000;6000;0112;3456;7890;189', True),
    ('Rendez-vous de 10h avec Luc Petit', False),
    ('Réunion de 11h avec Rose Bernard', False),
    ('Secrétaire de la société', False), ('Départ de 12h pour la visite', False),
    ('Je vous prie de relire ce devis', False),
])
def test_rejeu_separateurs_apres_correctif(texte, refuse):
    assert contient_sensible(texte) is refuse


# Reprise B-1088 : le même corpus traverse les deux appelants réels.
CORPUS_REPRISE = [
    # Contre-exemples Astra v3, avec préfixe susceptible de chevaucher l'IBAN.
    ('Paiement de 12 euros sur BE68 5390 0754 7034', 'IBAN'),
    ('Paiement de 12 euros sur AT61 1904 3002 3457 3201', 'IBAN'),
    ('DE12 euros sur BE68 5390 0754 7034', 'IBAN'),
    ('DE12 euros sur AT61 1904 3002 3457 3201', 'IBAN'),
    ('Paul adhère à FO', 'syndicale'),
    ('Rendez-vous de 10h avec Paul Robert', None),
    ('Traitement des factures', None),
    ('Je te prie de confirmer la commande', None),
    ('mot de passe : exemple-factice', 'passe'),
    ('password : exemple-factice', 'secret'),
    ('FR76 3000 6000 0112 3456 7890 189', 'IBAN'),
    ('BE68 5390 0754 7034', 'IBAN'),
    ('Traitements médicamenteux', 'santé'),
    ('Traitement par antidépresseur', 'santé'),
    ('Traitement de chimiothérapie', 'santé'),
    ('Adhésion à la CFE-CGC', 'syndicale'),
    ('Militante de Solidaires', 'syndicale'),
    ('Carte de la FSU', 'syndicale'),
    ('Délégué UNSA', 'syndicale'),
    ('Membre de SUD', 'syndicale'),
    ('Force ouvrière : Paul souhaite adhérer', 'syndicale'),
    ('Encartée à la CFTC', 'syndicale'),
    ('Elle cotise à la CGT', 'syndicale'),
    ('Elle est adhérente à la CFDT', 'syndicale'),
    # Vingt formulations professionnelles créées pour cette seconde reprise.
    ('Traitement des réserves du chantier de Nantes', None),
    ('Traitement du bois de charpente jeudi', None),
    ('Diagnostic thermique du dépôt à préparer', None),
    ('Livrer les poutres au chantier à 08h avec Marc Colin', None),
    ('Élodie prépare le métrage de la dalle', None),
    ('Traitement des rapprochements bancaires mardi', None),
    ('Traitement comptable des amortissements', None),
    ('Je les prie de vérifier les écritures', None),
    ('La secrétaire classe les justificatifs de frais', None),
    ('Luc établit le budget annuel du cabinet', None),
    ('Traitement des dossiers de formation continue', None),
    ('Je vous prie de transmettre les attestations', None),
    ('Diagnostic pédagogique des besoins du groupe', None),
    ('Réserver la salle avec Nadia Blanchard à 09h30', None),
    ('Traitement des tickets du support informatique', None),
    ('Diagnostic du stockage distant avant migration', None),
    ('Je te prie de relire le cahier des charges', None),
    ('Réunion de 15h avec Alice Renault au dépôt', None),
    ('Visite de 17h avec Hugo Caron vendredi', None),
    ('Prévenir Emma Moreau du départ à 06h45', None),
    ('client_secretvalue2 : exemple-factice', 'secret'),
    ('smtppasswd2 : exemple-factice', 'secret'),
    ('Il prie chaque dimanche', 'religieuse'),
    ('Adhérent au parti écologiste', 'politique'),
    ('smtp_passwd2 : exemple-factice', 'secret'),
    ('SECRETKEY : exemple-factice', 'secret'),
    ('client_secret2 : exemple-factice', 'secret'),
    ('smtp_token2 : exemple-factice', 'secret'),
    ('traitements psychiatriques', 'santé'),
    ('adhérent à FO', 'syndicale'),
    ('membre de FO', 'syndicale'),
    ('syndiqué à FO', 'syndicale'),
    ('AT611904300234573201', 'IBAN'),
    ('Rendez-vous de 14h avec Paul Martin', None),
    ('Secrétaire de direction', None),
    ('Je vous prie de bien vouloir', None),
    ('Traitement de la commande 42', None),
    ('Parti en congés', None),
    ('Diagnostic de performance énergétique', None),
    ('Fournisseur de FO', None),
    ('Traitement des commandes', None),
    ('Diagnostic réseau', None),
    ('Traitement des factures fournisseurs', None),
    ('Diagnostic comptable annuel', None),
    ('Traitement des écritures comptables', None),
    ('Diagnostic structurel du bâtiment', None),
    ('Traitement des eaux du chantier', None),
    ('Diagnostic de toiture avant travaux', None),
    ('Traitement des inscriptions en formation', None),
    ('Diagnostic des besoins de formation', None),
    ('Traitement des données informatiques', None),
    ('Diagnostic du serveur informatique', None),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(('texte', 'categorie'), CORPUS_REPRISE)
@pytest.mark.parametrize('voie', ['fiche', 'journal'])
async def test_reprise_corpus_par_les_deux_services(db_session, texte, categorie, voie):
    from app.services.action_journal import verifier_texte
    from app.services.memory_cards import RefusMemoire, ecrire
    from fastapi import HTTPException

    if voie == 'fiche':
        async def executer():
            fiche = await ecrire({'kind': 'preference', 'subject': 'organisation',
                                 'title': 'Organisation du travail', 'content': texte})
            assert fiche['content'] == texte
        exception = RefusMemoire
    else:
        async def executer():
            verifier_texte('Organisation du travail', texte, None)
        exception = HTTPException
    if categorie is None:
        await executer()
    else:
        with pytest.raises(exception) as refus:
            await executer()
        message = str(refus.value)
        assert categorie.casefold() in message.casefold()
        assert texte not in message
        assert 'exemple-factice' not in message
