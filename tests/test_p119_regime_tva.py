"""P-119 (persona Claire, cycle 13) : une coach en franchise facture à 0 %,
mais aucun écran ne permettait de déclarer la franchise ; la mention légale
obligatoire ne pouvait donc pas s'imprimer (depuis B-1357, le PDF se borne à
« Aucune TVA facturée »).

Mentions relevées aux sources le 25/09/2026 :
- franchise : « TVA non applicable, art. 293 B du code général des impôts »
  (entreprendre.service-public.gouv.fr/vosdroits/F31808, mise à jour du
  11/08/2026) ;
- exonération : « la référence à la disposition pertinente du code général
  des impôts » (CGI, annexe II, art. 242 nonies A, I, 12°) ; formation
  professionnelle continue : CGI art. 261, 4, 4° a.
"""

import pytest
from app.services.invoice_pdf import InvoicePDFGenerator
from httpx import AsyncClient
from pypdf import PdfReader

FRANCHISE = "TVA non applicable, art. 293 B du code général des impôts"
FORMATION = "Exonération de TVA, art. 261, 4, 4° a du code général des impôts"


def _texte_du_pdf(tmp_path, *, regime: str | None, taux: float = 0.0, tva_applicable: bool = True) -> str:
    gen = InvoicePDFGenerator(output_dir=str(tmp_path))
    tva = round(100.0 * taux / 100, 2)
    invoice_data = {
        "invoice_number": f"FACT-P119-{regime}-{int(taux)}-{int(tva_applicable)}",
        "document_type": "facture", "tva_applicable": tva_applicable, "validite_jours": 30,
        "issue_date": "2026-09-25T00:00:00", "due_date": "2026-10-25T00:00:00", "status": "draft",
        "subtotal_ht": 100.0, "total_tax": tva, "total_ttc": 100.0 + tva, "notes": "", "legal_mentions": "",
        "lines": [{"description": "Séance de coaching", "quantity": 1, "unit_price_ht": 100.0,
                   "tva_rate": taux, "total_ht": 100.0, "total_ttc": 100.0 + tva}],
    }
    profil = {"name": "Claire Exemple", "company": "Claire Exemple Coaching", "address": "Lyon",
              "siren": "", "siret": "99988877900009", "code_ape": "", "tva_intra": ""}
    if regime is not None:
        profil["regime_tva"] = regime
    chemin = gen.generate_invoice_pdf(
        invoice_data=invoice_data,
        contact_data={"name": "Hélène Ménard", "company": "", "email": "", "phone": "", "address": ""},
        user_profile=profil,
    )
    return " ".join("".join(page.extract_text() for page in PdfReader(chemin).pages).split())


def test_franchise_declaree_imprime_la_mention_293_b(tmp_path):
    assert FRANCHISE in _texte_du_pdf(tmp_path, regime="franchise")


def test_exoneration_formation_imprime_sa_reference(tmp_path):
    texte = _texte_du_pdf(tmp_path, regime="exoneration_formation")
    assert FORMATION in texte
    assert "293 B" not in texte


def test_sans_regime_declare_le_pdf_se_borne_au_constat(tmp_path):
    texte = _texte_du_pdf(tmp_path, regime="normal")
    assert "Aucune TVA facturée" in texte
    assert "293 B" not in texte and "261" not in texte


def test_une_ligne_taxee_ne_se_dit_jamais_exoneree(tmp_path):
    texte = _texte_du_pdf(tmp_path, regime="franchise", taux=20.0)
    assert "293 B" not in texte
    assert "TVA incluse" in texte


def test_une_piece_non_assujettie_ecrit_la_mention_en_entier(tmp_path):
    assert FRANCHISE in _texte_du_pdf(tmp_path, regime=None, tva_applicable=False)


@pytest.mark.asyncio
async def test_le_regime_se_declare_dans_le_profil(client: AsyncClient):
    corps = {"name": "Claire Exemple", "regime_tva": "franchise"}
    reponse = await client.post("/api/config/profile", json=corps)
    assert reponse.status_code == 200
    assert reponse.json()["regime_tva"] == "franchise"
    relu = await client.get("/api/config/profile")
    assert relu.json()["regime_tva"] == "franchise"


@pytest.mark.asyncio
async def test_un_regime_inconnu_est_refuse(client: AsyncClient):
    reponse = await client.post("/api/config/profile", json={"name": "Claire", "regime_tva": "offshore"})
    assert reponse.status_code == 422


@pytest.mark.asyncio
async def test_l_import_de_therese_md_garde_le_regime_declare(db_session, tmp_path):
    """Même règle que B-1299 : le fichier ne dit rien du régime de TVA, il ne
    le remet donc pas à « normal »."""
    from app.services import user_profile as up

    await up.set_user_profile(
        db_session, up.UserProfile(name="Claire Exemple", regime_tva="franchise"), embed_in_qdrant=False,
    )
    fichier = tmp_path / "THERESE.md"
    fichier.write_text("**Owner** : Claire Exemple\n", encoding="utf-8")
    profil = await up.import_from_claude_md(db_session, str(fichier))
    assert profil.regime_tva == "franchise"
