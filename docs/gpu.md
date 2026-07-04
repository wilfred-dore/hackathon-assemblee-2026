# Stratégie GPU / inférence — hardware-agnostique & souverain

> L'orga ne fournit **pas** d'endpoint d'inférence. On l'amène. Angle : **la couche
> de confiance est indépendante du matériel** — même pipeline, on swappe le backend
> en changeant `LLM_BASE_URL`. `src/llm/client.py` est OpenAI-compatible → changer 3
> variables `.env` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) suffit.

## Ce qui est déjà prouvé (2026-07-04)

| Backend | Matériel | Statut |
|---|---|---|
| Mistral La Plateforme 🇫🇷 | cloud souverain FR | ✅ live |
| Ollama, Mistral 7B | **Apple Silicon (M2 Pro)**, 100 % local | ✅ live |
| Qualcomm Cloud AI 100 (Cirrascale) | Qualcomm, Llama-3.1-8B | ✅ live (essai gratuit) |
| Kernel Mojo natif arm64 | Apple Silicon | ✅ committé ([`examples/mojo/`](../examples/mojo/)) |

⚠️ L'endpoint Qualcomm testé est l'**essai gratuit Cirrascale** (instance partagée) →
non représentatif du Cloud AI 100 Ultra. Ne pas en tirer de conclusion de perf.

## Où louer, et tout piloter par API

### GPU serveur (pour un vrai comparatif)
| Matériel | À partir de | Fournisseurs faciles (API/on-demand) |
|---|---|---|
| **AMD MI300X** | ~0,95–2,00 $/h | DigitalOcean (~1,99 $), RunPod, Vultr, TensorWave, Crusoe, Oracle, HotAisle |
| **NVIDIA H100 / H200** | ~3,39–3,44 $/h | Vast.ai, RunPod, Lambda, Crusoe, la plupart |
| **NVIDIA B200 / B300** | ~3,44–7,92 $/h | Vast.ai (le moins cher), Oracle, GCP |

→ Un comparatif **apples-to-apples** coûte quelques dollars : ~1 h de MI300X (~2 $) +
~1 h de H100 (~3,4 $). Réservé = -30 à -40 % si besoin de plus.

### Qualcomm Cloud AI 100 — pilotable par API
- **Playground gratuit** : <https://cloudai.cirrascale.com/> (Llama-3.1-8B/70B, SDXL
  Turbo). On l'utilise déjà.
- **Qualcomm AI Inference Suite** : **SDK Python + API OpenAI-compatibles** → se branche
  direct sur notre `LLMClient`. Doc dev Qualcomm.
- **Cloud AI SDK** (open source) : <https://github.com/quic/cloud-ai-sdk>.
- Cartes dispo chez **AWS** et **Cirrascale** (1 à 8 accélérateurs/instance).

### Alternative « devices in the loop » (ton idée)
- **Qualcomm Device Cloud (QDC)** : accès distant à de **vrais devices** (Dragonwing
  RB3 Gen 2…), **5000 min gratuits**. Plutôt edge/Snapdragon que Cloud AI 100, mais
  parfait pour l'axe **PC de bureau : Apple vs Snapdragon X Elite**.
- **Ton MacBook (M2 Pro)** : déjà le pied dans la porte Apple Silicon (Mojo + Ollama).

## Le comparatif propre à faire (apples-to-apples)

Deux tableaux, **même modèle** (p.ex. Mistral-7B open-weight), même prompt, même charge :

1. **Serveur / on-premise** : NVIDIA (vLLM) vs AMD MI300X (vLLM/ROCm **et** MAX) vs
   Qualcomm Cloud AI 100 (AI Inference Suite). Mesurer latence, débit, **et perf/watt**.
2. **Bureau** : Apple Silicon (MAX/Ollama) vs Snapdragon X Elite (via QDC).

**Protocole reproductible** (loue 1 GPU, ~1 h) :
```bash
# sur l'instance louée (MI300X ou H100)
# 1) vLLM (baseline)
pip install vllm && vllm serve mistralai/Mistral-7B-Instruct-v0.3 --port 8000
# 2) MAX (même modèle, même port après arrêt de vLLM)
pip install modular && max serve --model mistralai/Mistral-7B-Instruct-v0.3
# 3) on pointe notre bench vendor-agnostique dessus
LLM_BASE_URL=http://<ip>:8000/v1 LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.3 make bench
```
→ produit latence + tokens/s comparables. Reporter dans `benchmarks/` + le papier.

## MAX vs vLLM — état honnête
- **Références** : perfs Mojo ~87 % CUDA (H100), parité HIP (AMD MI300A), arXiv 2509.21039.
- **Expérience perso (hackathon AMD ROCm 2025)** : MAX ne donnait pas encore des
  résultats extraordinaires — mais le tooling a bougé (MAX 26.x, GPU Apple Silicon
  ajouté) et on peut refaire l'essai avec de l'assistance agentique.
- **Position** : on ne prétend pas que MAX bat vLLM. On mesure, on publie, on reste
  agnostique. Le comparatif ci-dessus tranchera avec des chiffres à nous.

## Secrets
Clés/tokens (Qualcomm, Mammouth, Mistral, GPU loués) **uniquement dans `.env`**
(gitignored). Jamais dans le chat, le code, ou ce fichier.
