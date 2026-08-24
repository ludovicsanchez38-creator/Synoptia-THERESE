"""Le retrait Qdrant doit être COMPLET (0.45, fondation du service de retrait).

Challenge du design V2 : `delete_by_entity` faisait un scroll limité à 1000
points puis supprimait ces ids - un document de plus de 1000 fragments gardait
des vecteurs orphelins, invisibles mais toujours servis par la recherche. La
suppression passe par un FilterSelector côté serveur : tout ce qui matche
part, quel que soit le volume.
"""

from unittest.mock import MagicMock

from qdrant_client.models import FilterSelector


class TestLeRetraitNeS_arretePasA1000:
    def _service_avec_client_factice(self, nombre_de_points: int):
        from app.services.qdrant import QdrantService

        service = QdrantService.__new__(QdrantService)
        client = MagicMock()
        client.count.return_value = MagicMock(count=nombre_de_points)
        # `client` est une propriété paresseuse : on pose l'attribut interne.
        service._client = client
        return service, client

    def test_delete_by_entity_supprime_par_filtre(self):
        service, client = self._service_avec_client_factice(2500)

        supprimes = service.delete_by_entity("fichier-geant")

        assert supprimes == 2500, (
            "2500 fragments existent : le retrait doit tous les compter, pas "
            "s'arrêter au scroll de 1000"
        )
        selecteur = client.delete.call_args.kwargs["points_selector"]
        assert isinstance(selecteur, FilterSelector), (
            "la suppression doit être un filtre serveur, pas une liste d'ids "
            "issue d'un scroll plafonné"
        )

    def test_delete_by_scope_supprime_par_filtre(self):
        service, client = self._service_avec_client_factice(1500)

        supprimes = service.delete_by_scope("project", "p-1")

        assert supprimes == 1500
        assert isinstance(
            client.delete.call_args.kwargs["points_selector"], FilterSelector
        )

    def test_une_entite_sans_points_rend_zero_sans_supprimer(self):
        service, client = self._service_avec_client_factice(0)

        assert service.delete_by_entity("absent") == 0
        client.delete.assert_not_called()
