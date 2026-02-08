"""
THERESE v2 - Entity Extractor Service

Extracts contacts and projects from user messages using LLM.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from app.services.llm import ContextWindow, Message, get_llm_service

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContact:
    """Extracted contact entity."""
    name: str
    company: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    confidence: float = 0.0


@dataclass
class ExtractedProject:
    """Extracted project entity."""
    name: str
    description: str | None = None
    budget: float | None = None
    status: str | None = None
    confidence: float = 0.0


@dataclass
class ExtractionResult:
    """Result of entity extraction."""
    contacts: list[ExtractedContact]
    projects: list[ExtractedProject]


EXTRACTION_SYSTEM_PROMPT = """Tu es un assistant specialise dans l'extraction d'entites depuis des messages.

Tu dois extraire les CONTACTS et PROJETS mentionnes dans le message utilisateur.

REGLES:
1. N'extrais QUE les entites clairement identifiables
2. Un contact doit avoir un nom propre (prenom et/ou nom de famille)
3. Un projet doit avoir un nom ou une description claire
4. N'invente RIEN - n'extrais que ce qui est explicitement mentionne
5. Ignore les pronoms (je, tu, il, nous) et les references vagues
6. Attribue un score de confiance entre 0 et 1

EXEMPLES DE CONTACTS VALIDES:
- "Pierre Dupont" (nom complet)
- "Marie de chez Acme" (prenom + entreprise)
- "le CEO Jean Martin" (nom + role)

EXEMPLES DE CONTACTS INVALIDES:
- "mon client" (trop vague)
- "quelqu'un" (pas de nom)
- "l'equipe" (pas individuel)

EXEMPLES DE PROJETS VALIDES:
- "le projet Site Web" (nom explicite)
- "la refonte du CRM" (description claire)
- "mission a 5000 euros" (budget mentionne)

EXEMPLES DE PROJETS INVALIDES:
- "ce truc" (trop vague)
- "mon travail" (pas specifique)

REPONDS UNIQUEMENT en JSON valide avec ce format exact:
{
  "contacts": [
    {"name": "Nom Complet", "company": "Entreprise ou null", "role": "Role ou null", "email": "email ou null", "phone": "tel ou null", "confidence": 0.85}
  ],
  "projects": [
    {"name": "Nom du Projet", "description": "Description ou null", "budget": 5000 ou null, "status": "active/completed/on_hold ou null", "confidence": 0.9}
  ]
}

Si aucune entite n'est trouvee, retourne: {"contacts": [], "projects": []}"""


class EntityExtractor:
    """Service for extracting entities from messages."""

    MIN_CONFIDENCE = 0.6

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm_service()
        return self._llm

    async def extract_entities(
        self,
        user_message: str,
        existing_contacts: list[str] | None = None,
        existing_projects: list[str] | None = None,
    ) -> ExtractionResult:
        if len(user_message.strip()) < 10:
            return ExtractionResult(contacts=[], projects=[])

        skip_patterns = [
            "qui suis-je", "aide moi", "aide-moi", "comment faire",
            "qu'est-ce que", "peux-tu", "pourrais-tu",
        ]
        message_lower = user_message.lower()
        if any(pattern in message_lower for pattern in skip_patterns):
            return ExtractionResult(contacts=[], projects=[])

        try:
            llm = self._get_llm()
            prompt = f"Message utilisateur a analyser:\n\n{user_message}"
            messages = [Message(role="user", content=prompt)]
            context = ContextWindow(
                messages=messages,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                max_tokens=2000,
            )

            response_parts = []
            async for chunk in llm.stream_response(context):
                response_parts.append(chunk)

            response = "".join(response_parts).strip()
            result = await asyncio.to_thread(self._parse_extraction_response, response)

            if existing_contacts:
                existing_lower = [n.lower() for n in existing_contacts]
                result.contacts = [
                    c for c in result.contacts
                    if c.name.lower() not in existing_lower
                ]

            if existing_projects:
                existing_lower = [n.lower() for n in existing_projects]
                result.projects = [
                    p for p in result.projects
                    if p.name.lower() not in existing_lower
                ]

            result.contacts = [c for c in result.contacts if c.confidence >= self.MIN_CONFIDENCE]
            result.projects = [p for p in result.projects if p.confidence >= self.MIN_CONFIDENCE]

            logger.info(f"Extracted {len(result.contacts)} contacts, {len(result.projects)} projects")
            return result

        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return ExtractionResult(contacts=[], projects=[])

    def _parse_extraction_response(self, response: str) -> ExtractionResult:
        json_str = response
        backtick = "`"
        triple_backtick = backtick * 3

        if f"{triple_backtick}json" in response:
            start = response.find(f"{triple_backtick}json") + 7
            end = response.find(triple_backtick, start)
            if end > start:
                json_str = response[start:end].strip()
        elif triple_backtick in response:
            start = response.find(triple_backtick) + 3
            end = response.find(triple_backtick, start)
            if end > start:
                json_str = response[start:end].strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(response[start:end])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse extraction response: {response[:200]}")
                    return ExtractionResult(contacts=[], projects=[])
            else:
                return ExtractionResult(contacts=[], projects=[])

        contacts = []
        for c in data.get("contacts", []):
            if isinstance(c, dict) and c.get("name"):
                contacts.append(ExtractedContact(
                    name=c.get("name", ""),
                    company=c.get("company"),
                    role=c.get("role"),
                    email=c.get("email"),
                    phone=c.get("phone"),
                    confidence=float(c.get("confidence", 0.5)),
                ))

        projects = []
        for p in data.get("projects", []):
            if isinstance(p, dict) and p.get("name"):
                projects.append(ExtractedProject(
                    name=p.get("name", ""),
                    description=p.get("description"),
                    budget=float(p["budget"]) if p.get("budget") else None,
                    status=p.get("status"),
                    confidence=float(p.get("confidence", 0.5)),
                ))

        return ExtractionResult(contacts=contacts, projects=projects)


_extractor: EntityExtractor | None = None


def get_entity_extractor() -> EntityExtractor:
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def extraction_result_to_dict(result: ExtractionResult) -> dict[str, Any]:
    return {
        "contacts": [
            {
                "name": c.name,
                "company": c.company,
                "role": c.role,
                "email": c.email,
                "phone": c.phone,
                "confidence": c.confidence,
            }
            for c in result.contacts
        ],
        "projects": [
            {
                "name": p.name,
                "description": p.description,
                "budget": p.budget,
                "status": p.status,
                "confidence": p.confidence,
            }
            for p in result.projects
        ],
    }
