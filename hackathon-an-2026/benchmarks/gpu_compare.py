"""Comparaison apples-to-apples des moteurs d'inférence (vLLM vs MAX) par matériel.

Tape un endpoint OpenAI-compatible en STREAMING pour mesurer :
  - TTFT (time-to-first-token) : réactivité perçue
  - débit de génération (tokens/s, hors TTFT)
  - latence totale
Écrit/complète un JSON de résultats pour le graphique final.

Usage (une invocation par cellule de la matrice) :
  python benchmarks/gpu_compare.py \
    --base-url https://<pod>-8000.proxy.runpod.net/v1 --api-key demo \
    --model mistralai/Mistral-7B-Instruct-v0.3 \
    --tier "cloud" --hardware "NVIDIA H100" --engine "vLLM" \
    --runs 3 --out benchmarks/gpu_results.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

PROMPTS = [
    "Quelle est la durée légale du travail en France ? Cite l'article.",
    "Dans quels cas peut-on conclure un CDD ? Réponds en trois phrases.",
    "Que dit le Code civil sur le respect de la vie privée ?",
    "Explique en quatre phrases la navette parlementaire d'un projet de loi.",
]


def bench_once(client, model: str, prompt: str, max_tokens: int) -> dict:
    t0 = time.perf_counter()
    ttft = None
    n_chunks = 0
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and (chunk.choices[0].delta.content or ""):
            if ttft is None:
                ttft = time.perf_counter() - t0
            n_chunks += 1
    total = time.perf_counter() - t0
    gen_time = total - (ttft or 0.0)
    # n_chunks ~ n tokens en pratique (1 chunk = 1 token pour vLLM/MAX)
    return {
        "ttft_s": round(ttft or 0.0, 3),
        "total_s": round(total, 3),
        "tokens": n_chunks,
        "tok_per_s": round(n_chunks / gen_time, 1) if gen_time > 0 and n_chunks else 0.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--api-key", default="demo")
    ap.add_argument("--model", required=True)
    ap.add_argument("--tier", required=True, help="cloud | on-premise | local")
    ap.add_argument("--hardware", required=True, help='ex. "NVIDIA H100", "AMD MI300X", "Apple M2 Pro"')
    ap.add_argument("--engine", required=True, help="vLLM | MAX | Ollama")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--out", default="benchmarks/gpu_results.json")
    args = ap.parse_args()

    from openai import OpenAI
    client = OpenAI(base_url=args.base_url, api_key=args.api_key, timeout=180)

    # warmup (chargement KV/caches, ne compte pas)
    bench_once(client, args.model, "Bonjour", 16)

    ttfts, tpss, totals = [], [], []
    for p in PROMPTS:
        for _ in range(args.runs):
            r = bench_once(client, args.model, p, args.max_tokens)
            print(f"  {p[:44]:46} ttft={r['ttft_s']:.2f}s  {r['tok_per_s']:.1f} tok/s  ({r['tokens']} tok)")
            if r["tokens"]:
                ttfts.append(r["ttft_s"]); tpss.append(r["tok_per_s"]); totals.append(r["total_s"])

    entry = {
        "tier": args.tier,
        "hardware": args.hardware,
        "engine": args.engine,
        "model": args.model,
        "runs_per_prompt": args.runs,
        "n_prompts": len(PROMPTS),
        "ttft_s_median": round(statistics.median(ttfts), 3) if ttfts else None,
        "tok_per_s_median": round(statistics.median(tpss), 1) if tpss else None,
        "total_s_median": round(statistics.median(totals), 3) if totals else None,
    }
    out = Path(args.out)
    data = json.loads(out.read_text()) if out.exists() else []
    data = [e for e in data if not (e["hardware"] == entry["hardware"] and e["engine"] == entry["engine"] and e["model"] == entry["model"])]
    data.append(entry)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n=> {entry['hardware']} · {entry['engine']} : TTFT {entry['ttft_s_median']}s · {entry['tok_per_s_median']} tok/s (médianes) — écrit dans {out}")


if __name__ == "__main__":
    main()
