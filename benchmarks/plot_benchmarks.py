"""Graphiques de benchmark — Le Rapporteur.

Données RÉELLES mesurées sur un MacBook M2 Pro (16 Go) le 2026-07-04.
Reproduire :  uv run --with matplotlib python benchmarks/plot_benchmarks.py
Sorties :     benchmarks/compute_kernel.png , benchmarks/llm_backends.png

Honnêteté : latences LLM = bout-en-bout sur une réponse courte (~33-39 tokens),
réseau inclus pour les backends cloud → chiffres conservateurs, pas un classement
définitif. Le kernel de calcul, lui, est mesuré en local sans réseau.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GOLD = "#c9a24b"
BLUE = "#5b8cff"
GREY = "#9aa0a6"
INK = "#1a1a1a"

plt.rcParams.update({
    "font.size": 12,
    "axes.edgecolor": "#cccccc",
    "axes.grid": True,
    "grid.color": "#eeeeee",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

# --- Graphique 1 : kernel de similarité RAG (100 000 comparaisons, dim 384) ---
labels1 = ["Python pur", "Mojo\n(SIMD, natif arm64)", "NumPy\n(BLAS multi-thread)"]
ms1 = [850.0, 7.6, 2.9]
colors1 = [GREY, GOLD, BLUE]

fig, ax = plt.subplots(figsize=(7.5, 4.4))
bars = ax.bar(labels1, ms1, color=colors1, width=0.6)
ax.set_yscale("log")
ax.set_ylabel("Temps (ms, échelle log) — plus bas = mieux")
ax.set_title("Kernel de similarité cosinus sur Apple Silicon (M2 Pro)\n100 000 comparaisons · dim 384", fontweight="bold")
for b, v in zip(bars, ms1):
    ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:g} ms",
            ha="center", va="bottom", fontweight="bold")
ax.text(1, 26, "114× vs Python pur", ha="center", color="#a97f22", fontsize=11, fontweight="bold")
ax.annotate("code façon Python,\nvitesse native, sans BLAS vendeur",
            xy=(1, 7.6), xytext=(1.55, 60),
            fontsize=9.5, color="#555",
            arrowprops=dict(arrowstyle="->", color="#999"))
fig.tight_layout()
fig.savefig("benchmarks/compute_kernel.png", dpi=160)
print("écrit benchmarks/compute_kernel.png")

# --- Graphique 2 : backends LLM souverains (même prompt, même pipeline) ---
backends = ["Mistral\nLa Plateforme (FR)", "Ollama local\nMistral 7B (M2)", "Qualcomm\nCloud AI 100"]
latency = [0.86, 1.21, 1.49]      # s, bout-en-bout
tokps = [39.4, 32.3, 22.1]        # tokens/s
colors2 = [BLUE, GOLD, "#7bb274"]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.5, 4.4))

b1 = axL.bar(backends, latency, color=colors2, width=0.62)
axL.set_ylabel("Latence bout-en-bout (s) — plus bas = mieux")
axL.set_title("Latence", fontweight="bold")
for b, v in zip(b1, latency):
    axL.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:g} s", ha="center", va="bottom", fontweight="bold")

b2 = axR.bar(backends, tokps, color=colors2, width=0.62)
axR.set_ylabel("Débit (tokens/s) — plus haut = mieux")
axR.set_title("Débit", fontweight="bold")
for b, v in zip(b2, tokps):
    axR.text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:g}", ha="center", va="bottom", fontweight="bold")

fig.suptitle("Le même pipeline, trois backends souverains — swap par variable d'env",
             fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig("benchmarks/llm_backends.png", dpi=160, bbox_inches="tight")
print("écrit benchmarks/llm_backends.png")

# --- Graphique 3 : frugalité (efficacité énergétique) — donnée EXTERNE citée ---
# Source : UCSD, arXiv 2507.00418. Qualcomm Cloud AI 100 = 10 à 35x moins d'énergie
# qu'un NVIDIA A100 (12 LLM open source). On ne mesure PAS le watt nous-mêmes : on cite.
fig, ax = plt.subplots(figsize=(7.5, 4.4))
xs = ["NVIDIA A100\n(référence)", "Qualcomm\nCloud AI 100"]
mid = [1, 22.5]                      # A100 = 1x ; Qualcomm = milieu de 10-35x
err = [[0, 12.5], [0, 12.5]]         # barre d'incertitude 10-35x pour Qualcomm
b = ax.bar(xs, mid, color=["#9aa0a6", "#7bb274"], width=0.55,
           yerr=err, capsize=8, error_kw=dict(ecolor="#4a4a4a", lw=1.5))
ax.set_ylabel("Efficacité énergétique (× vs A100) — plus haut = plus frugal")
ax.set_title("Frugalité de l'inférence (d'après UCSD, arXiv 2507.00418)", fontweight="bold")
ax.text(0, 1 + 1.2, "1×", ha="center", fontweight="bold")
ax.text(1, 35 + 1.2, "10 à 35× moins d'énergie", ha="center", color="#3d7a4d", fontweight="bold")
ax.set_ylim(0, 42)
ax.text(0.5, -10, "Donnée externe citée, non mesurée par nous — 12 LLM open source.",
        ha="center", transform=ax.transData, fontsize=8.5, color="#777")
fig.tight_layout()
fig.savefig("benchmarks/energy_efficiency.png", dpi=160, bbox_inches="tight")
print("écrit benchmarks/energy_efficiency.png")
