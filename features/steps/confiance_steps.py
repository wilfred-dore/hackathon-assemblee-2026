"""Steps behave qui appellent le vrai pipeline.

Le 2e scénario injecte des sources de test via un LLM factice, pour vérifier
le garde-fou anti-citation-inventée sans dépendre d'un vrai endpoint.
"""
from behave import given, when, then

from src.pipeline import Source, answer_question, generate, validate


class _FakeLLM:
    """LLM factice : renvoie un texte citant uniquement des refs connues."""
    def __init__(self, refs):
        self._refs = refs

    def chat(self, messages, temperature=0.0):
        cites = " ".join(f"[{r}]" for r in self._refs)
        return f"Selon les sources disponibles {cites}, voici la réponse."


# --- Scénario 1 : refus sans source ---

@given("une question juridique sans source disponible")
def step_question_sans_source(context):
    context.question = "Question de test sans aucune source branchée ?"


@when("je pose la question à l'assistant")
def step_pose_question(context):
    # Sans .env câblé, retrieve() ne ramène rien -> refus attendu.
    context.answer = answer_question(context.question)


@then("l'assistant refuse de répondre")
def step_refuse(context):
    assert context.answer.refused, "L'assistant aurait dû refuser (pas de source)."


@then("la réponse ne contient aucune citation inventée")
def step_pas_citation_inventee(context):
    v = context.answer.validation
    assert v.get("no_invented_citation", False), f"Citations inventées : {v}"


# --- Scénario 2 : citations valides quand sources présentes ---

@given("une question juridique avec des sources disponibles")
def step_question_avec_sources(context):
    context.question = "Question de test avec sources ?"
    context.sources = [
        Source(ref="LEGIARTI-DEMO-1", title="Article démo 1", snippet="...", origin="canutes"),
        Source(ref="LEGIARTI-DEMO-2", title="Article démo 2", snippet="...", origin="canutes"),
    ]
    context.llm = _FakeLLM([s.ref for s in context.sources])
    # On court-circuite retrieve() pour tester la génération + validation.
    text = generate(context.question, context.sources, context.llm)
    context.validation = validate(text, context.sources)


@then("chaque citation de la réponse correspond à une source fournie")
def step_citations_valides(context):
    assert context.validation["no_invented_citation"], \
        f"Citations inventées détectées : {context.validation['invented_refs']}"
