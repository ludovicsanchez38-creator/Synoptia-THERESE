"""Adaptateurs chat des opérations tâches et brouillons déjà utilisées par l'API.

Aucun transport HTTP : même validation, calculs et transactions que les modules.
Les mutations sont appelées uniquement par le portillon de confirmation du chat.
"""
import json
from typing import Any

from app.models.schemas import CreateInvoiceRequest, CreateTaskRequest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


def _outil(nom: str, description: str, proprietes: dict[str, Any], requis: list[str]) -> dict[str, Any]:
    return {'type': 'function', 'function': {
        'name': nom, 'description': description,
        'parameters': {'type': 'object', 'properties': proprietes, 'required': requis},
    }}


OUTILS_METIER = [
    _outil('list_tasks', 'Lire les tâches du module Tâches (pas les rendez-vous), dans le projet courant si choisi.', {
        'status': {'type': 'string', 'enum': ['todo', 'in_progress', 'done', 'cancelled']},
        'priority': {'type': 'string', 'enum': ['low', 'medium', 'high', 'urgent']},
    }, []),
    _outil('create_task', 'Préparer une tâche dans le module Tâches. Écriture seulement après Confirmer. Ne pas créer un rendez-vous pour une tâche.', {
        'title': {'type': 'string'}, 'description': {'type': 'string'},
        'due_date': {'type': 'string', 'description': 'Échéance ISO 8601 si demandée.'},
        'priority': {'type': 'string', 'enum': ['low', 'medium', 'high', 'urgent']},
        'contact_id': {'type': 'string'},
    }, ['title']),
    _outil('create_invoice', 'Préparer un BROUILLON de facture ou de devis dans Devis et factures, jamais un document Word/Excel. Demander le client ou les montants manquants. Écriture seulement après Confirmer ; aucune émission ni envoi.', {
        'contact_id': {'type': 'string', 'description': 'Identifiant obtenu avec read_contact.'},
        'document_type': {'type': 'string', 'enum': ['facture', 'devis']},
        'tva_applicable': {'type': 'boolean'},
        'currency': {'type': 'string', 'enum': ['EUR', 'CHF', 'USD', 'GBP', 'CAD']},
        'due_date': {'type': 'string'}, 'notes': {'type': 'string'},
        'lines': {'type': 'array', 'minItems': 1, 'items': {
            'type': 'object', 'properties': {
                'description': {'type': 'string'}, 'quantity': {'type': 'number'},
                'unit_price_ht': {'type': 'number'}, 'tva_rate': {'type': 'number'},
            }, 'required': ['description', 'quantity', 'unit_price_ht', 'tva_rate'],
        }},
    }, ['contact_id', 'document_type', 'lines']),
]
NOMS_OUTILS_METIER = {o['function']['name'] for o in OUTILS_METIER}


async def executer_outil_metier(
    nom: str, arguments: dict[str, Any], session: AsyncSession, project_id: str | None,
) -> str:
    from app.routers import invoices, tasks
    from app.services.workspace_tools import _client_du_dossier

    try:
        if nom == 'list_tasks':
            lignes = await tasks.list_tasks(
                status=arguments.get('status'), priority=arguments.get('priority'),
                project_id=project_id, contact_id=None, limit=200, offset=0, session=session,
            )
            return json.dumps({'tasks': [t.model_dump() for t in lignes], 'limit': 200}, ensure_ascii=False)
        if nom == 'create_task':
            demande = CreateTaskRequest.model_validate({
                **{k: v for k, v in arguments.items() if k in {'title', 'description', 'priority', 'due_date', 'contact_id'}},
                'project_id': project_id,
            })
            tache = await tasks.create_task(demande, session)
            return json.dumps({'success': True, 'task_id': tache.id, 'message': f'Tâche créée : {tache.title}.'}, ensure_ascii=False)
        if arguments.get('document_type') not in ('facture', 'devis'):
            raise HTTPException(400, 'Choisis une facture ou un devis en brouillon.')
        if not arguments.get('lines'):
            raise HTTPException(400, 'Ajoute au moins une ligne au brouillon.')
        demande_facture = CreateInvoiceRequest.model_validate(arguments)
        cloisonne, client = await _client_du_dossier(project_id, session)
        if cloisonne and demande_facture.contact_id != client:
            raise HTTPException(400, 'Choisis le client du projet courant pour ce brouillon.')
        facture = await invoices.create_invoice(demande_facture, session)
        return json.dumps({'success': True, 'invoice_id': facture.id, 'message': f'Brouillon de {facture.document_type} créé dans Devis et factures.'}, ensure_ascii=False)
    except ValidationError:
        return json.dumps({'success': False, 'message': 'Vérifie les champs obligatoires, les dates et les montants de la carte.'}, ensure_ascii=False)
    except HTTPException as erreur:
        return json.dumps({'success': False, 'message': str(erreur.detail)}, ensure_ascii=False)
