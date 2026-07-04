"""Steps behave qui appellent le vrai pipeline (mode hors-ligne : LLM démo +
vérificateur Mock, aucun réseau requis)."""
from behave import given, when, then

from src.pipeline import REFUSAL, answer_question


@given('une question citoyenne "{question}"')
def step_question(context, question):
    context.question = question


@when("le système répond")
def step_repond(context):
    context.answer = answer_question(context.question)


@then("chaque article cité doit exister dans les sources")
def step_citations_existent(context):
    cites = context.answer.citations
    assert cites, "Aucune citation extraite de la réponse."
    absents = [c["label"] for c in cites if not c["exists"]]
    assert not absents, f"Articles non trouvés dans les sources : {absents}"


@then("la réponse ne doit pas être un refus")
def step_pas_refus(context):
    assert context.answer.ok, f"Refus inattendu : {context.answer.detail}"


@then("la réponse doit être un refus explicite")
def step_refus(context):
    assert context.answer.refused, "L'assistant aurait dû refuser."
    assert context.answer.text == REFUSAL, f"Refus non explicite : {context.answer.text!r}"


@then("aucun article absent des sources ne doit être présenté comme vérifié")
def step_pas_faux_verifie(context):
    # On asserte sur les garanties CALCULÉES AU RUNTIME (src/guarantees.py) : le test
    # et le runtime partagent la même définition -> aucune divergence possible.
    g = {x["rule"]: x for x in context.answer.guarantees}
    rule = g["Zéro citation inexistante présentée comme vérifiée"]
    assert rule["passed"], f"Garantie violée : {rule['detail']}"
