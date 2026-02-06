"""
THÉRÈSE v2 - Skills Router

API endpoints pour la génération de documents via skills.
"""

import logging

from app.models.database import get_session
from app.models.entities import Contact, Project
from app.models.schemas_skills import ExecuteSkillRequest, SkillInfo
from app.services.llm import LLMService, get_llm_service
from app.services.skills import (
    SkillExecuteRequest,
    SkillExecuteResponse,
    get_skills_registry,
)
from app.services.skills.base import SkillOutputType
from app.services.skills.model_capability import get_model_capability
from app.services.user_profile import get_cached_profile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", response_model=list[SkillInfo])
async def list_skills():
    """
    Liste tous les skills disponibles.

    Returns:
        Liste des skills avec leurs métadonnées
    """
    registry = get_skills_registry()
    return registry.list_skills()


@router.post("/execute/{skill_id}", response_model=SkillExecuteResponse)
async def execute_skill(
    skill_id: str,
    request: ExecuteSkillRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Exécute un skill pour générer un document.

    Flow:
    1. Récupère le skill depuis le registry
    2. Récupère le profil utilisateur et la mémoire
    3. Enrichit le contexte avec le skill
    4. Enrichit le prompt avec les instructions du skill
    5. Appelle le LLM pour générer le contenu
    6. Génère le fichier via le skill
    7. Retourne l'URL de téléchargement

    Args:
        skill_id: Identifiant du skill
        request: Paramètres de génération
        session: Session DB

    Returns:
        Réponse avec URL de téléchargement ou erreur
    """
    registry = get_skills_registry()
    skill = registry.get(skill_id)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found. Available: [{ ','.join([s['skill_id'] for s in registry.list_skills()]) }]"
        )

    try:
        # 1. Récupérer le profil utilisateur
        user_profile = get_cached_profile()
        user_profile_dict = {
            'name': user_profile.display_name if user_profile else '',
            'company': user_profile.company if user_profile else '',
            'role': user_profile.role if user_profile else '',
        }

        # 2. Récupérer la mémoire (contacts et projets)
        from sqlmodel import select
        contacts_result = await session.execute(select(Contact).limit(50))
        contacts = contacts_result.scalars().all()

        projects_result = await session.execute(select(Project).limit(50))
        projects = projects_result.scalars().all()

        memory_context = {
            'inputs': request.context or {},
            'contacts': [
                {
                    'name': f"{c.first_name or ''} {c.last_name or ''}".strip(),
                    'company': c.company,
                    'email': c.email,
                    'notes': c.notes,
                }
                for c in contacts
            ],
            'projects': [
                {
                    'name': p.name,
                    'status': p.status,
                    'budget': p.budget,
                }
                for p in projects
            ],
        }

        # 3. Enrichir le contexte via le skill
        enrichment = skill.get_enrichment_context(user_profile_dict, memory_context)

        # 4. Préparer le prompt enrichi pour le LLM
        llm_service: LLMService = get_llm_service()
        system_addition = skill.get_system_prompt_addition()

        # Construire la section d'enrichissement
        enrichment_text = "\n".join([f"{key}: {value}" for key, value in enrichment.items() if value])

        # Adapter le prompt selon la capacité du modèle (code Python vs Markdown)
        code_instruction = ""
        if skill.output_type == SkillOutputType.FILE:
            capability = get_model_capability(
                llm_service.config.provider,
                llm_service.config.model,
            )
            if capability == "code":
                code_instruction = "\nIMPORTANT : Génère ta réponse sous forme d'un bloc de code Python (```python```) qui crée le fichier. Le code sera exécuté directement."
            else:
                # Modèle non code-capable : demander du Markdown structuré
                system_addition = skill.get_markdown_prompt_addition()
                logger.info(
                    f"Modèle {llm_service.config.model} ({llm_service.config.provider.value}) "
                    f"→ mode markdown pour skill {skill_id}"
                )

        enriched_prompt = f"""
{request.prompt}

## Contexte utilisateur
{enrichment_text}

{system_addition}
{code_instruction}
"""

        # 5. Appeler le LLM (max_tokens augmenté pour les skills FILE qui génèrent du code)
        llm_max_tokens = 8192 if skill.output_type == SkillOutputType.FILE else None
        llm_content = await llm_service.generate_content(
            prompt=enriched_prompt,
            context=request.context,
            max_tokens=llm_max_tokens,
        )

        # Exécuter le skill avec le contenu généré
        skill_request = SkillExecuteRequest(
            prompt=request.prompt,
            title=request.title,
            template=request.template,
            context=request.context,
        )

        result = await registry.execute(skill_id, skill_request, llm_content)

        return result

    except Exception as e:
        logger.exception(f"Error executing skill {skill_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating document: {str(e)}"
        )


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Télécharge un fichier généré par un skill.

    Args:
        file_id: Identifiant du fichier

    Returns:
        Le fichier en téléchargement
    """
    registry = get_skills_registry()
    result = registry.get_file(file_id)

    # Si pas en cache, chercher le fichier sur disque par son ID
    if not result:
        output_dir = registry.output_dir

        # Chercher un fichier dont le nom contient le file_id (format: Title_fileId[:8].ext)
        short_id = file_id[:8]
        matching_files = list(output_dir.glob(f"*_{short_id}.*"))

        if matching_files:
            file_path = matching_files[0]
            # Déterminer le MIME type par extension
            ext = file_path.suffix.lower()
            mime_types = {
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".pdf": "application/pdf",
                ".md": "text/markdown",
            }
            mime_type = mime_types.get(ext, "application/octet-stream")

            return FileResponse(
                path=str(file_path),
                filename=file_path.name,
                media_type=mime_type,
            )

        raise HTTPException(
            status_code=404,
            detail=f"File '{file_id}' not found or expired"
        )

    if not result.file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found on disk"
        )

    return FileResponse(
        path=str(result.file_path),
        filename=result.file_name,
        media_type=result.mime_type,
    )


@router.get("/info/{skill_id}", response_model=SkillInfo)
async def get_skill_info(skill_id: str):
    """
    Récupère les informations détaillées d'un skill.

    Args:
        skill_id: Identifiant du skill

    Returns:
        Informations sur le skill
    """
    registry = get_skills_registry()
    skill = registry.get(skill_id)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found"
        )

    return SkillInfo(
        skill_id=skill.skill_id,
        name=skill.name,
        description=skill.description,
        format=skill.output_format.value,
    )


@router.get("/prompt/{skill_id}")
async def get_skill_prompt(skill_id: str):
    """
    Récupère les instructions de prompt pour un skill.

    Utile pour le frontend pour afficher des instructions à l'utilisateur.

    Args:
        skill_id: Identifiant du skill

    Returns:
        Instructions de prompt du skill
    """
    registry = get_skills_registry()
    skill = registry.get(skill_id)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found"
        )

    return {
        "skill_id": skill_id,
        "system_prompt": skill.get_system_prompt_addition(),
    }


@router.get("/schema/{skill_id}")
async def get_skill_schema(skill_id: str):
    """
    Récupère le schéma des champs d'entrée pour un skill.

    Utilisé par le frontend pour générer dynamiquement le formulaire.

    Args:
        skill_id: Identifiant du skill

    Returns:
        Schéma JSON des champs d'entrée

    Example response:
        {
            "skill_id": "email-pro",
            "output_type": "text",
            "schema": {
                "recipient": {
                    "type": "text",
                    "label": "Destinataire",
                    "placeholder": "Nom de la personne",
                    "required": true,
                    "help_text": "À qui s'adresse cet email ?"
                },
                "tone": {
                    "type": "select",
                    "label": "Ton",
                    "options": ["formel", "amical", "neutre"],
                    "default": "formel",
                    "required": false
                }
            }
        }
    """
    registry = get_skills_registry()
    skill = registry.get(skill_id)

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found"
        )

    # Récupérer le schéma depuis le skill
    schema = skill.get_input_schema()

    # Convertir les InputField dataclasses en dictionnaires
    schema_dict = {}
    for field_name, input_field in schema.items():
        schema_dict[field_name] = {
            "type": input_field.type,
            "label": input_field.label,
            "placeholder": input_field.placeholder,
            "required": input_field.required,
            "options": input_field.options,
            "default": input_field.default,
            "help_text": input_field.help_text,
        }

    return {
        "skill_id": skill_id,
        "output_type": skill.output_type.value,
        "schema": schema_dict,
    }
