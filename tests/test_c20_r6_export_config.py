"""Régressions de la passe 6 : règles d'export retenues en P-173."""

import json
from time import process_time

import pytest
from app.models.entities import Calendar, EmailAccount, Preference


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/data/export", "/api/config/export"])
@pytest.mark.parametrize("caractere", ["'", '"', "<", ">", "\\"])
@pytest.mark.parametrize("secret_avant", [False, True])
async def test_export_masque_les_parametres_sur_tout_le_champ_url(
    client, db_session, route, caractere, secret_avant,
):
    filtre = f"filtre=l{caractere}agenda"
    parametres = ["access_token=FICTIF", filtre] if secret_avant else [filtre, "access_token=FICTIF"]
    url = "https://agenda.invalid/dav?" + "&".join(parametres)
    attendu = url.replace("access_token=FICTIF", "access_token=[REDACTED]")
    db_session.add(Calendar(
        id="cal-r6-url", summary="Agenda", provider="caldav", caldav_url=url, remote_id=url,
    ))
    db_session.add(EmailAccount(id="mail-r6-url", email="a@b.invalid", imap_host=url, smtp_host=url))
    db_session.add(Preference(key="relais_config", value=json.dumps({"url": url})))
    await db_session.commit()

    reponse = await (client.get(route) if route == "/api/data/export" else client.post(route))
    assert reponse.status_code == 200
    export = reponse.json()
    agenda = next(c for c in export["calendars"] if c["id"] == "cal-r6-url")
    compte = next(c for c in export["email_accounts"] if c["id"] == "mail-r6-url")
    preference = next(p["value"] for p in export["preferences"] if p["key"] == "relais_config")
    assert agenda["caldav_url"] == attendu
    assert agenda["remote_id"] == attendu
    assert compte["imap_host"] == attendu
    assert compte["smtp_host"] == attendu
    assert json.loads(preference) == {"url": attendu}


def test_masquage_d_une_url_entiere_conserve_les_espaces_autour():
    from app.routers.data import _masquer_urls_export

    texte = " \thttps://agenda.invalid/dav?access_token=FICTIF\n  "
    assert _masquer_urls_export(texte) == texte.replace("FICTIF", "[REDACTED]")


@pytest.mark.parametrize("prefixe", ["https://hote.invalid/", "Voir "])
def test_recherche_des_urls_reste_lineaire_sur_des_suffixes_a_points(prefixe):
    """La reproduction vise la première passe ; sans URL, elle vise aussi la seconde.

    Le temps CPU isole la mesure de la charge des autres lots sur la machine.
    Le rapport tolère une marge, mais refuse le quadruplement quadratique.
    """
    from app.routers.data import _masquer_urls_export

    durees = []
    for taille in (64_000, 128_000):
        texte = prefixe + "a." * taille
        depart = process_time()
        sortie = _masquer_urls_export(texte)
        durees.append(process_time() - depart)
        assert sortie == texte
    petite, grande = durees
    assert grande < 3 * petite + 0.02, f"Coût non linéaire : {petite:.3f}s puis {grande:.3f}s"
    assert grande < 5, f"Recherche trop lente : {grande:.3f}s CPU"
