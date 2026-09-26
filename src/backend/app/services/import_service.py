"""
THÉRÈSE v2 - Import Service (ICS + VCard)

Parse et importe des fichiers .ics (calendrier) et .vcf (contacts).
"""

import logging
from typing import Any

import vobject
from app.services.calendar.base_provider import allday_end_from_wire
from app.services.civil_time import PARIS
from app.services.crm_import import _sanitize_field
from icalendar import Calendar

logger = logging.getLogger(__name__)


def parse_ics(content: bytes) -> list[dict]:
    """
    Parse un fichier .ics et retourne une liste d'événements.

    Returns:
        Liste de dicts avec les champs : summary, description, location,
        start, end, all_day, attendees, recurrence, status
    """
    cal = Calendar.from_ical(content)
    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart = component.get("dtstart")
        dtend = component.get("dtend")

        if not dtstart:
            continue

        start_dt = dtstart.dt
        end_dt = dtend.dt if dtend else start_dt

        # Détecter all-day (date vs datetime)
        all_day = not hasattr(start_dt, "hour")

        # Convertir en datetime si c'est une date
        if all_day:
            # BUG-144 (F4 revue) : DTEND est EXCLUSIF dans ICS (RFC 5545),
            # l'app stocke une fin INCLUSIVE. Sans DTEND, l'événement dure
            # un seul jour (end_dt retombe déjà sur start_dt).
            if dtend is not None:
                end_dt = allday_end_from_wire(start_dt, end_dt)
            start_str = start_dt.isoformat()
            end_str = end_dt.isoformat()
        else:
            # B-1486 : l'agenda local range une heure murale de Paris sans
            # fuseau (B-275), et SQLite jette le décalage. Un instant daté
            # (Z ou TZID) est donc ramené à Paris ; une heure flottante
            # (RFC 5545 : l'heure du lieu) reste telle quelle.
            if start_dt.tzinfo is not None:
                start_dt = start_dt.astimezone(PARIS).replace(tzinfo=None)
            if end_dt.tzinfo is not None:
                end_dt = end_dt.astimezone(PARIS).replace(tzinfo=None)
            start_str = start_dt.isoformat()
            end_str = end_dt.isoformat()

        # Participants
        attendees_list = []
        raw_attendees = component.get("attendee")
        if raw_attendees:
            if not isinstance(raw_attendees, list):
                raw_attendees = [raw_attendees]
            for att in raw_attendees:
                email = str(att).replace("mailto:", "").replace("MAILTO:", "")
                if email:
                    attendees_list.append(email)

        # Récurrence
        rrule = component.get("rrule")
        recurrence = None
        if rrule:
            recurrence = [f"RRULE:{rrule.to_ical().decode()}"]

        events.append({
            "summary": str(component.get("summary", "Sans titre")),
            "description": str(component.get("description", "")) or None,
            "location": str(component.get("location", "")) or None,
            "start": start_str,
            "end": end_str,
            "all_day": all_day,
            "attendees": attendees_list,
            "recurrence": recurrence,
            "status": str(component.get("status", "confirmed")).lower(),
            "uid": str(component.get("uid", "")),
        })

    logger.info(f"Parsed {len(events)} events from ICS file")
    return events


def parse_vcf(content: bytes) -> list[dict]:
    """
    Parse un fichier .vcf (VCard) et retourne une liste de contacts.

    Returns:
        Liste de dicts avec les champs : first_name, last_name, company,
        email, phone, address, notes
    """
    return parse_vcf_avec_ecarts(content)[0]


def parse_vcf_avec_ecarts(content: bytes) -> tuple[list[dict[str, Any]], list[str], int]:
    """Les contacts lus, ce qui a été écarté (en clair) et le nombre de cartes.

    B-1380 : une carte sans nom disparaissait avant tout comptage, et une
    adresse douteuse était vidée en silence ; l'import disait « terminé » sans
    dire ce qu'il avait écarté.
    """
    text = content.decode("utf-8", errors="replace")
    contacts = []
    ecartees: list[str] = []
    nb_cartes = 0

    for numero, vcard in enumerate(vobject.readComponents(text), start=1):
        nb_cartes = numero
        contact = {}

        # Nom
        if hasattr(vcard, "n"):
            n = vcard.n.value
            contact["first_name"] = n.given or ""
            contact["last_name"] = n.family or ""
        elif hasattr(vcard, "fn"):
            parts = vcard.fn.value.split(" ", 1)
            contact["first_name"] = parts[0]
            contact["last_name"] = parts[1] if len(parts) > 1 else ""
        else:
            ecartees.append(f"carte n° {numero} écartée : sans nom")
            continue

        # Organisation
        if hasattr(vcard, "org"):
            org_values = vcard.org.value
            if isinstance(org_values, list):
                contact["company"] = org_values[0] if org_values else ""
            else:
                contact["company"] = str(org_values)

        # Email
        if hasattr(vcard, "email"):
            # B-1074 : une adresse double ou douteuse n'est pas importée ; la
            # fiche l'est, sans adresse.
            from app.models.schemas import adresse_unique_valide

            valeur = str(vcard.email.value or "").strip()
            contact["email"] = valeur if adresse_unique_valide(valeur) else None
            if valeur and contact["email"] is None:
                ecartees.append(
                    f"carte n° {numero} : adresse e-mail « {valeur} » illisible, non importée"
                )

        # Téléphone
        if hasattr(vcard, "tel"):
            contact["phone"] = vcard.tel.value

        # Adresse
        if hasattr(vcard, "adr"):
            adr = vcard.adr.value
            parts = [
                adr.street or "",
                adr.code or "",
                adr.city or "",
                adr.country or "",
            ]
            contact["address"] = ", ".join(p for p in parts if p)

        # Notes
        if hasattr(vcard, "note"):
            contact["notes"] = vcard.note.value

        # B-054 : la VCard est un fichier tiers, au même titre qu'un CSV. Les
        # deux routes qui appellent parse_vcf posaient ces valeurs directement
        # dans Contact(...) sans jamais passer par la neutralisation SEC-017
        # qu'applique le chemin CSV/Excel/JSON. Un `=HYPERLINK(...)` importé
        # ici redevenait une formule active au premier export tableur.
        # Neutraliser à la sortie du parseur ferme les DEUX routes d'un coup.
        contact = {
            champ: _sanitize_field(valeur, champ) for champ, valeur in contact.items()
        }

        # Ne garder que les contacts avec au moins un nom
        if contact.get("first_name") or contact.get("last_name"):
            contacts.append(contact)
        else:
            ecartees.append(f"carte n° {numero} écartée : sans nom")

    logger.info(f"Parsed {len(contacts)} contacts from VCF file")
    return contacts, ecartees, nb_cartes


def resume_des_ecarts(ecartees: list[str]) -> str:
    """B-1380 : la phrase qui suit le bilan d'un import vCard."""
    cartes = sum(1 for e in ecartees if "écartée" in e)
    adresses = len(ecartees) - cartes
    morceaux = []
    if cartes:
        morceaux.append(f"{cartes} carte{'s' if cartes > 1 else ''} écartée{'s' if cartes > 1 else ''} (sans nom)")
    if adresses:
        morceaux.append(
            f"{adresses} adresse{'s' if adresses > 1 else ''} e-mail illisible{'s' if adresses > 1 else ''} non importée{'s' if adresses > 1 else ''}"
        )
    return ", ".join(morceaux)
