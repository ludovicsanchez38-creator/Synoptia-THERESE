"""Verrou applicatif utilisé pendant les restaurations de données."""

import asyncio
from enum import Enum


class RequestAdmission(Enum):
    """Décision du verrou pour une requête API entrante."""

    TRACKED = "tracked"
    BYPASS = "bypass"
    REJECTED = "rejected"


class MaintenanceMode:
    """Bloque les API pendant qu'une opération exclusive remplace les données.

    Le compteur permet à la restauration d'attendre la fin des requêtes déjà
    admises avant de fermer les moteurs de base de données.
    """

    def __init__(self) -> None:
        self._active = False
        self._active_requests = 0

    @property
    def active(self) -> bool:
        return self._active

    def admit(self, method: str, path: str) -> RequestAdmission:
        """Admet, contourne ou refuse atomiquement une requête API."""
        if not path.startswith("/api/") or path in {"/api/health", "/api/shutdown"}:
            return RequestAdmission.BYPASS

        if self._active:
            return RequestAdmission.REJECTED

        # La requête qui déclenche le restore doit pouvoir activer elle-même le
        # verrou sans attendre sa propre fin. Les restores concurrents seront
        # refusés dès que le premier aura activé le mode maintenance.
        if method == "POST" and path.startswith("/api/data/restore/"):
            return RequestAdmission.BYPASS

        self._active_requests += 1
        return RequestAdmission.TRACKED

    def release(self, admission: RequestAdmission) -> None:
        if admission is RequestAdmission.TRACKED:
            self._active_requests = max(0, self._active_requests - 1)

    async def begin(self) -> None:
        """Active le verrou puis attend que les requêtes admises se terminent."""
        if self._active:
            raise RuntimeError("Une restauration est déjà en cours")

        self._active = True
        while self._active_requests:
            await asyncio.sleep(0.01)

    def end(self) -> None:
        self._active = False


maintenance_mode = MaintenanceMode()
