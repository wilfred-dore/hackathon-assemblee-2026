"""Classe chaque hallucination du benchmark : inexistante (attrapée par la vérif
d'existence Canutes) vs existante-mais-fausse (NON attrapée). Donne le vrai chiffre
d'hallucination *présentée* après vérification d'existence.

  CANUTES_DB_PASSWORD=... uv run --with openai python benchmarks/hallucination/classify_hallucinations.py
"""
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research")
from hallucination_bench import QUESTIONS
from src.data import canutes

CODENAMES = {'travail': 'Code du travail', 'civil': 'Code civil', 'procédure pénale': 'Code de procédure pénale', 'consommation': 'Code de la consommation'}

# gt_num -> gt_code (pour savoir dans quel code chercher l'existence d'une citation)
gt_code = {gt: code for (_q, gt, code) in QUESTIONS}
# map question tronquée (40) -> gt_code, pour retrouver le code de chaque item
q40_code = {q[:40]: code for (q, _gt, code) in QUESTIONS}

res = json.load(open("benchmarks/hallucination/bench_results.json"))
cache = {}


def exists(num, code):
    key = (num, code)
    if key not in cache:
        try:
            r = canutes.verify_article(num, CODENAMES.get(code, code))
            cache[key] = bool(r and r.get("exists"))
        except Exception as e:
            print("  [warn]", num, code, type(e).__name__)
            cache[key] = False
    return cache[key]


summary = {}
for model, v in res.items():
    correct = v["counts"]["correct"]
    hallu_A = 0  # inexistant -> attrapé (refus)
    hallu_B = 0  # existe mais faux -> PAS attrapé (présenté avec vrai lien)
    for d in v["details"]:
        if d["verdict"] != "hallucination":
            continue
        code = q40_code.get(d["q"], "")
        cited = d["cité"]
        any_exists = any(exists(c, code) for c in cited)
        if any_exists:
            hallu_B += 1
        else:
            hallu_A += 1
    n = len(v["details"])
    summary[model] = {
        "n": n, "correct": correct,
        "hallu_inexistant_attrape": hallu_A,
        "hallu_existant_faux_NON_attrape": hallu_B,
    }
    print(f"{model:34} n={n} correct={correct:2} "
          f"inexistant(attrapé)={hallu_A} existant-faux(NON attrapé)={hallu_B}")

json.dump(summary, open("benchmarks/hallucination/classification.json", "w"), ensure_ascii=False, indent=2)

# Agrégats honnêtes
tot_n = sum(s["n"] for s in summary.values())
tot_B = sum(s["hallu_existant_faux_NON_attrape"] for s in summary.values())
tot_A = sum(s["hallu_inexistant_attrape"] for s in summary.values())
print("\n=== AGRÉGÉ ===")
print(f"total items: {tot_n}")
print(f"hallucination INEXISTANTE (attrapée par vérif existence): {tot_A} ({tot_A/tot_n*100:.0f}%)")
print(f"hallucination EXISTANTE-MAIS-FAUSSE (NON attrapée):        {tot_B} ({tot_B/tot_n*100:.0f}%)")
# focus petit modèle local
loc = summary.get("mistral")
if loc:
    print(f"\nMistral 7B local: {loc['correct']}/12 correct ; "
          f"inexistant(attrapé)={loc['hallu_inexistant_attrape']} ; "
          f"existant-faux(NON attrapé)={loc['hallu_existant_faux_NON_attrape']}")
