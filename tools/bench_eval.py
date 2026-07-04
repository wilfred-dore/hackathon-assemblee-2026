#!/usr/bin/env python3
"""Mini-benchmark n=100 pour Le Rapporteur (donnees REELLES, jamais inventees).

Rejoue un jeu de questions citoyennes a travers le pipeline
`answer_question` et mesure des metriques HONNETES et bien definies :

  * fuite de fabrication  = reponse "ok" contenant une citation non verifiee
    (invariant central : doit valoir 0 ; verifie empiriquement) ;
  * taux de refus         = part des questions ou le systeme refuse ;
  * garde-fou declenche   = refus provoques par >=1 citation non resolue
    (le modele a invente/mal cite, la base l'a attrape) ;
  * sous-ensembles        = taux de reponse sur les questions "answerable",
    taux de refus sur les "trap" ;
  * latence               = mediane / p95 end-to-end, debit median (tokens/s).

Sorties :
  * results.json  : une ligne par question (repro / annexe) + resume ;
  * metrics.tex   : macros LaTeX \\eval... consommees par sections/eval.tex.

Les chiffres proviennent EXCLUSIVEMENT de l'execution : en mode demo ils sont
insignifiants (LLM canned) ; lancer avec un .env MODE=live pour de vraies
donnees. L'en-tete de metrics.tex indique toujours mode/backend/date.

Usage :
    uv run python tools/bench_eval.py                 # tout le jeu
    uv run python tools/bench_eval.py --limit 8       # dry-run rapide
    uv run python tools/bench_eval.py --sleep 0.3     # throttle anti rate-limit
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from datetime import date

# Racine du repo sur le sys.path (le script vit dans tools/).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.config import CONFIG  # noqa: E402
from src.llm.client import LLMClient  # noqa: E402
from src.pipeline import answer_question  # noqa: E402
from src.verify import default_verifier  # noqa: E402

DEFAULT_QUESTIONS = os.path.join(_ROOT, "paper", "eval", "questions.jsonl")
DEFAULT_OUT = os.path.join(_ROOT, "paper", "eval", "results.json")
DEFAULT_TEX = os.path.join(_ROOT, "paper", "eval", "metrics.tex")


def load_questions(path: str) -> list[dict]:
    items: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def _percentile(xs: list[float], p: float) -> float:
    """Percentile (interpolation lineaire). p dans [0, 1]."""
    if not xs:
        return 0.0
    ys = sorted(xs)
    k = (len(ys) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ys[int(k)]
    return ys[lo] + (ys[hi] - ys[lo]) * (k - lo)


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    n = len(ys)
    mid = n // 2
    return ys[mid] if n % 2 else (ys[mid - 1] + ys[mid]) / 2


def run(items: list[dict], sleep: float = 0.0) -> list[dict]:
    llm = LLMClient()
    verifier = default_verifier()
    rows: list[dict] = []
    total = len(items)
    for i, item in enumerate(items, 1):
        q = item["question"]
        t0 = time.perf_counter()
        try:
            ans = answer_question(q, llm=llm, verifier=verifier)
            dt = time.perf_counter() - t0
            cits = ans.citations
            n_cit = len(cits)
            n_verified = sum(1 for c in cits if c.get("exists"))
            n_failed = n_cit - n_verified
            invented = list(ans.validation.get("invented", []))
            m = llm.last_metrics or {}
            row = {
                "id": item.get("id", i),
                "category": item.get("category", "?"),
                "question": q,
                "status": ans.status,
                "n_citations": n_cit,
                "n_verified": n_verified,
                "n_failed": n_failed,
                "invented": invented,
                # fuite : une reponse "ok" ne DOIT jamais porter de citation non verifiee
                "leaked": ans.status == "ok" and n_failed > 0,
                # garde-fou declenche : refus cause par au moins une citation KO
                "guard_fired": ans.status != "ok" and n_failed > 0,
                "verifier_source": (cits[0]["source"] if cits else None),
                "latency_s": round(dt, 3),
                "llm_latency_s": m.get("latency_s"),
                "tokens_per_s": m.get("tokens_per_s"),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 — un appel reseau KO ne casse pas le run
            dt = time.perf_counter() - t0
            row = {
                "id": item.get("id", i),
                "category": item.get("category", "?"),
                "question": q,
                "status": "error",
                "n_citations": 0, "n_verified": 0, "n_failed": 0,
                "invented": [], "leaked": False, "guard_fired": False,
                "verifier_source": None, "latency_s": round(dt, 3),
                "llm_latency_s": None, "tokens_per_s": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
        rows.append(row)
        flag = {"ok": "OK ", "refus": "REF", "error": "ERR"}.get(row["status"], "???")
        print(f"[{i:>3}/{total}] {flag} {row['category']:<10} "
              f"cit={row['n_verified']}/{row['n_citations']} "
              f"{row['latency_s']:>6.2f}s  {q[:58]}")
        if sleep:
            time.sleep(sleep)
    return rows


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    graded = [r for r in rows if r["status"] != "error"]
    answered = [r for r in graded if r["status"] == "ok"]
    refused = [r for r in graded if r["status"] == "refus"]
    errors = [r for r in rows if r["status"] == "error"]

    def cat(name: str) -> list[dict]:
        return [r for r in graded if r["category"] == name]

    answerable, trap, opn = cat("answerable"), cat("trap"), cat("open")
    lat = [r["latency_s"] for r in graded]
    tokps = [r["tokens_per_s"] for r in graded if r["tokens_per_s"]]
    distinct_invented = sorted({lbl for r in rows for lbl in r["invented"]})
    sources = Counter(r["verifier_source"] for r in graded if r["verifier_source"])

    def rate(part: int, whole: int) -> float:
        return round(100.0 * part / whole, 1) if whole else 0.0

    return {
        "n": n,
        "graded": len(graded),
        "errors": len(errors),
        "answered": len(answered),
        "refused": len(refused),
        "refusal_rate_pct": rate(len(refused), len(graded)),
        "leak_count": sum(1 for r in graded if r["leaked"]),
        "guard_fired_count": sum(1 for r in graded if r["guard_fired"]),
        "distinct_invented": distinct_invented,
        "distinct_invented_count": len(distinct_invented),
        "citations_total": sum(r["n_citations"] for r in graded),
        "citations_verified": sum(r["n_verified"] for r in graded),
        "citations_failed": sum(r["n_failed"] for r in graded),
        "answerable_n": len(answerable),
        "answerable_answered": sum(1 for r in answerable if r["status"] == "ok"),
        "answerable_answer_rate_pct": rate(sum(1 for r in answerable if r["status"] == "ok"), len(answerable)),
        "trap_n": len(trap),
        "trap_refused": sum(1 for r in trap if r["status"] == "refus"),
        "trap_refusal_rate_pct": rate(sum(1 for r in trap if r["status"] == "refus"), len(trap)),
        "open_n": len(opn),
        "open_answered": sum(1 for r in opn if r["status"] == "ok"),
        "latency_median_s": round(_median(lat), 2),
        "latency_p95_s": round(_percentile(lat, 0.95), 2),
        "tokens_per_s_median": round(_median(tokps), 1) if tokps else None,
        "verifier_source_top": (sources.most_common(1)[0][0] if sources else None),
        "mode": CONFIG.mode,
        "backend_host": (CONFIG.llm_base_url or "").split("//")[-1].split("/")[0] or "demo (offline)",
        "model": CONFIG.llm_model or "LLM demo (offline)",
        "date": date.today().isoformat(),
    }


def _tex_escape(s: str) -> str:
    return str(s).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def write_tex(path: str, s: dict) -> None:
    """Emet les macros LaTeX \\eval... (chiffres reels du run)."""
    def pct(x: float) -> str:
        return f"{x:g}\\%"

    live = s["mode"] == "live"
    # Bandeau injecte dans le PDF UNIQUEMENT en mode demo (chiffres placeholders).
    banner_demo = (
        r"\newcommand{\evalModeBanner}{\par\noindent\fbox{\parbox{0.95\linewidth}"
        r"{\small\textbf{[DRAFT --- DEMO NUMBERS]} The figures in this section come "
        r"from an offline canned model and are placeholders. Run the pipeline with "
        r"\texttt{MODE=live} (real LLM + Canutes verifier) to populate measured "
        r"results.}}\par\medskip}"
    )
    banner_live = r"\newcommand{\evalModeBanner}{}"
    lines = [
        "% GENERATED by tools/bench_eval.py — DO NOT EDIT BY HAND.",
        f"% mode={s['mode']}  backend={s['backend_host']}  model={s['model']}  date={s['date']}",
        f"% {'DONNEES LIVE' if live else 'DRY-RUN DEMO — chiffres NON significatifs (LLM canned)'}.",
        banner_live if live else banner_demo,
        r"\newcommand{\evalN}{%d}" % s["n"],
        r"\newcommand{\evalGraded}{%d}" % s["graded"],
        r"\newcommand{\evalErrors}{%d}" % s["errors"],
        r"\newcommand{\evalAnswered}{%d}" % s["answered"],
        r"\newcommand{\evalRefused}{%d}" % s["refused"],
        r"\newcommand{\evalRefusalRate}{%s}" % pct(s["refusal_rate_pct"]),
        r"\newcommand{\evalLeak}{%d}" % s["leak_count"],
        r"\newcommand{\evalGuardFired}{%d}" % s["guard_fired_count"],
        r"\newcommand{\evalDistinctInvented}{%d}" % s["distinct_invented_count"],
        r"\newcommand{\evalCitTotal}{%d}" % s["citations_total"],
        r"\newcommand{\evalCitVerified}{%d}" % s["citations_verified"],
        r"\newcommand{\evalCitFailed}{%d}" % s["citations_failed"],
        r"\newcommand{\evalAnswerableN}{%d}" % s["answerable_n"],
        r"\newcommand{\evalAnswerableAnswered}{%d}" % s["answerable_answered"],
        r"\newcommand{\evalAnswerableRate}{%s}" % pct(s["answerable_answer_rate_pct"]),
        r"\newcommand{\evalTrapN}{%d}" % s["trap_n"],
        r"\newcommand{\evalTrapRefused}{%d}" % s["trap_refused"],
        r"\newcommand{\evalTrapRate}{%s}" % pct(s["trap_refusal_rate_pct"]),
        r"\newcommand{\evalOpenN}{%d}" % s["open_n"],
        r"\newcommand{\evalOpenAnswered}{%d}" % s["open_answered"],
        r"\newcommand{\evalLatMedian}{%s}" % f"{s['latency_median_s']:g}",
        r"\newcommand{\evalLatPToNine}{%s}" % f"{s['latency_p95_s']:g}",
        r"\newcommand{\evalTokps}{%s}" % (f"{s['tokens_per_s_median']:g}" if s["tokens_per_s_median"] else "n/a"),
        r"\newcommand{\evalMode}{%s}" % _tex_escape(s["mode"]),
        r"\newcommand{\evalBackend}{%s}" % _tex_escape(s["backend_host"]),
        r"\newcommand{\evalModel}{%s}" % _tex_escape(s["model"]),
        r"\newcommand{\evalVerifier}{%s}" % _tex_escape(s["verifier_source_top"] or "n/a"),
        r"\newcommand{\evalDate}{%s}" % _tex_escape(s["date"]),
        "",
    ]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description="Mini-benchmark n=100 (donnees reelles).")
    ap.add_argument("--questions", default=DEFAULT_QUESTIONS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--tex", default=DEFAULT_TEX)
    ap.add_argument("--limit", type=int, default=0, help="0 = tout le jeu")
    ap.add_argument("--sleep", type=float, default=0.0, help="pause entre appels (anti rate-limit)")
    args = ap.parse_args()

    items = load_questions(args.questions)
    if args.limit:
        items = items[: args.limit]

    banner = "LIVE" if CONFIG.is_live else "DEMO (hors-ligne, chiffres non significatifs)"
    print(f"== Le Rapporteur — benchmark n={len(items)} — mode {banner} ==")
    if not CONFIG.is_live:
        print("!! MODE=demo : renseigne .env (MODE=live + LLM_* + verificateur) pour de vraies donnees.\n")

    rows = run(items, sleep=args.sleep)
    s = summarize(rows)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"summary": s, "rows": rows}, fh, ensure_ascii=False, indent=2)
    write_tex(args.tex, s)

    print("\n== RESUME ==")
    print(f"  n={s['n']}  gradees={s['graded']}  erreurs={s['errors']}")
    print(f"  repondu={s['answered']}  refuse={s['refused']}  (taux refus {s['refusal_rate_pct']}%)")
    print(f"  FUITE de fabrication (doit=0) : {s['leak_count']}")
    print(f"  garde-fou declenche : {s['guard_fired_count']}  | articles inventes distincts : {s['distinct_invented_count']}")
    print(f"  citations : {s['citations_verified']}/{s['citations_total']} verifiees ({s['citations_failed']} KO)")
    print(f"  answerable : {s['answerable_answered']}/{s['answerable_n']} repondues ({s['answerable_answer_rate_pct']}%)")
    print(f"  trap       : {s['trap_refused']}/{s['trap_n']} refusees ({s['trap_refusal_rate_pct']}%)")
    print(f"  latence    : mediane {s['latency_median_s']}s  p95 {s['latency_p95_s']}s  | {s['tokens_per_s_median']} tok/s")
    print(f"  backend    : {s['backend_host']}  modele {s['model']}  verif {s['verifier_source_top']}")
    print(f"\n  -> {args.out}\n  -> {args.tex}")


if __name__ == "__main__":
    main()
