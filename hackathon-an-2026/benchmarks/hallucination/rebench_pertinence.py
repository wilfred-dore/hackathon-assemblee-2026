"""Re-mesure le benchmark AVEC vérification complète (existence + pertinence).

Pour chaque réponse de modèle (citations déjà enregistrées), on rejoue la logique
du pipeline : une citation est *vérifiée* si elle EXISTE (Canutes) ET est PERTINENTE
(son texte soutient la question, jugé par un LLM ancré). On présente la réponse
seulement si toutes ses citations sont vérifiées, sinon refus.

Sorties par modèle : correct-présenté / hallucination-présentée (BAD) /
hallucination-refusée (attrapée) / sur-refus (correct mais rejeté à tort).

  MODE=live LLM_*=<verifier Mistral> CANUTES_DB_PASSWORD=... PYTHONPATH=. \
    .venv/bin/python benchmarks/hallucination/rebench_pertinence.py
"""
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research")
from hallucination_bench import QUESTIONS
from src.data import canutes
from src.pertinence import check_pertinence
from src.llm.client import LLMClient

CODENAMES = {'travail': 'Code du travail', 'civil': 'Code civil', 'procédure pénale': 'Code de procédure pénale', 'consommation': 'Code de la consommation'}

by_gt = {gt: (q, code) for (q, gt, code) in QUESTIONS}
res = json.load(open("benchmarks/hallucination/bench_results.json"))
llm = LLMClient()
_cache = {}


def verify_cite(num, code, question):
    key = (num, code, question)
    if key in _cache:
        return _cache[key]
    try:
        r = canutes.verify_article(num, CODENAMES.get(code, code))
        exists = bool(r and r.get("exists"))
        pert = check_pertinence(question, r.get("excerpt"), llm) if exists else False
    except Exception as e:
        print("  [warn]", num, code, type(e).__name__)
        exists, pert = False, False
    _cache[key] = (exists and pert)
    return _cache[key]


summary = {}
for model, v in res.items():
    o = {"correct_presente": 0, "hallu_presentee": 0, "hallu_refusee": 0, "sur_refus": 0}
    for d in v["details"]:
        gt = d["gt"]
        q, code = by_gt.get(gt, (d["q"], ""))
        cited = d["cité"]
        correct = gt in cited
        presented = bool(cited) and all(verify_cite(c, code, q) for c in cited)
        if presented and correct:
            o["correct_presente"] += 1
        elif presented and not correct:
            o["hallu_presentee"] += 1
        elif (not presented) and (not correct):
            o["hallu_refusee"] += 1
        else:  # refusé alors que correct
            o["sur_refus"] += 1
    summary[model] = o
    print(f"{model:34} {o}")

json.dump(summary, open("benchmarks/hallucination/rebench_results.json", "w"), ensure_ascii=False, indent=2)
n = len(QUESTIONS) * len(summary)
tot = {k: sum(s[k] for s in summary.values()) for k in ["correct_presente", "hallu_presentee", "hallu_refusee", "sur_refus"]}
print("\n=== AGRÉGÉ (n =", n, ") ===")
for k, val in tot.items():
    print(f"  {k:20} {val:3}  ({val/n*100:.0f}%)")
print(f"\nHallucination PRÉSENTÉE après vérif complète : {tot['hallu_presentee']}/{n} "
      f"({tot['hallu_presentee']/n*100:.0f}%)  [vs 19% avec existence seule]")
