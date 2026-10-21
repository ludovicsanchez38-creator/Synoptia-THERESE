"""Groupes fonctionnels pour un allégement local progressif."""
import re
import unicodedata
from typing import Any

GROUPES = {
 'agenda': {'list_calendar_events', 'create_calendar_event'},
 'courrier': {'read_emails', 'search_emails', 'summarize_emails', 'send_email'},
 'taches': {'list_tasks', 'create_task'},
 'factures': {'create_invoice', 'search_invoices', 'invoice_totals'},
 'fichiers': {'search_files', 'read_file', 'generate_document'},
 'memoire': {'upsert_memory_card', 'create_contact', 'create_project', 'read_contact'},
 'web': {'web_search', 'browser_navigate'},
}
MOTS = {
 'agenda': r'agenda|calendrier|rendez|rdv|reunion|demain|aujourd',
 'courrier': r'mail|courrier|message|envoy|boite',
 'taches': r'tache|todo|a faire',
 'factures': r'factur|devis|encaisser|tresorerie|avoir',
 'fichiers': r'fichier|document|pdf|word|excel|powerpoint',
 'memoire': r'retiens|memor|souviens|contact|client|dossier',
 'web': r'internet|site|actualite|https?://',
}


def groupe_outil(outil: dict[str, Any]) -> str:
    nom = outil.get('function', {}).get('name', '')
    return next((g for g, noms in GROUPES.items() if nom in noms), 'externe:' + nom.split('__')[0])


def domaines_demandes(messages: list[Any]) -> set[str]:
    # Trois demandes récentes et appels d'outils : « et demain ? » conserve
    # l'agenda du tour précédent sans figer tous les sujets de l'historique.
    demandes = [m for m in messages if m.role == 'user'][-3:]
    texte = ' '.join(str(m.content) for m in demandes).lower()
    texte = ''.join(c for c in unicodedata.normalize('NFKD', texte) if not unicodedata.combining(c))
    groupes = {g for g, motif in MOTS.items() if re.search(motif, texte)}
    for m in messages[-6:]:
        for appel in getattr(m, 'tool_calls', None) or []:
            nom = appel.get('function', {}).get('name', '') if isinstance(appel, dict) else appel.name
            groupes.add(groupe_outil({'function': {'name': nom}}))
    return groupes
