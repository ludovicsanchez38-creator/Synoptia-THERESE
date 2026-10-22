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
