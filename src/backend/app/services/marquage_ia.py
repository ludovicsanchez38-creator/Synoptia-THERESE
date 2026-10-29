"""Marquage de provenance non signé ; voir docs/marquage-ia.md."""

import io
import json
import re
import struct
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from app import __version__

NS = "https://synoptia.fr/ns/therese/ia/1.0/"
IPTC = "http://iptc.org/std/Iptc4xmpExt/2008-02-29/"
SOURCE = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


def provenance_ia(provider: str, model: str) -> dict[str, str]:
    # Les seuls éléments variables sont des identifiants techniques, jamais un prompt.
    def identifiant(value: str) -> str:
        if not re.fullmatch(r"[\w./:-]{1,160}", value, flags=re.ASCII):
            raise ValueError("Identifiant de provenance IA invalide")
        return value

    return {
        "ia_generee": "oui",
        "systeme": f"THÉRÈSE {__version__}",
        "fournisseur_modele": f"{identifiant(provider)}/{identifiant(model)}",
        "date": datetime.now(UTC).isoformat(),
    }


def provenance_service(service: Any) -> dict[str, str]:
    # Le service est celui de cette génération, même si le choix global change ensuite.
    return provenance_ia(service.config.provider.value, service.config.model)


def xmp_ia(champs: dict[str, str], existant: bytes | None = None) -> bytes:
    ET.register_namespace("rdf", RDF)
    ET.register_namespace("therese", NS)
    ET.register_namespace("Iptc4xmpExt", IPTC)
    root = ET.fromstring(existant) if existant else ET.Element("{adobe:ns:meta/}xmpmeta")
    rdf = root.find(f".//{{{RDF}}}RDF")
    if rdf is None:
        rdf = ET.SubElement(root, f"{{{RDF}}}RDF")
    description = ET.SubElement(rdf, f"{{{RDF}}}Description", {f"{{{RDF}}}about": ""})
    for key, value in champs.items():
        ET.SubElement(description, f"{{{NS}}}{key}").text = value
    ET.SubElement(description, f"{{{IPTC}}}DigitalSourceType").text = SOURCE
    return bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def marquer_document(path: Path, champs: dict[str, str] | None) -> None:
    if not champs:
        return  # Texte humain, simple conversion ou facture au formulaire.
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        reader = PdfReader(io.BytesIO(path.read_bytes()))
        writer = PdfWriter(clone_from=reader)
        writer.add_metadata({"/ThereseIA": json.dumps(champs, ensure_ascii=False)})
        ancien = cast(DictionaryObject, reader.trailer["/Root"]).get("/Metadata")
        xmp = xmp_ia(champs, ancien.get_object().get_data() if ancien else None)
        stream = DecodedStreamObject()
        stream.set_data(xmp)
        stream.update(
            {
                NameObject("/Type"): NameObject("/Metadata"),
                NameObject("/Subtype"): NameObject("/XML"),
            }
        )
        writer._root_object[NameObject("/Metadata")] = writer._add_object(stream)
        out = io.BytesIO()
        writer.write(out)
        path.write_bytes(out.getvalue())
        return
    if path.suffix.lower() not in (".docx", ".xlsx", ".pptx"):
        return
    custom = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
    vt = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
    rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    content = "http://schemas.openxmlformats.org/package/2006/content-types"
    type_rel = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
    )
    with ZipFile(path) as archive:
        entries = {entry.filename: (entry, archive.read(entry)) for entry in archive.infolist()}
    root = (
        ET.fromstring(entries["docProps/custom.xml"][1])
        if "docProps/custom.xml" in entries
        else ET.Element(f"{{{custom}}}Properties")
    )
    for prop in list(root):
        if prop.get("name") in {f"therese:{key}" for key in champs}:
            root.remove(prop)
    pid = max([int(p.get("pid", "1")) for p in root] or [1]) + 1
    for key, value in champs.items():
        prop = ET.SubElement(
            root,
            f"{{{custom}}}property",
            {
                "fmtid": "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}",
                "pid": str(pid),
                "name": f"therese:{key}",
            },
        )
        ET.SubElement(prop, f"{{{vt}}}lpwstr").text = value
        pid += 1
    types = ET.fromstring(entries["[Content_Types].xml"][1])
    if not any(p.get("PartName") == "/docProps/custom.xml" for p in types):
        ET.SubElement(
            types,
            f"{{{content}}}Override",
            {
                "PartName": "/docProps/custom.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.custom-properties+xml",
            },
        )
    relations = ET.fromstring(entries["_rels/.rels"][1])
    if not any(p.get("Type") == type_rel for p in relations):
        ident = "rIdThereseIA"
        while any(p.get("Id") == ident for p in relations):
            ident += "x"
        ET.SubElement(
            relations,
            f"{{{rel}}}Relationship",
            {"Id": ident, "Type": type_rel, "Target": "docProps/custom.xml"},
        )
    replacements = {
        "docProps/custom.xml": root,
        "[Content_Types].xml": types,
        "_rels/.rels": relations,
    }
    out = io.BytesIO()
    with ZipFile(out, "w", compression=ZIP_DEFLATED) as archive:
        for name, (entry, data) in entries.items():
            if name not in replacements:
                archive.writestr(entry, data)
        for name, xml in replacements.items():
            archive.writestr(name, ET.tostring(xml, encoding="utf-8", xml_declaration=True))
    path.write_bytes(out.getvalue())


def deja_marquee(data: bytes) -> bool:
    # Conservateur : ne pas réécrire un manifeste dont on ne vérifie pas la signature.
    return any(
        marque in data
        for marque in (
            b"c2pa",
            b"C2PA",
            b"caBX",
            b"trainedAlgorithmicMedia",
            b"compositeWithTrainedAlgorithmicMedia",
        )
    )


def marquer_image(data: bytes, champs: dict[str, str]) -> bytes:
    if deja_marquee(data):
        return data
    xmp_key = b"XML:com.adobe.xmp"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        chunks = []
        pos = 8
        ancien = None
        while pos + 12 <= len(data):
            length = struct.unpack(">I", data[pos : pos + 4])[0]
            kind, payload = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
            if pos + 12 + length > len(data):
                raise ValueError("Image PNG tronquée")
            if kind == b"iTXt" and payload.startswith(xmp_key + b"\x00"):
                rest = payload[len(xmp_key) + 1 :]
                compressed = rest[0]
                text = rest[2:].split(b"\x00", 2)[2]
                ancien = zlib.decompress(text) if compressed else text
            else:
                chunks.append((kind, data[pos : pos + 12 + length]))
            pos += 12 + length
        payload = xmp_key + b"\x00\x00\x00\x00\x00" + xmp_ia(champs, ancien)
        kind = b"iTXt"
        chunk = (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload))
        )
        result = bytearray(data[:8])
        inserted = False
        for kind, raw in chunks:
            if kind in (b"IDAT", b"IEND") and not inserted:
                result.extend(chunk)
                inserted = True
            result.extend(raw)
        if not inserted:
            raise ValueError("Image PNG sans données")
        return bytes(result)
    if data.startswith(b"\xff\xd8"):
        prefix = b"http://ns.adobe.com/xap/1.0/\x00"
        pos = 2
        segments = []
        ancien = None
        while pos + 4 <= len(data) and data[pos : pos + 2] not in (b"\xff\xda", b"\xff\xd9"):
            length = int.from_bytes(data[pos + 2 : pos + 4], "big")
            if length < 2 or pos + 2 + length > len(data):
                raise ValueError("Image JPEG tronquée")
            segment = data[pos : pos + 2 + length]
            if segment[:2] == b"\xff\xe1" and segment[4:].startswith(prefix):
                ancien = segment[4 + len(prefix) :]
            else:
                segments.append(segment)
            pos += 2 + length
        payload = prefix + xmp_ia(champs, ancien)
        return (
            data[:2]
            + b"".join(segments)
            + b"\xff\xe1"
            + (len(payload) + 2).to_bytes(2, "big")
            + payload
            + data[pos:]
        )
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        from PIL import Image

        chunks = []
        pos = 12
        ancien = None
        while pos + 8 <= len(data):
            kind = data[pos : pos + 4]
            size = int.from_bytes(data[pos + 4 : pos + 8], "little")
            payload = data[pos + 8 : pos + 8 + size]
            if kind == b"XMP ":
                ancien = payload
            else:
                if kind == b"VP8X":
                    payload = bytes([payload[0] | 4]) + payload[1:]
                chunks.append((kind, payload))
            pos += 8 + size + size % 2
        if not any(k == b"VP8X" for k, _ in chunks):
            with Image.open(io.BytesIO(data)) as im:
                w, h = im.size
                flags = 4 | (16 if "A" in im.getbands() else 0)
            chunks.insert(
                0,
                (
                    b"VP8X",
                    bytes([flags, 0, 0, 0])
                    + (w - 1).to_bytes(3, "little")
                    + (h - 1).to_bytes(3, "little"),
                ),
            )
        chunks.append((b"XMP ", xmp_ia(champs, ancien)))
        body = b"WEBP" + b"".join(
            k + len(p).to_bytes(4, "little") + p + (b"\x00" if len(p) % 2 else b"")
            for k, p in chunks
        )
        return b"RIFF" + len(body).to_bytes(4, "little") + body
    raise ValueError("Format d’image non pris en charge pour le marquage IA")


def entete_ia(champs: dict[str, str] | None) -> str | None:
    if not champs:
        return None
    # ASCII pour traverser MIME sans encodage ambigu des paramètres.
    systeme = champs["systeme"].replace("THÉRÈSE ", "THERESE/")
    valeurs = [systeme, champs["fournisseur_modele"], champs["date"]]
    if any("\r" in v or "\n" in v or ";" in v for v in valeurs):
        raise ValueError("Provenance MIME invalide")
    return f"genere; ia_generee=oui; systeme={systeme}; fournisseur_modele={valeurs[1]}; date={valeurs[2]}"


class TexteIA(str):
    """Texte compatible avec les appelants historiques, avec provenance interne."""

    provenance: dict[str, str]

    def __new__(cls, texte: str, champs: dict[str, str]) -> "TexteIA":
        instance = super().__new__(cls, texte)
        instance.provenance = champs
        return instance
