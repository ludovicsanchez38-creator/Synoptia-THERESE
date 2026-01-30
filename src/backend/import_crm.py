#!/usr/bin/env python3
"""
Import CRM data from Google Sheets to THÉRÈSE v2
"""

import requests
import json

# Les données récupérées depuis Google Sheets
crm_data = [
    {"Nom": "MCPS", "Entreprise": "MCPS", "Email": "contact@mc-libreveil.fr", "Tel": "682621306", "Stage": "active", "Score": 95, "Tags": "micro-creche,client-payant"},
    {"Nom": "Perinne Sanchez", "Entreprise": "MCPS", "Email": "perrine.sanchez@live.fr", "Tel": "682621306", "Stage": "active", "Score": 95, "Tags": "micro-creche"},
    {"Nom": "Denis Miniconi", "Entreprise": "TOOGGY", "Email": "denis.miniconi@gmail.com", "Tel": "687143886", "Stage": "active", "Score": 100, "Tags": "Claude code,probono"},
    {"Nom": "Pierre Monvoisin", "Entreprise": "TOOGGY", "Email": "monvoisin.pierre38@gmail.com", "Tel": "634012920", "Stage": "active", "Score": 100, "Tags": "claude code,probono"},
    {"Nom": "Michel Sanchez", "Entreprise": "TOOGGY", "Email": "michel.sanchez02061961@gmail.com", "Tel": "", "Stage": "active", "Score": 100, "Tags": "claude code,probono"},
    {"Nom": "Yoan Rolin", "Entreprise": "TOOGGY", "Email": "yoan.rolin@gmail.com", "Tel": "645513877", "Stage": "active", "Score": 100, "Tags": "claude code,probono"},
    {"Nom": "PROFILSUCCESS", "Entreprise": "PROFILSUCCESS", "Email": "profilage@agi.business", "Tel": "679339368", "Stage": "active", "Score": 100, "Tags": "partenaire,formation,qualiopi"},
    {"Nom": "Eric Montmureau", "Entreprise": "PROFILSUCCESS", "Email": "profilage@agi.business", "Tel": "679339368", "Stage": "active", "Score": 100, "Tags": "formation,decision-maker,qualiopi"},
    {"Nom": "Sophie Montmurreau", "Entreprise": "PROFILSUCCESS", "Email": "sophie@agi.business", "Tel": "625047006", "Stage": "proposition", "Score": 25, "Tags": "formation"},
    {"Nom": "Denis Leymas", "Entreprise": "PROFILSUCCESS", "Email": "denis.leymas@profilsuccess.com", "Tel": "686585640", "Stage": "active", "Score": 100, "Tags": "formation"},
    {"Nom": "Melanie Montmurreau", "Entreprise": "PROFILSUCCESS", "Email": "", "Tel": "", "Stage": "proposition", "Score": 45, "Tags": "coaching,formation,leadership,DISC,FORGER-cadeau-livre"},
    {"Nom": "Alban Montreuil", "Entreprise": "NEW DYNAMIC / MAD INSTITUTE", "Email": "alban.montreuil@gmail.com", "Tel": "635035655", "Stage": "active", "Score": 100, "Tags": "coaching,formation,leadership,DISC,probono"},
    {"Nom": "Catherine Roche", "Entreprise": "", "Email": "catherinemariemorgane@gmail.com", "Tel": "650166797", "Stage": "delivery", "Score": 25, "Tags": "coaching,formation,qualiopi,probono"},
    {"Nom": "Estelle Heninger", "Entreprise": "MAD INSTITUTE", "Email": "estelle@agir-sens.fr", "Tel": "669027722", "Stage": "discovery", "Score": 20, "Tags": "coaching,DISC,international"},
    {"Nom": "CAPEB Alpes Durance", "Entreprise": "CAPEB", "Email": "", "Tel": "", "Stage": "active", "Score": 85, "Tags": "partenaire,formation,batiment,qualiopi,artisans"},
    {"Nom": "Stephane Paris", "Entreprise": "CAPEB Alpes Durance", "Email": "stephane@capeb0405.fr", "Tel": "631077460", "Stage": "signature", "Score": 0, "Tags": "decision-maker,formation"},
    {"Nom": "Stephanie", "Entreprise": "CAPEB", "Email": "stephanie@capeb0405.fr", "Tel": "667452672", "Stage": "signature", "Score": 0, "Tags": ""},
    {"Nom": "Julien", "Entreprise": "CAPEB", "Email": "", "Tel": "", "Stage": "signature", "Score": 0, "Tags": ""},
    {"Nom": "Laurent", "Entreprise": "CAPEB", "Email": "", "Tel": "", "Stage": "signature", "Score": 0, "Tags": ""},
    {"Nom": "Yoan Sartre", "Entreprise": "Lebonrevenu", "Email": "", "Tel": "", "Stage": "discovery", "Score": 65, "Tags": "remuneration,dirigeants,patrimoine,auteur"},
    {"Nom": "Jacques Bardouin", "Entreprise": "Pèpinière de Haute Provence", "Email": "jacques@pdhp.fr", "Tel": "672091833", "Stage": "proposition", "Score": 100, "Tags": "automation,agent"},
    {"Nom": "Krumsh Barclank", "Entreprise": "TEST MAIL", "Email": "krumshbarclank@hotmail.com", "Tel": "650333807", "Stage": "archive", "Score": 100, "Tags": "TEST"},
    {"Nom": "SYNOPTIA", "Entreprise": "SYNOPTIA", "Email": "ludo@synoptia.fr", "Tel": "650333807", "Stage": "active", "Score": 100, "Tags": "MOI MEME"},
    {"Nom": "TOOGGY", "Entreprise": "TOOGGY", "Email": "undifined@live.fr", "Tel": "650333807", "Stage": "active", "Score": 100, "Tags": "App react"},
    {"Nom": "Gilles ROBAUT", "Entreprise": "Generali", "Email": "lesrobauts@gmail.com", "Tel": "625918322", "Stage": "contact", "Score": 20, "Tags": "Initiation"},
    {"Nom": "WITTMANN France", "Entreprise": "WITTMANN France", "Email": "pierre.monvoisin@free.fr", "Tel": "606060606", "Stage": "contact", "Score": 25, "Tags": "Agent IA"},
    {"Nom": "Célia Galas", "Entreprise": "Célia Galas", "Email": "galas.celia@gmail.com", "Tel": "623614959", "Stage": "active", "Score": 100, "Tags": "LinkedIn,FORGER-livre"},
    {"Nom": "Sophia El Gourmate", "Entreprise": "ADEOS Formations", "Email": "sophia.el-gourmate@adeos-formations.com", "Tel": "469647207", "Stage": "active", "Score": 85, "Tags": "formation,IA,formateur-externe,valence"},
    {"Nom": "Pierre Heninger", "Entreprise": "DAF (confidentiel)", "Email": "", "Tel": "", "Stage": "active", "Score": 100, "Tags": "DAF,Excel-expert,formation-IA,claude-code,FORGER-livre"},
    {"Nom": "Bertrand Flutet", "Entreprise": "Axene", "Email": "https://www.linkedin.com/in/bertrand-flutet-axene-805a01a5/", "Tel": "6098460", "Stage": "contact", "Score": 100, "Tags": "IA"},
    {"Nom": "Bruno LE CORRE", "Entreprise": "Renault TRUCKS", "Email": "b.me-corre@azur-trucks.com", "Tel": "647254635", "Stage": "contact", "Score": 100, "Tags": ""},
    {"Nom": "Michel Pucheu", "Entreprise": "Initiative", "Email": "michel.pucheu@club-internet.fr", "Tel": "662466628", "Stage": "contact", "Score": 95, "Tags": "EIGHT commission 20%"},
    {"Nom": "Sebastien Pichon", "Entreprise": "ARGOS", "Email": "argos@argos-controle.fr", "Tel": "623652703", "Stage": "contact", "Score": 95, "Tags": "Bureau d'étude,administratif"},
    {"Nom": "Fabrice HECQUET", "Entreprise": "M2i Formation", "Email": "f.hecquet@m2iformation.fr", "Tel": "60000001", "Stage": "contact", "Score": 95, "Tags": "Formation,claude code."},
    {"Nom": "Charline", "Entreprise": "", "Email": "", "Tel": "", "Stage": "contact", "Score": 50, "Tags": ""},
    {"Nom": "Jean-Marie VANDEPUT", "Entreprise": "Hydro-Group", "Email": "jmv@hydro-group.com", "Tel": "", "Stage": "contact", "Score": 90, "Tags": "Automatisation,sécurité/robustesse"},
]

API_URL = "http://localhost:8000/api/memory/contacts"

def import_contacts():
    """Import contacts to THÉRÈSE v2"""
    created = 0
    skipped = 0

    for contact_data in crm_data:
        # Extraire prénom et nom
        full_name = contact_data["Nom"]
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if len(name_parts) > 0 else full_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Préparer les données
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "company": contact_data.get("Entreprise"),
            "email": contact_data.get("Email") or None,
            "phone": contact_data.get("Tel") or None,
            "tags": [tag.strip() for tag in contact_data.get("Tags", "").split(",") if tag.strip()],
            "stage": contact_data.get("Stage", "contact"),
            "source": "google_sheets",
        }

        # Créer le contact
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                created += 1
                print(f"✓ {full_name} créé")
            else:
                print(f"✗ {full_name} erreur: {response.text}")
                skipped += 1
        except Exception as e:
            print(f"✗ {full_name} exception: {e}")
            skipped += 1

    print(f"\n=== Import terminé ===")
    print(f"Créés: {created}")
    print(f"Ignorés: {skipped}")

if __name__ == "__main__":
    import_contacts()
