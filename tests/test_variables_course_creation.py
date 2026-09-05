"""B-549 (05/09/2026) : deux créations simultanées d'une même variable.

`create_variable` lit puis insère. Entre la lecture et l'insertion, un
concurrent peut avoir inséré le même nom : la contrainte UNIQUE lève alors
une IntegrityError que personne ne rattrapait, et l'API rendait 500 au lieu
du 409 « existe déjà » réservé à ce cas. Le test rejoue exactement la fenêtre
de la course : la lecture ne voit rien, l'insertion collisionne.
"""
import pytest
from app.services import variables_service
from app.services.variables_service import VariableExistante, create_variable


@pytest.mark.asyncio
async def test_collision_a_l_insertion_devient_variable_existante(db_session, monkeypatch):
    await create_variable(db_session, "course", "text", "première")

    async def _lecture_aveugle(session, name):
        return None  # le concurrent n'est pas encore visible à la lecture

    monkeypatch.setattr(variables_service, "get_variable", _lecture_aveugle)

    with pytest.raises(VariableExistante):
        await create_variable(db_session, "course", "text", "seconde")

    # La session reste utilisable après la reprise (rollback fait).
    monkeypatch.undo()
    conservee = await variables_service.get_variable(db_session, "course")
    assert conservee is not None
    assert conservee.parsed_value == "première"
