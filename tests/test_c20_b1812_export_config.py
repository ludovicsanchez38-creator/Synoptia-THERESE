"""L'export annoncé complet doit inclure les données CRM enregistrées."""

import json

import pytest
from app.models.entities import (
    Activity,
    Calendar,
    Conversation,
    Deliverable,
    EmailAccount,
    Preference,
    Project,
)


@pytest.mark.asyncio
async def test_export_config_inclut_les_activites_et_livrables(client, db_session):
    db_session.add(Project(id="projet-export", name="Projet d'essai"))
    await db_session.flush()
    db_session.add_all([
        Activity(id="activite-export", project_id="projet-export", type="note", title="Note"),
        Deliverable(id="livrable-export", project_id="projet-export", title="Compte rendu"),
        Conversation(id="conversation-export", project_id="projet-export", memory_scope="project"),
    ])
    await db_session.commit()

    reference = await client.get("/api/data/export")
    assert reference.status_code == 200
    assert "activite-export" in {a["id"] for a in reference.json()["activities"]}
    assert "livrable-export" in {d["id"] for d in reference.json()["deliverables"]}

    reponse = await client.post("/api/config/export")
    assert reponse.status_code == 200
    export = reponse.json()
    activites = {a["id"] for a in export.get("activities", [])}
    livrables = {d["id"] for d in export.get("deliverables", [])}
    assert ("activite-export" in activites, "livrable-export" in livrables) == (True, True)
    conversation = next(c for c in export["conversations"] if c["id"] == "conversation-export")
    assert conversation["project_id"] == "projet-export"
    assert conversation["memory_scope"] == "project"


@pytest.mark.asyncio
async def test_export_config_exclut_les_secrets_de_connexion(client, db_session):
    temoin = "valeur-confidentielle-fictive"
    db_session.add(Preference(key="crm_sheets_refresh_token", value=temoin, category="crm"))
    db_session.add(EmailAccount(
        id="compte-export", email="test@example.invalid", client_secret=temoin,
        access_token=temoin, refresh_token=temoin, imap_password=temoin,
    ))
    db_session.add(Calendar(id="cal-export", summary="Agenda", caldav_password=temoin))
    await db_session.commit()

    reponse = await client.post("/api/config/export")
    assert reponse.status_code == 200
    assert temoin not in reponse.text
    assert reponse.json()["preferences"][0]["value"] == "[REDACTED]"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_masque_identifiants_des_urls_et_configurations_de_connexion(
    client, db_session, route,
):
    utilisateur = "identifiant-fictif"
    mot_de_passe = "motdepasse-fictif"
    url = f"https://{utilisateur}:{mot_de_passe}@hote.example/dav?vue=mois&password={mot_de_passe}"
    db_session.add(Calendar(
        id="cal-url", summary="Agenda", provider="caldav", caldav_url=url,
        remote_id=url, caldav_username=utilisateur, caldav_password=mot_de_passe,
    ))
    db_session.add(EmailAccount(
        id="compte-url", email="contact@example.invalid", imap_host=url,
        smtp_host=url, imap_username=utilisateur, imap_password=mot_de_passe,
    ))
    db_session.add(Preference(
        key="proxy_config", category="general",
        value='{"url": "' + url + '", "username": "' + utilisateur
        + '", "password": "' + mot_de_passe + '"}',
    ))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    assert utilisateur not in reponse.text
    assert mot_de_passe not in reponse.text
    assert "hote.example/dav" in reponse.text
    assert "contact@example.invalid" in reponse.text


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
@pytest.mark.parametrize("caractere", ["'", '"', "<", ">", "\\", " "])
async def test_export_masque_url_dont_le_mot_de_passe_contient_un_delimiteur(
    client, db_session, route, caractere,
):
    utilisateur = "temoin"
    mot_de_passe = f"FAUX-sec{caractere}ret"
    url = f"https://{utilisateur}:{mot_de_passe}@agenda.invalid/dav"
    db_session.add(Calendar(
        id="cal-dav-caractere", summary="Agenda", provider="caldav",
        caldav_url=url, remote_id=url,
        description=f"Adresse : {url}",
    ))
    db_session.add(Preference(
        key="proxy_config", category="general",
        value=json.dumps({"serveurs": [{"url": url, "username": utilisateur}]}),
    ))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    export = reponse.json()
    agenda = next(c for c in export["calendars"] if c["id"] == "cal-dav-caractere")
    proxy = json.loads(next(p["value"] for p in export["preferences"] if p["key"] == "proxy_config"))
    valeurs = [agenda["caldav_url"], agenda["remote_id"], agenda["description"], proxy["serveurs"][0]["url"]]

    def chaines(valeur):
        if isinstance(valeur, dict):
            for element in valeur.values():
                yield from chaines(element)
        elif isinstance(valeur, list):
            for element in valeur:
                yield from chaines(element)
        elif isinstance(valeur, str):
            yield valeur
            try:
                contenu = json.loads(valeur)
            except (TypeError, ValueError):
                return
            if isinstance(contenu, (dict, list)):
                yield from chaines(contenu)

    assert all(utilisateur not in texte and mot_de_passe not in texte for texte in chaines(export))
    assert all(utilisateur not in valeur and mot_de_passe not in valeur for valeur in valeurs)
    assert all("agenda.invalid/dav" in valeur for valeur in valeurs)
    assert proxy["serveurs"][0]["username"] == "[REDACTED]"


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_conserve_le_texte_entre_une_url_et_une_adresse_mail(
    client, db_session, route,
):
    description = "Voir https://agenda.invalid puis contacter : personne@example.invalid"
    db_session.add(Calendar(id="cal-texte", summary="Agenda", description=description))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    agenda = next(c for c in reponse.json()["calendars"] if c["id"] == "cal-texte")
    assert agenda["description"] == description


# Relecture 4 du lot (17/11/2026) : le masquage prenait le port d'une URL pour
# le début d'un identifiant dès qu'une adresse e-mail suivait sur la ligne, et
# retraitait comme un texte le JSON déjà sérialisé d'une préférence.
@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_conserve_un_port_suivi_d_une_adresse_mail(client, db_session, route):
    description = "Voir https://agenda.invalid:443 puis contacter : personne@example.invalid"
    preference = '{"url":"https://agenda.invalid:443","email":"personne@example.invalid"}'
    db_session.add(Calendar(id="cal-port", summary="Agenda", description=description))
    db_session.add(Preference(key="annuaire_config", category="general", value=preference))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    export = reponse.json()
    agenda = next(c for c in export["calendars"] if c["id"] == "cal-port")
    assert agenda["description"] == description
    valeur = json.loads(next(p["value"] for p in export["preferences"] if p["key"] == "annuaire_config"))
    assert valeur == {"url": "https://agenda.invalid:443", "email": "personne@example.invalid"}


@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        # Rien à masquer : la valeur sort telle quelle.
        ("https://agenda.invalid:443/dav", "https://agenda.invalid:443/dav"),
        ("Voir https://agenda.invalid:443 puis écrire à a@b.invalid", "Voir https://agenda.invalid:443 puis écrire à a@b.invalid"),
        ("https://[::1]:8443/dav puis a@b.invalid", "https://[::1]:8443/dav puis a@b.invalid"),
        ("Site https://site.invalid, contact a@b.invalid", "Site https://site.invalid, contact a@b.invalid"),
        ("écrire à a@b.invalid", "écrire à a@b.invalid"),
        # Identifiants : tout ce qui précède le dernier @ de l'autorité part.
        ("https://temoin:FAUX-secret@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("https://temoin@agenda.invalid:8443/dav", "https://agenda.invalid:8443/dav"),
        ("https://temoin:12345'ret@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("Adresse : 'https://temoin:FAUX\"sec@agenda.invalid/dav'", "Adresse : 'https://agenda.invalid/dav'"),
        ("Voir https://temoin:FAUX sec@agenda.invalid/dav.", "Voir https://agenda.invalid/dav."),
        # Une URL passée en paramètre d'une autre est lue elle aussi.
        (
            "https://a.invalid/?suite=https://temoin:FAUX-secret@b.invalid/x",
            "https://a.invalid/?suite=https://b.invalid/x",
        ),
    ],
)
def test_masquage_des_urls_table_de_cas(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


def test_masquage_d_un_json_serialise_garde_ses_autres_champs():
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export('{"url":"https://temoin:FAUX-secret@agenda.invalid/dav","email":"p@e.invalid"}')
    assert json.loads(sortie) == {"url": "https://agenda.invalid/dav", "email": "p@e.invalid"}


def test_masquage_d_un_json_sans_identifiant_garde_tous_ses_champs():
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export('{"url":"https://agenda.invalid:443","email":"personne@example.invalid"}')
    assert json.loads(sortie) == {"url": "https://agenda.invalid:443", "email": "personne@example.invalid"}


def test_masquage_d_un_json_a_cles_en_double_ne_rend_pas_la_chaine_d_origine():
    """Le lecteur JSON ne garde que la dernière clé : comparer au résultat lu ne prouve rien sur le texte."""
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export(
        '{"url":"https://temoin:FAUX-secret@agenda.invalid/dav","url":"https://agenda.invalid/dav"}'
    )
    assert "temoin" not in sortie and "FAUX-secret" not in sortie
    assert json.loads(sortie) == {"url": "https://agenda.invalid/dav"}


def test_masquage_des_cles_d_un_json():
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export({"https://temoin:FAUX-secret@agenda.invalid/dav": "agenda"})
    assert sortie == {"https://agenda.invalid/dav": "agenda"}


def test_masquage_d_urls_imbriquees_en_grand_nombre_sans_debordement():
    from app.routers.data import _masquer_urls_export

    entree = "https://a.invalid/?s=" * 5000 + "https://temoin:FAUX-secret@b.invalid/x"
    sortie = _masquer_urls_export(entree)
    assert "FAUX-secret" not in sortie and "temoin" not in sortie
    assert sortie == "https://a.invalid/?s=" * 5000 + "https://b.invalid/x"


@pytest.mark.parametrize("texte", ["https://a.invalid/?https://b.invalid/x", "https://a.invalid/#https://b.invalid/x"])
def test_masquage_garde_le_separateur_devant_une_url_imbriquee(texte):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(texte) == texte


# Revue de sécurité du 17/11 : couper une URL là où une URL imbriquée commence
# laissait sortir un paramètre de connexion placé après elle.
@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        (
            "https://a.invalid/?next=http://x.invalid&password=FAUX-secret",
            "https://a.invalid/?next=http://x.invalid&password=[REDACTED]",
        ),
        (
            "https://a.invalid/?r=https://b.invalid/&access_token=FAUX-secret&vue=mois",
            "https://a.invalid/?r=https://b.invalid/&access_token=[REDACTED]&vue=mois",
        ),
        (
            "https://a.invalid/?r=https://b.invalid/?access_token=FAUX-secret",
            "https://a.invalid/?r=https://b.invalid/?access_token=[REDACTED]",
        ),
        ("https://a.invalid/retour#access_token=FAUX-secret&etat=1", "https://a.invalid/retour#access_token=[REDACTED]&etat=1"),
        (
            "https://temoin:FAUX-secret@a.invalid/?r=https://temoin:FAUX-secret@b.invalid/x&password=FAUX-secret",
            "https://a.invalid/?r=https://b.invalid/x&password=[REDACTED]",
        ),
        # Ce qui n'est pas un secret sort à l'identique, casse comprise.
        ("HTTPS://Agenda.invalid/Dav?Vue=Mois", "HTTPS://Agenda.invalid/Dav?Vue=Mois"),
        ("Noter password=exemple dans le guide", "Noter password=exemple dans le guide"),
    ],
)
def test_masquage_des_parametres_de_connexion_sur_toute_l_url(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


# Relecture 5 du lot (17/11/2026) : une ponctuation après le port relançait la
# confusion avec un identifiant, deux clés distinctes devenaient identiques une
# fois masquées, et la réécriture d'un JSON altérait ses nombres.
@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
@pytest.mark.parametrize("apres_le_port", [",", ".", ")", ";", " :", "!"])
async def test_export_conserve_un_port_suivi_d_une_ponctuation(client, db_session, route, apres_le_port):
    description = f"Voir https://agenda.invalid:443{apres_le_port} puis contacter : personne@example.invalid"
    db_session.add(Calendar(id="cal-ponctuation", summary="Agenda", description=description))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    agenda = next(c for c in reponse.json()["calendars"] if c["id"] == "cal-ponctuation")
    assert agenda["description"] == description


@pytest.mark.parametrize(
    "texte",
    [
        "Voir https://exemple.invalid:test puis écrire à a@b.invalid",
        "Serveur https://exemple.invalid:prod, deux mots puis a@b.invalid",
        "https://agenda.invalid:443, puis a@b.invalid",
    ],
)
def test_masquage_ne_prolonge_un_identifiant_que_sur_le_mot_suivant(texte):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(texte) == texte


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_garde_deux_entrees_dont_les_cles_se_confondent_une_fois_masquees(client, db_session, route):
    db_session.add(Project(
        id="projet-cles", name="Projet aux deux agendas",
        extra_data=json.dumps({
            "https://alice:FICTIF-a@agenda.invalid/dav": "Personnel",
            "https://bob:FICTIF-b@agenda.invalid/dav": "Travail",
        }),
    ))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    assert all(secret not in reponse.text for secret in ("alice", "bob", "FICTIF-a", "FICTIF-b"))
    projet = next(p for p in reponse.json()["projects"] if p["id"] == "projet-cles")
    donnees = projet["extra_data"] if isinstance(projet["extra_data"], dict) else json.loads(projet["extra_data"])
    assert sorted(donnees.values()) == ["Personnel", "Travail"]
    assert all("agenda.invalid/dav" in cle for cle in donnees)


def test_masquage_des_cles_sans_collision_avec_une_cle_deja_presente():
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export({
        "https://temoin:FAUX-secret@agenda.invalid/dav": "avec identifiants",
        "https://agenda.invalid/dav": "sans identifiants",
    })
    assert sorted(sortie.values()) == ["avec identifiants", "sans identifiants"]
    assert sortie["https://agenda.invalid/dav"] == "sans identifiants"
    assert not any("temoin" in cle or "FAUX-secret" in cle for cle in sortie)

    texte = _masquer_urls_export(
        '{"https://alice:FICTIF-a@agenda.invalid/dav":"Personnel","https://bob:FICTIF-b@agenda.invalid/dav":"Travail"}'
    )
    assert sorted(json.loads(texte).values()) == ["Personnel", "Travail"]
    assert "alice" not in texte and "bob" not in texte and "FICTIF" not in texte


@pytest.mark.parametrize(
    "texte",
    [
        '{"montant":123456789.123456789}',
        '{"grand": 123456789012345678901234567890, "petit": 1e-400, "liste": [0.1, 1.10, -0.0]}',
        '{ "espaces" :  "gardés" ,"vide":{},"rien":null,"vrai":true }',
    ],
)
def test_masquage_rend_tel_quel_un_json_sans_identifiant(texte):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(texte) == texte


def test_masquage_d_un_json_garde_ses_nombres_au_caractere_pres():
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export(
        '{"url":"https://temoin:FAUX-secret@agenda.invalid/dav","montant":123456789.123456789,"n":1.10,"ok":true}'
    )
    assert "temoin" not in sortie and "FAUX-secret" not in sortie
    assert "123456789.123456789" in sortie and "1.10" in sortie
    assert json.loads(sortie)["url"] == "https://agenda.invalid/dav"
    assert json.loads(sortie)["ok"] is True


@pytest.mark.parametrize("profondeur", [300, 5000])
def test_masquage_d_un_json_tres_imbrique_ne_fait_pas_tomber_l_export(profondeur):
    from app.routers.data import _masquer_urls_export

    texte = "[" * profondeur + '"https://temoin:FAUX-secret@agenda.invalid/dav"' + "]" * profondeur
    sortie = _masquer_urls_export(texte)
    assert "temoin" not in sortie and "FAUX-secret" not in sortie
    assert "agenda.invalid/dav" in sortie


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_d_une_preference_json_garde_ses_nombres(client, db_session, route):
    intacte = '{"montant":123456789.123456789,"url":"https://agenda.invalid:443"}'
    db_session.add(Preference(key="devis_config", category="general", value=intacte))
    db_session.add(Preference(
        key="relais_config", category="general",
        value='{"seuil":0.10,"password":"FAUX-secret","url":"https://temoin:FAUX-secret@agenda.invalid/dav"}',
    ))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    valeurs = {p["key"]: p["value"] for p in reponse.json()["preferences"]}
    assert valeurs["devis_config"] == intacte
    assert "FAUX-secret" not in valeurs["relais_config"] and "temoin" not in valeurs["relais_config"]
    assert '"seuil": 0.10' in valeurs["relais_config"]
    assert json.loads(valeurs["relais_config"]) == {
        "seuil": 0.1, "password": "[REDACTED]", "url": "https://agenda.invalid/dav",
    }


@pytest.mark.parametrize("profondeur", [400, 6000])
def test_preference_json_trop_imbriquee_ne_sort_jamais_brute(profondeur):
    """Revue de sécurité du 17/11 : un parcours qui déborde ne doit pas rendre la valeur telle quelle."""
    from app.routers.data import _valeur_de_preference_exportable

    valeur = '{"a":' * profondeur + '{"password":"FAUX-secret"}' + "}" * profondeur
    sortie = _valeur_de_preference_exportable(Preference(key="relais_config", category="general", value=valeur))
    assert "FAUX-secret" not in sortie


def test_preference_qui_n_est_pas_un_json_sort_telle_quelle():
    from app.routers.data import _valeur_de_preference_exportable

    for valeur in ("sombre", "{pas du json", "[1, 2"):
        assert _valeur_de_preference_exportable(Preference(key="theme", category="general", value=valeur)) == valeur


# Relecture 6 du lot (17/11/2026) : un lien HTML suivi d'une adresse e-mail
# était tronqué, une URL imbriquée absorbait les paramètres suivants, et un
# point-virgule coupait la valeur d'un paramètre de connexion.
TEXTES_SANS_IDENTIFIANT = [
    '<img src="https://logo.invalid">personne@example.invalid',
    '<a href="https://site.invalid">contact@site.invalid</a>',
    "<a href='https://site.invalid:8443/x'>a@b.invalid</a>",
    "<a href=https://site.invalid>a@b.invalid</a>",
    'Config : {"url":"https://hote.invalid:443","email":"a@b.invalid"} fin',
    "[contact@site.invalid](https://site.invalid)",
    "(voir https://site.invalid),a@b.invalid",
    "Voir https://site.invalid;a@b.invalid ici",
    "Liste : https://site.invalid,a@b.invalid fin",
    "<https://site.invalid>a@b.invalid",
    "https://site.invalid/?next=https://agenda.invalid&email=personne@example.invalid",
    "https://site.invalid/?a=1;next=https://agenda.invalid;email=personne@example.invalid",
    "https://site.invalid/#retour=https://agenda.invalid:443&mail=a@b.invalid",
    # Une URL entre guillemets ou chevrons s'arrête au guillemet fermant.
    '<a href="/aller?u=https://site.invalid">contact@site.invalid</a>',
    '<a href="https://suivi.invalid/?u=https://site.invalid">contact@site.invalid</a>',
    '<a href="https://exemple.invalid:port"> a@b.invalid</a>',
    '"https://exemple.invalid:port" puis a@b.invalid',
    "{'url': 'https://hote.invalid:8443', 'mail': 'a@b.invalid'}",
    "Connexion : https://exemple.invalid:8080 (admin@exemple.invalid)",
]


@pytest.mark.parametrize("texte", TEXTES_SANS_IDENTIFIANT)
def test_masquage_laisse_intact_un_texte_sans_identifiant(texte):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(texte) == texte


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_conserve_html_et_url_imbriquee_sans_identifiant(client, db_session, route):
    description = "\n".join(TEXTES_SANS_IDENTIFIANT)
    db_session.add(Calendar(id="cal-html", summary="Agenda", description=description))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    agenda = next(c for c in reponse.json()["calendars"] if c["id"] == "cal-html")
    assert agenda["description"] == description


@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        # Un secret entier part, point-virgule compris ; les autres paramètres restent.
        ("https://site.invalid/?password=FICTIF;deuxieme&vue=mois", "https://site.invalid/?password=[REDACTED]&vue=mois"),
        ("https://site.invalid/?vue=mois;jour&token=FICTIF#p", "https://site.invalid/?vue=mois;jour&token=[REDACTED]#p"),
        # Identifiants dont le mot de passe porte un séparateur de texte.
        ('<a href="https://temoin:FAUX-secret@site.invalid/x">lien</a>', '<a href="https://site.invalid/x">lien</a>'),
        ("https://temoin:FAUX,sec;ret@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("https://temoin:FAUX)sec@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("https://temoin:p&ss@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("https://temoin'x@agenda.invalid/dav", "https://agenda.invalid/dav"),
        # Une URL imbriquée avec ses propres identifiants, suivie d'un autre paramètre.
        (
            "https://site.invalid/?next=https://temoin:FAUX-secret@agenda.invalid/x&email=personne@example.invalid",
            "https://site.invalid/?next=https://agenda.invalid/x&email=personne@example.invalid",
        ),
    ],
)
def test_masquage_des_identifiants_a_separateurs(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


@pytest.mark.parametrize(
    "texte",
    [
        "x" * 300_000 + "https://hote.invalid" * 20_000,
        "https://a.invalid/?s=" * 20_000 + "https://hote.invalid/",
        '"https://hote.invalid">a@b.invalid ' * 8_000,
        "https://hote.invalid:" + "9" * 400_000,
    ],
    ids=["prefixe-et-urls", "urls-imbriquees", "url-et-mail", "port-tres-long"],
)
def test_masquage_reste_rapide_sur_un_texte_tres_long(texte):
    """Le coût est linéaire : un export ne doit pas pouvoir être figé par un champ volumineux."""
    import time

    from app.routers.data import _masquer_urls_export

    depart = time.monotonic()
    assert _masquer_urls_export(texte) == texte
    assert time.monotonic() - depart < 5


# Revue de sécurité du 17/11 sur la passe précédente.
@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        # Un paramètre secret placé après un point-virgule est vu, et sa valeur part en entier.
        ("https://site.invalid/?vue=mois;password=FAUX-secret", "https://site.invalid/?vue=mois;password=[REDACTED]"),
        ("https://site.invalid/?a=1;token=FAUX;suite&vue=mois", "https://site.invalid/?a=1;token=[REDACTED]&vue=mois"),
        # Un « nom:secret » reste un indice, même entre guillemets ou chevrons.
        ('Adresse : "https://temoin:FAUX"sec@agenda.invalid/dav"', 'Adresse : "https://agenda.invalid/dav"'),
        ("<https://temoin:FAUX>sec@agenda.invalid/dav>", "<https://agenda.invalid/dav>"),
    ],
)
def test_masquage_parametre_apres_point_virgule_et_guillemet_dans_un_mot_de_passe(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


# Relecture 7 du lot (17/11/2026) : un champ qui est une URL entière se lit
# comme une bibliothèque d'URL le lit ; dans un texte, un guillemet ne prolonge
# jamais une URL sans l'indice « nom:secret ».
@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        ("https://temoin:42,FAUX-secret@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("https://temoin:42;FAUX(secret)@agenda.invalid/dav", "https://agenda.invalid/dav"),
        ("https://temoin,x:12345@agenda.invalid:8443/dav", "https://agenda.invalid:8443/dav"),
        ("  https://temoin:42,FAUX-secret@agenda.invalid/dav\n", "  https://agenda.invalid/dav\n"),
        ('{"url":"https://temoin:42,FAUX-secret@agenda.invalid/dav"}', '{"url": "https://agenda.invalid/dav"}'),
    ],
)
def test_masquage_d_un_champ_qui_est_une_url_entiere(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
async def test_export_masque_un_mot_de_passe_qui_commence_par_des_chiffres(client, db_session, route):
    url = "https://temoin:42,FAUX-secret@agenda.invalid/dav"
    db_session.add(Calendar(id="cal-chiffres", summary="Agenda", provider="caldav", caldav_url=url, remote_id=url))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    assert "FAUX-secret" not in reponse.text and "temoin" not in reponse.text
    agenda = next(c for c in reponse.json()["calendars"] if c["id"] == "cal-chiffres")
    assert agenda["caldav_url"] == "https://agenda.invalid/dav"


@pytest.mark.parametrize(
    "texte",
    [
        '<img src=" https://logo.invalid">personne@example.invalid',
        '<a href= "https://site.invalid" >contact@site.invalid</a>',
        "<a href=' https://site.invalid:8443/x '>a@b.invalid</a>",
        "L'adresse est https://site.invalid'puis a@b.invalid",
        'Il a dit "voir https://site.invalid" a@b.invalid',
        "Sur https://site.invalid's admin@site.invalid répond",
        '<td>"https://site.invalid"</td><td>a@b.invalid</td>',
    ],
)
def test_masquage_dans_un_texte_un_guillemet_ne_prolonge_pas_une_url(texte):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(texte) == texte


# Revue de sécurité du 17/11 : dans une phrase, un guillemet que rien n'a ouvert
# et qu'une lettre ou un chiffre suit aussitôt appartient au mot de passe.
@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        ('Connexion par http://temoin:123"x@hote.invalid puis rien', "Connexion par http://hote.invalid puis rien"),
        ('Voir http://te"moin:FAUX@hote.invalid ici', "Voir http://hote.invalid ici"),
        ("Voir http://temoin'x@hote.invalid/dav ici", "Voir http://hote.invalid/dav ici"),
    ],
)
def test_masquage_d_un_guillemet_non_ouvert_dans_une_phrase(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


# Sondes de la relecture 8 (interrompue faute de crédits Codex, 17/11/2026) :
# un jeton masqué dans un lien Markdown mangeait la parenthèse fermante et la
# suite de la ligne, un attribut HTML collé au suivant était mal lu.
@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        ("[Dossier](https://portail.invalid/?access_token=FICTIF)", "[Dossier](https://portail.invalid/?access_token=[REDACTED])"),
        (
            "|[Dossier](https://portail.invalid/?access_token=FICTIF)|contact@example.invalid|1500|",
            "|[Dossier](https://portail.invalid/?access_token=[REDACTED])|contact@example.invalid|1500|",
        ),
        ("Copier `https://portail.invalid/?token=FICTIF` puis continuer.", "Copier `https://portail.invalid/?token=[REDACTED]` puis continuer."),
        ("Voir (https://portail.invalid/?token=FICTIF), puis écrire.", "Voir (https://portail.invalid/?token=[REDACTED]), puis écrire."),
        ("Lien : https://portail.invalid/?token=FICTIF. Merci.", "Lien : https://portail.invalid/?token=[REDACTED]. Merci."),
        ("https://wiki.invalid/Page_(test)?token=FICTIF&vue=1", "https://wiki.invalid/Page_(test)?token=[REDACTED]&vue=1"),
        ("Voir https://wiki.invalid/Page_(test) et la suite", "Voir https://wiki.invalid/Page_(test) et la suite"),
        # Dans un attribut HTML, « &amp; » sépare les paramètres et « &#45; » fait partie de la valeur.
        (
            '<a href="https://portail.invalid/?access_token=FAUX&#45;suite&amp;vue=mois">Dossier</a>',
            '<a href="https://portail.invalid/?access_token=[REDACTED]&amp;vue=mois">Dossier</a>',
        ),
        (
            '<a href="https://portail.invalid/?vue=mois&amp;password=FAUX-secret">Dossier</a>',
            '<a href="https://portail.invalid/?vue=mois&amp;password=[REDACTED]">Dossier</a>',
        ),
    ],
)
def test_masquage_d_un_parametre_dans_un_lien_markdown_ou_html(entree, attendu):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(entree) == attendu


@pytest.mark.parametrize(
    "texte",
    [
        '<a href=" https://site.invalid"title="contact@example.invalid">Contact</a>',
        "<a href=' https://site.invalid'title='contact@example.invalid'>Contact</a>",
        '<img src="https://logo.invalid"alt="a@b.invalid">',
    ],
)
def test_masquage_d_un_attribut_html_colle_au_suivant(texte):
    from app.routers.data import _masquer_urls_export

    assert _masquer_urls_export(texte) == texte


# Revue de sécurité du 17/11 : raccourcir l'URL à sa fin apparente ne doit
# jamais laisser en clair un secret placé après.
@pytest.mark.parametrize(
    ("entree", "attendu"),
    [
        (
            "Voir https://portail.invalid/?token=ab)cd&password=FAUX-secret ici",
            "Voir https://portail.invalid/?token=[REDACTED]&password=[REDACTED] ici",
        ),
        (
            "[x](https://portail.invalid/?token=FICTIF&password=FAUX-secret)",
            "[x](https://portail.invalid/?token=[REDACTED]&password=[REDACTED])",
        ),
        ("Voir https://portail.invalid/?password=FAUX]secret ici", "Voir https://portail.invalid/?password=[REDACTED] ici"),
        ("Voir https://portail.invalid/?a=1)&password=FAUX-secret ici", "Voir https://portail.invalid/?a=1)&password=[REDACTED] ici"),
        ("| https://portail.invalid/?token=FICTIF|a=b|", "| https://portail.invalid/?token=[REDACTED]|a=b|"),
        (
            "Voir https://portail.invalid/?token=FICTIF|suite&password=FAUX-secret ici",
            "Voir https://portail.invalid/?token=[REDACTED]&password=[REDACTED] ici",
        ),
        (
            "| https://portail.invalid/?token=FICTIF|https://autre.invalid/?password=FAUX-secret|",
            # La suite porte un secret : rien n'est coupé, tout part avec la valeur masquée.
            "| https://portail.invalid/?token=[REDACTED]",
        ),
        ("Voir https://portail.invalid/?token=FICTIF|suite ici", "Voir https://portail.invalid/?token=[REDACTED] ici"),
        ("Voir https://portail.invalid/?token=FICTIF`suite ici", "Voir https://portail.invalid/?token=[REDACTED] ici"),
        ("Voir `https://portail.invalid/?token=FICTIF`&password=FAUX-secret ici", "Voir `https://portail.invalid/?token=[REDACTED]&password=[REDACTED] ici"),
    ],
)
def test_masquage_ne_laisse_aucun_secret_apres_la_fin_apparente_d_une_url(entree, attendu):
    from app.routers.data import _masquer_urls_export

    sortie = _masquer_urls_export(entree)
    assert "FAUX" not in sortie and "FICTIF" not in sortie
    assert sortie == attendu
