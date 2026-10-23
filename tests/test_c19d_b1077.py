from app.services.invoice_pdf import libelle_statut_pdf


def test_avoir_en_retard_traduit_sans_changer_les_regles_de_statut():
    assert libelle_statut_pdf('overdue', 'avoir') == 'En retard'


def test_rejeu_dix_statuts_apres_correctif():
    for statut, type_document, attendu in [
        ('OVERDUE', 'avoir', 'En retard'), (' overdue ', 'avoir', 'En retard'),
        ('draft', 'avoir', 'Brouillon'), ('sent', 'avoir', 'Émis'),
        ('paid', 'avoir', 'Remboursé'), ('cancelled', 'avoir', 'Annulé'),
        ('overdue', 'facture', 'En retard'), ('sent', 'facture', 'Envoyée'),
        ('sent', 'devis', 'Envoyé'), ('accepted', 'devis', 'Accepté'),
    ]:
        assert libelle_statut_pdf(statut, type_document) == attendu
