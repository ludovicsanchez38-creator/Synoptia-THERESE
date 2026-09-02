"""
THÉRÈSE v2 - Schemas Commands

Request/Response models pour les commandes utilisateur personnalisées.
"""

from pydantic import BaseModel, Field, field_validator

# B-187 : le nom d'une commande est repris TEL QUEL dans le chemin des routes
# qui la lisent, la modifient et la suppriment (`/api/commands/user/{name}`,
# et `user-{name}` côté V3). Un nom contenant une barre oblique était accepté,
# apparaissait dans la liste et dans le menu, puis rendait 404 sur les trois
# verbes - encodé ou non, le routeur découpe le chemin avant d'atteindre la
# fonction. La commande devenait impossible à modifier comme à supprimer.
_CARACTERES_HORS_CHEMIN = ("/", "\\")


def valider_nom_de_commande(valeur: str) -> str:
    """Refuse un nom qui ne pourra plus être désigné par les routes de chemin."""
    nom = valeur.strip()
    if not nom:
        raise ValueError("Le nom de la commande ne peut pas être vide")
    if any(caractere in nom for caractere in _CARACTERES_HORS_CHEMIN):
        raise ValueError(
            "Le nom d'une commande ne peut pas contenir « / » ni « \\ » : "
            "elle serait injoignable"
        )
    if any(ord(caractere) < 32 for caractere in nom):
        raise ValueError("Le nom d'une commande ne peut pas contenir de caractère de contrôle")
    if nom.startswith("."):
        raise ValueError("Le nom d'une commande ne peut pas commencer par un point")
    return nom


class CreateCommandRequest(BaseModel):
    """Create user command request."""

    name: str = Field(..., min_length=1, max_length=50, description="Slug de la commande")
    description: str = Field("", max_length=200)
    category: str = Field("general", max_length=50)
    icon: str = Field("", max_length=10)
    show_on_home: bool = False
    content: str = Field("", description="Contenu/prompt de la commande")

    @field_validator("name")
    @classmethod
    def _valider_nom(cls, valeur: str) -> str:
        return valider_nom_de_commande(valeur)


class UpdateCommandRequest(BaseModel):
    """Update user command request."""

    description: str | None = None
    category: str | None = None
    icon: str | None = None
    show_on_home: bool | None = None
    content: str | None = None


class CommandResponse(BaseModel):
    """Command response."""

    name: str
    description: str
    category: str
    icon: str
    show_on_home: bool
    content: str
    created_at: str | None = None
    updated_at: str | None = None
