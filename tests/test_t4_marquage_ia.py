"""Les champs IA sont relus dans les fichiers livrés, sans changer leur contenu."""

import base64
import io
import json
from email import message_from_bytes
from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image, PngImagePlugin


def provenance():
    from app.services.marquage_ia import provenance_ia

    return provenance_ia("openai", "modele-test")


@pytest.mark.parametrize("extension", ["docx", "xlsx", "pptx", "pdf"])
def test_proprietes_du_document_reel(tmp_path, extension):
    from app.services.marquage_ia import marquer_document

    path = tmp_path / ("document." + extension)
    if extension == "docx":
        from docx import Document

        doc = Document()
        doc.add_paragraph("Contenu visible inchangé")
        doc.save(path)
    elif extension == "xlsx":
        from openpyxl import Workbook

        doc = Workbook()
        doc.active["A1"] = "Contenu visible inchangé"
        doc.save(path)
    elif extension == "pptx":
        from pptx import Presentation

        doc = Presentation()
        doc.slides.add_slide(doc.slide_layouts[0]).shapes.title.text = "Contenu visible inchangé"
        doc.save(path)
    else:
        from reportlab.pdfgen.canvas import Canvas

        doc = Canvas(str(path))
        doc.drawString(30, 30, "Contenu visible inchange")
        doc.save()
    champs = provenance()
    marquer_document(path, champs)
    if extension == "pdf":
        from pypdf import PdfReader

        pdf = PdfReader(path)
        assert json.loads(pdf.metadata["/ThereseIA"]) == champs
        assert "Contenu visible inchange" in pdf.pages[0].extract_text()
        assert b"trainedAlgorithmicMedia" in pdf.trailer["/Root"]["/Metadata"].get_data()
    else:
        with ZipFile(path) as archive:
            xml = archive.read("docProps/custom.xml").decode()
            for cle, valeur in champs.items():
                assert cle in xml and valeur in xml
            assert "custom-properties" in archive.read("[Content_Types].xml").decode()


def test_image_sans_marque_recoit_xmp_sans_changer_les_pixels():
    from app.services.marquage_ia import marquer_image

    out = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(out, format="PNG")
    avant = out.getvalue()
    apres = marquer_image(avant, provenance())
    assert "trainedAlgorithmicMedia" in Image.open(io.BytesIO(apres)).info["XML:com.adobe.xmp"]
    assert Image.open(io.BytesIO(avant)).tobytes() == Image.open(io.BytesIO(apres)).tobytes()


def test_image_deja_marquee_reste_identique_octet_pour_octet():
    from app.services.marquage_ia import marquer_image

    out = io.BytesIO()
    meta = PngImagePlugin.PngInfo()
    meta.add(b"caBX", b"c2pa-manifeste-factice")
    Image.new("RGB", (4, 4), "red").save(out, format="PNG", pnginfo=meta)
    original = out.getvalue()
    assert marquer_image(original, provenance()) == original


def test_mime_gmail_ia_et_mail_manuel():
    from app.services.gmail_service import GmailService

    champs = provenance()
    raw = GmailService._encoder_message(
        ["dest@example.test"], "Sujet", "Texte visible", ai_provenance=champs
    )
    message = message_from_bytes(base64.urlsafe_b64decode(raw))
    assert "genere" in str(message["X-Therese-IA"])
    assert "openai/modele-test" in str(message["X-Therese-IA"])
    manual = GmailService._encoder_message(["dest@example.test"], "Sujet", "Texte visible")
    assert message_from_bytes(base64.urlsafe_b64decode(manual))["X-Therese-IA"] is None


def test_mime_smtp_brouillon_ia():
    from app.services.email.base_provider import SendEmailRequest
    from app.services.email.imap_smtp_provider import ImapSmtpProvider

    provider = ImapSmtpProvider.__new__(ImapSmtpProvider)
    provider._email = "source@example.test"
    request = SendEmailRequest(
        to=["dest@example.test"], subject="Sujet", body="Texte visible", ai_provenance=provenance()
    )
    message = provider._message_du_brouillon(request)
    assert "genere" in str(message["X-Therese-IA"])
    assert message.get_payload()[0].get_payload(decode=True) == b"Texte visible"


@pytest.mark.asyncio
async def test_image_garde_fournisseur_modele_en_base(client, tmp_path):
    from app.models.database import get_sync_session
    from app.models.entities import AIGeneration
    from app.services.image_generator import ImageGeneratorService, ImageProvider

    out = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(out, format="PNG")
    service = ImageGeneratorService(tmp_path)
    result = service._save_image(out.getvalue(), ImageProvider.OPENAI.value, "description de test")
    with get_sync_session() as session:
        record = session.get(AIGeneration, result.id)
        assert (record.provider, record.model) == ("openai", "gpt-image-2")
    assert ImageGeneratorService(tmp_path).get_image(result.id).provider == "openai"


@pytest.mark.asyncio
async def test_registre_marque_le_pdf_livre(tmp_path):
    from app.services.skills.base import SkillExecuteRequest
    from app.services.skills.pdf_generator import PdfSkill
    from app.services.skills.registry import SkillsRegistry
    from pypdf import PdfReader

    registry = SkillsRegistry()
    skill = PdfSkill(tmp_path)
    registry.register(skill)
    response = await registry.execute(
        skill.skill_id,
        SkillExecuteRequest(prompt="Rédige un document", context={"_ai_provenance": provenance()}),
        "# Document\n\nUn contenu rédigé pour le test du circuit de livraison.",
    )
    assert response.success
    artifact = registry.get_file(response.file_id)
    assert "/ThereseIA" in PdfReader(artifact.file_path).metadata
    assert response.file_size == artifact.file_path.stat().st_size


def test_facture_saisie_au_formulaire_non_marquee(tmp_path):
    from app.services.invoice_pdf import InvoicePDFGenerator
    from pypdf import PdfReader

    data = {
        "invoice_number": "FACT-TEST",
        "document_type": "facture",
        "status": "draft",
        "issue_date": "2026-10-29",
        "due_date": "2026-11-29",
        "subtotal_ht": 10,
        "total_tax": 0,
        "total_ttc": 10,
        "tva_applicable": False,
        "lines": [
            {
                "description": "Service saisi",
                "quantity": 1,
                "unit_price_ht": 10,
                "tva_rate": 0,
                "total_ht": 10,
                "total_ttc": 10,
            }
        ],
    }
    path = InvoicePDFGenerator(str(tmp_path)).generate_invoice_pdf(
        data, {"name": "Client test"}, {"name": "Émetteur test"}
    )
    reader = PdfReader(path)
    assert "/ThereseIA" not in reader.metadata
    assert b"trainedAlgorithmicMedia" not in Path(path).read_bytes()


@pytest.mark.parametrize("format", ["JPEG", "WEBP"])
def test_image_autres_formats_sans_recompression(format):
    from app.services.marquage_ia import marquer_image

    original = io.BytesIO()
    Image.new("RGB", (7, 5), "blue").save(original, format=format)
    marque = marquer_image(original.getvalue(), provenance())
    avant, apres = Image.open(io.BytesIO(original.getvalue())), Image.open(io.BytesIO(marque))
    assert avant.tobytes() == apres.tobytes()
    assert b"trainedAlgorithmicMedia" in marque


@pytest.mark.asyncio
async def test_provenance_mail_liee_au_compte_et_absente_pour_texte_manuel(client, db_session):
    from app.services.provenance_store import ajouter_generation, provenance_mail
    from fastapi import HTTPException

    champs = provenance()
    identifiant = ajouter_generation(db_session, "email", "compte-a", champs)
    await db_session.commit()
    assert await provenance_mail(db_session, identifiant, "compte-a") == champs
    assert await provenance_mail(db_session, None, "compte-a") is None
    with pytest.raises(HTTPException) as exc:
        await provenance_mail(db_session, identifiant, "compte-b")
    assert exc.value.status_code == 422


def test_migration_provenance_preserve_les_mails_existants(tmp_path):
    from importlib.util import module_from_spec, spec_from_file_location

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect, text

    spec = spec_from_file_location(
        "t4marquage", Path("src/backend/alembic/versions/t4marque02_provenance_ia.py")
    )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine(f"sqlite:///{tmp_path / 'mails.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE email_messages (id TEXT, body_plain TEXT)"))
        conn.execute(text("INSERT INTO email_messages VALUES ('mail-a', 'Texte conservé')"))
        module.op = Operations(MigrationContext.configure(conn))
        module.upgrade()
        module.upgrade()
        assert "ai_generations" in inspect(conn).get_table_names()
        assert conn.execute(
            text("SELECT body_plain, ai_generation_id FROM email_messages")
        ).one() == ("Texte conservé", None)
