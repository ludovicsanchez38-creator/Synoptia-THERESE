"""B1 — cesser de promettre un envoi qui n'existe pas.

Campagne dix personas : l'artisan fait son devis et ne peut pas l'envoyer.
`POST /invoices/{id}/send` répond 501 en toutes circonstances.

Décision de la relecture de design : NE PAS implémenter l'envoi dans ce lot.
« Il faut attacher le PDF, vérifier que le contact a un e-mail, et ne poser
`sent` qu'après acceptation du fournisseur. Un échec Gmail sans PJ enverrait un
devis SANS le devis. Pire que le 501. » Deux jours minimum, et ce n'est pas la
rupture vécue.

Ce que B fait : retirer la promesse restante. Le chat orientait encore vers
« la vue Facturation » pour envoyer — or cette vue n'envoie pas non plus. Le
vrai repli existe et fonctionne : télécharger le PDF, l'envoyer par ses propres
moyens, puis marquer la facture « Envoyée » à la main dans le formulaire.
"""


class TestLeChatNOrientePlusVersUneVueQuiNEnvoiePas:
    def test_le_guidage_de_l_outil_ne_promet_pas_la_vue_facturation(self):
        from app.services.workspace_tools import SEARCH_INVOICES_TOOL

        description = SEARCH_INVOICES_TOOL["function"]["description"]
        assert "oriente vers la vue Facturation" not in description, (
            "la vue Facturation n'envoie pas non plus : l'orientation est un "
            "cul-de-sac de plus"
        )
        assert "IMPOSSIBLE" in description or "impossible" in description, (
            "le modèle doit continuer de savoir que l'envoi n'existe pas"
        )

    def test_le_resultat_de_recherche_dit_le_vrai_repli(self):
        import inspect

        from app.services import workspace_tools

        source = inspect.getsource(workspace_tools._search_invoices)
        assert "ouvre la vue Facturation, sélectionne le" not in source, (
            "ce texte décrit un parcours d'envoi qui n'aboutit pas"
        )

    def test_la_route_d_envoi_dit_ce_qu_il_faut_faire(self):
        """Le 501 reste, mais son message doit être actionnable."""
        import inspect

        from app.routers import invoices

        source = inspect.getsource(invoices.send_invoice_by_email)
        assert "501" in source
        assert "Télécharge le PDF" in source or "telecharge" in source.lower()
