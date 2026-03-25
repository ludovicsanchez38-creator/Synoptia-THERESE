"""
THÉRÈSE v2 - Import Service (ICS + VCard)

Parse et importe des fichiers .ics (calendrier) et .vcf (contacts).
"""

import logging
from datetime import UTC

import vobject
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
            start_str = start_dt.isoformat()
            end_str = end_dt.isoformat()
        else:
            # S'assurer que c'est un datetime aware
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=UTC)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=UTC)
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
    text = content.decode("utf-8", errors="replace")
    contacts = []

    for vcard in vobject.readComponents(text):
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
            continue  # Pas de nom, skip

        # Organisation
        if hasattr(vcard, "org"):
            org_values = vcard.org.value
            if isinstance(org_values, list):
                contact["company"] = org_values[0] if org_values else ""
            else:
                contact["company"] = str(org_values)

        # Email
        if hasattr(vcard, "email"):
            contact["email"] = vcard.email.value

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

        # Ne garder que les contacts avec au moins un nom
        if contact.get("first_name") or contact.get("last_name"):
            contacts.append(contact)

    logger.info(f"Parsed {len(contacts)} contacts from VCF file")
    return contacts
