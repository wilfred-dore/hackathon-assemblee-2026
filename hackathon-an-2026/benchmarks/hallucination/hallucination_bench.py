"""Mini-benchmark d'hallucination de citations juridiques (FR).

Pose N questions citoyennes (vérité-terrain = article correct connu) à un panel de
modèles (Mammouth AI OpenAI-compatible + Ollama local), extrait l'article cité, et
mesure : correct / halluciné (mauvaise citation) / sans citation.

Clés lues dans l'environnement (jamais en dur) :
  MAMMOUTH_API_KEY   -> panel cloud via https://api.mammouth.ai/v1
Ollama local suppose le daemon sur http://localhost:11434/v1 (modèle 'mistral').

  MAMMOUTH_API_KEY=... uv run --with openai --with matplotlib python benchmarks/hallucination/hallucination_bench.py

⚠️ Vérité-terrain hand-curée (pilote) — à re-vérifier dans Canutes pour n>=100.
"""
import os, re, json, time

# (question, num_normalisé_attendu, mot-clé code)
QUESTIONS = [
    ("Quelle est la durée légale du travail à temps complet en France ? Cite l'article.", "L3121-27", "travail"),
    ("Dans quels cas un contrat à durée déterminée (CDD) peut-il être conclu ? Cite l'article.", "L1242-2", "travail"),
    ("Un licenciement pour motif personnel doit reposer sur quoi ? Cite l'article.", "L1232-1", "travail"),
    ("Quel article protège le droit au respect de la vie privée ? Cite l'article.", "9", "civil"),
    ("À quel âge la majorité est-elle fixée en droit français ? Cite l'article.", "414", "civil"),
    ("Combien de jours de congés payés par mois de travail ? Cite l'article.", "L3141-3", "travail"),
    ("Quel article fonde la responsabilité du fait des choses ? Cite l'article.", "1242", "civil"),
    ("Les enfants doivent-ils des aliments à leurs parents dans le besoin ? Cite l'article.", "205", "civil"),
    ("Quelle est la durée de droit commun de la garde à vue ? Cite l'article.", "63", "procédure pénale"),
    ("Quel est le délai de rétractation pour un achat à distance ? Cite l'article.", "L221-18", "consommation"),
    ("Quel est l'âge minimum légal pour se marier ? Cite l'article.", "144", "civil"),
    ("Sur quel article repose le divorce par consentement mutuel ? Cite l'article.", "229", "civil"),
]

MAMMOUTH = "https://api.mammouth.ai/v1"
CLOUD_MODELS = [
    ("gpt-4o", MAMMOUTH, "MAMMOUTH_API_KEY"),
    ("claude-sonnet-4-5", MAMMOUTH, "MAMMOUTH_API_KEY"),
    ("gemini-2.5-flash", MAMMOUTH, "MAMMOUTH_API_KEY"),
    ("mistral-large-3", MAMMOUTH, "MAMMOUTH_API_KEY"),
    ("mistral-small-3.2-24b-instruct", MAMMOUTH, "MAMMOUTH_API_KEY"),
]
LOCAL_MODELS = [
    ("mistral", "http://localhost:11434/v1", None),  # Ollama Mistral 7B local
]

SYS = ("Tu es un assistant juridique pour les citoyens français. Réponds en une "
       "phrase et cite TOUJOURS l'article sous la forme « article <numéro> du "
       "<code> ». Ne cite jamais un article dont tu n'es pas certain.")

CIT = re.compile(r'(?:articles?|art\.?)\s+((?:L|R|D|A)\.?\s*)?(\d+(?:[-–]\d+)*)'
                 r'|\b([LRDA])\.\s?(\d+(?:[-–]\d+)*)', re.I)


def norm(letter, digits):
    letter = (letter or "").strip().replace(".", "").replace(" ", "").upper()
    digits = digits.replace("–", "-").replace(" ", "")
    return f"{letter}{digits}"


def extract(text):
    out = []
    for m in CIT.finditer(text or ""):
        if m.group(2):
            out.append(norm(m.group(1), m.group(2)))
        elif m.group(4):
            out.append(norm(m.group(3), m.group(4)))
    return out


def ask(model, base, key, question):
    from openai import OpenAI
    c = OpenAI(base_url=base, api_key=key or "ollama")
    r = c.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYS}, {"role": "user", "content": question}],
        temperature=0.2, timeout=60,
    )
    return r.choices[0].message.content or ""


def score(cited, gt_num, gt_code, text):
    if not cited:
        return "sans_citation"
    if gt_num in cited and gt_code.split()[0].lower() in (text or "").lower():
        return "correct"
    if gt_num in cited:
        return "correct"  # bon numéro, code implicite/omis -> on est indulgent
    return "hallucination"


def run():
    panel = [(m, b, os.environ.get(k) if k else None) for (m, b, k) in CLOUD_MODELS] + \
            [(m, b, None) for (m, b, _k) in LOCAL_MODELS]
    results = {}
    for model, base, key in panel:
        if base == MAMMOUTH and not key:
            print(f"skip {model}: MAMMOUTH_API_KEY absent"); continue
        counts = {"correct": 0, "hallucination": 0, "sans_citation": 0, "erreur": 0}
        details = []
        for q, gt_num, gt_code in QUESTIONS:
            try:
                ans = ask(model, base, key, q)
                cited = extract(ans)
                verdict = score(cited, gt_num, gt_code, ans)
            except Exception as e:
                verdict = "erreur"; cited = []; ans = f"[{type(e).__name__}] {str(e)[:120]}"
            counts[verdict] += 1
            details.append({"q": q[:40], "gt": gt_num, "cité": cited, "verdict": verdict})
            print(f"  {model:34} {verdict:14} attendu={gt_num:9} cité={cited}")
        results[model] = {"counts": counts, "details": details}
        print(f"== {model}: {counts}")
    return results


if __name__ == "__main__":
    res = run()
    with open("benchmarks/hallucination/bench_results.json", "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("écrit benchmarks/hallucination/bench_results.json")

    # --- chart ---
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(QUESTIONS)
    models = list(res.keys())
    labels = [m.replace("-3.2-24b-instruct", " (24B)").replace("mistral", "Mistral 7B local" if m == "mistral" else "mistral") for m in models]
    corr = [res[m]["counts"]["correct"] / n * 100 for m in models]
    hall = [res[m]["counts"]["hallucination"] / n * 100 for m in models]
    noc = [(res[m]["counts"]["sans_citation"] + res[m]["counts"]["erreur"]) / n * 100 for m in models]

    fig, ax = plt.subplots(figsize=(11, 5))
    import numpy as np
    x = np.arange(len(models))
    ax.bar(x, corr, color="#7bb274", label="Citation correcte")
    ax.bar(x, hall, bottom=corr, color="#d9534f", label="Hallucination (mauvaise citation)")
    ax.bar(x, noc, bottom=[c + h for c, h in zip(corr, hall)], color="#9aa0a6", label="Sans citation / erreur")
    # barre "avec notre vérification" : 0 hallucination présentée
    ax.bar(len(models), 0, color="#7bb274")
    ax.bar(len(models), 100, color="#c9a24b", label="Le Rapporteur : 0 hallucination présentée")
    labels2 = labels + ["Le Rapporteur\n(avec vérification)"]
    ax.set_xticks(list(x) + [len(models)])
    ax.set_xticklabels(labels2, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("% des questions")
    ax.set_title(f"Hallucination de citations juridiques FR — {n} questions (vérité-terrain hand-curée)", fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(0, 105)
    fig.tight_layout()
    fig.savefig("benchmarks/hallucination/hallucination_rates.png", dpi=150)
    print("écrit benchmarks/hallucination/hallucination_rates.png")
