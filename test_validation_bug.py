"""Test pour reproduire le bug VALIDATION-DETAILS-VIDE."""
import json

# Simulation de la validação Pydantic
# exc.errors() retourne une liste de dicts avec loc, type, msg
mock_errors = [
    {
        "type": "value_error.missing",
        "loc": ("body", "first_name"),  # first_name is required
        "msg": "field required",
        "input": {"body": {}},
    },
    {
        "type": "string_type",
        "loc": ("body", "email"),
        "msg": "Input should be a valid string",
        "input": {"email": 123},
    }
]

# CODE ACTUEL (ligne 457-463 du main.py)
safe_details_current = [
    {
        "field": ".".join(str(x) for x in err.get("loc", []) if x != "body"),
        "message": err.get("msg", ""),
    }
    for err in mock_errors
]

print("=== CURRENT CODE (BUGUÉ) ===")
print(json.dumps(safe_details_current, indent=2))

# Le problème: si loc == ("body",) ou loc == ("body", "field"),
# le filtre if x != "body" enlève TOUS les éléments
# et on se retrouve avec un field vide ""
