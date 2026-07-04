# Benchmark d'hallucination de citations juridiques (FR)

Scripts + résultats du pilote (n=12 questions, 6 modèles, 2026-07-04). C'est la
base à étendre vers **n ≥ 100** pour le papier (`paper/main.tex`).

## Fichiers

| Fichier | Rôle |
|---|---|
| `hallucination_bench.py` | pose les 12 questions au panel (Mammouth API + Ollama local), extrait les citations, score correct/hallucination → `bench_results.json` + graphique |
| `classify_hallucinations.py` | classe chaque hallucination : article **inexistant** (attrapé par la vérif d'existence) vs **réel mais hors-sujet** (attrapé seulement par la pertinence) |
| `rebench_pertinence.py` | rejoue les 72 réponses à travers la vérification complète (existence CID + pertinence LLM ancrée) → hallucination présentée / refusée / sur-refus |
| `bench_results.json` / `rebench_results.json` | résultats bruts du pilote |

## Lancer

```bash
# depuis hackathon-an-2026/ (clés dans l'environnement, jamais en dur)
MAMMOUTH_API_KEY=... uv run --with openai --with matplotlib --with numpy \
  python benchmarks/hallucination/hallucination_bench.py

MODE=live LLM_BASE_URL=... LLM_API_KEY=... LLM_MODEL=... CANUTES_DB_PASSWORD=... \
  PYTHONPATH=. uv run python benchmarks/hallucination/rebench_pertinence.py
```

## Étendre à n ≥ 100 (plan)

1. **Questions** : puiser dans les questions écrites parlementaires (Canutes contient
   292 746 questions Sénat, `senat.questions_tam_questions` ; ressources AN idem).
   Les réponses ministérielles citent les textes applicables → paires question-article.
2. **Vérité-terrain** : re-vérifier chaque article de référence dans Canutes
   (`verify_article`, statut VIGUEUR) — pas de hand-curation.
3. **Rigueur** : plusieurs runs par modèle, intervalle de confiance, versions de
   modèles figées, à température fixe documentée.

## Résultats pilote (rappel)

- LLM seul : 21 % d'hallucination présentée (15/72) — dont **14/15 = articles réels
  mais hors-sujet** (la vérif d'existence seule n'attrape presque rien).
- Vérification complète (existence CID + pertinence) : **3 %** présentée, 7 % de
  sur-refus (fail-closed assumé).
- Par modèle : claude-sonnet-4-5 et mistral-large-3 12/12 ; mistral-small-24B 11/12 ;
  gpt-4o et gemini-2.5-flash 10/12 ; **mistral 7B local 2/12**.
