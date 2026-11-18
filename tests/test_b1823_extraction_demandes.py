"""B-1823 : une formule d'aide ne masque pas les entités nommées."""
import pytest
from app.services.entity_extractor import EntityExtractor


class ModeleFictif:
    async def stream_response(self, context):
        yield '{"contacts":[{"name":"Marie Martin","confidence":0.9}],"projects":[{"name":"Orion","confidence":0.9}]}'


@pytest.mark.parametrize("formule", ["peux-tu", "pourrais-tu", "comment faire", "aide-moi", "aide moi", "qu'est-ce que"])
async def test_demande_aide_n_ecarte_pas_contact_ni_projet(formule):
    resultat = await EntityExtractor().extract_entities(
        f"{formule} pour le projet Orion de Marie Martin ?", llm=ModeleFictif()
    )
    assert [contact.name for contact in resultat.contacts] == ["Marie Martin"]
    assert [projet.name for projet in resultat.projects] == ["Orion"]
