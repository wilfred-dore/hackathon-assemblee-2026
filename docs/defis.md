# Défis visés — le scaffold marche pour les 3

> Défi PAS encore verrouillé. Ce fichier sert de référence pour ne pas dériver.
> Le flux commun (question → retrieval sourcé → réponse → validation BDD) est
> déjà en place dans [../src/pipeline.py](../src/pipeline.py) ; seul le
> branchement des sources/règles change selon le défi.

## 1. « La loi après la loi »
Analyser l'effet d'une loi **après adoption** : ce que le texte change concrètement.
- Retrieval : versions consolidées vs initiales (Canutes / MCP Moulineuse).
- Rules-as-code : OpenFisca (API web) pour **quantifier** l'effet d'une réforme socio-fiscale.
- Démo : "avant/après" sourcé + chiffres non inventés.

## 2. « NormaCheck »
Vérifier la **conformité / cohérence normative** d'un texte.
- Retrieval : textes de référence (hiérarchie des normes) via MCP/Canutes.
- Validation : garde-fous anti-hallucination + citations vérifiées.
- Démo : "ce passage est/ n'est pas conforme à [ref]" avec la source cliquable.

## 3. « IA de confiance souveraine » (notre défi)
LLM **souverain** (Mistral via Modular MAX sur AMD) + sources vérifiables + refus si pas de source.
- Angle : souveraineté + frugalité (panneau perf/watt) + zéro citation inventée.
- Démo : le refus explicite est une feature, pas un bug.

## Invariant commun (les 3)
Zéro citation inventée · chiffres via rules-as-code · refus si pas de source ·
scénarios Gherkin français vert/rouge lisibles par un juriste.
