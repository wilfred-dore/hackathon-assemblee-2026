from behave import given, then, when

from rapporteur.llm import DemoLLM
from rapporteur.pipeline import REFUSAL, Rapporteur
from rapporteur.verifier import MockVerifier


@given('une question citoyenne "{question}"')
def step_question(context, question):
    context.rapporteur = Rapporteur(llm=DemoLLM(), verifier=MockVerifier())
    context.question = question


@when("le système répond")
def step_answer(context):
    context.result = context.rapporteur.answer(context.question)


@then("chaque article cité doit exister dans Canutes/Légifrance")
def step_all_verified(context):
    citations = context.result["citations"]
    assert citations, "La réponse doit citer au moins une source"
    for c in citations:
        assert c["exists"], f"Article inventé présenté au citoyen : {c['label']}"


@then("la réponse ne doit pas être un refus")
def step_not_refusal(context):
    assert context.result["status"] == "ok"
    assert REFUSAL not in context.result["answer"]


@then("la réponse doit être un refus explicite")
def step_refusal(context):
    assert context.result["status"] == "refus"
    assert context.result["answer"] == REFUSAL


@then("aucun article absent des sources ne doit être présenté comme vérifié")
def step_no_invented_verified(context):
    for c in context.result["citations"]:
        if not c["exists"]:
            assert c["url"] is None, f"Lien fourni vers un article inexistant : {c['label']}"
