# Stratégie GPU / LLM — hardware-agnostique & souverain

> L'orga ne fournit **pas** d'endpoint d'inférence (cf. [ressources.md](ressources.md)).
> On l'amène. Angle de démo : **la couche de confiance est indépendante du
> matériel** — même pipeline, on swappe le backend en changeant `LLM_BASE_URL`.

## Le principe (déjà câblé)
`src/llm/client.py` est un client **OpenAI-compatible**. Changer de backend =
changer 3 variables `.env` : `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
Rien à recoder → le swap est démontrable **en direct sur scène**.

## Backends visés (par ordre de préférence démo)

| # | Backend | Matériel | Modèle | Souverain ? | Statut |
|---|---|---|---|---|---|
| 1 | **Modular MAX** (`modular/max-openai-api`) | **AMD** (Instinct, distant) | Mistral (open-weight) | ✅ | à obtenir (crédits AMD Dev Cloud ~100$, ou orga) |
| 2 | **Qualcomm Cloud AI 100** via Cirrascale AI Suite | Qualcomm | **Llama-3.1-8B** (pas de Mistral) | ✅ | ✅ **CONFIRMÉ LIVE** — OpenAI-compat OK |
| 3 | **Colab (Google AI One / Pro)** | NVIDIA (L4/A100) | Mistral via MAX ou vLLM | ✅ (open-weight auto-hébergé) | fallback fiable |

### Backend #2 confirmé (Qualcomm Cloud AI 100 / Cirrascale)
- `LLM_BASE_URL=https://aisuite.cirrascale.com/apis/v2` · `LLM_MODEL=Llama-3.1-8B`
  · auth `Authorization: Bearer <clé>` (dans `.env`).
- `GET /models` → `llm:[Llama-3.1-8B]`, embeddings BAAI, image sdxl-turbo.
- `POST /chat/completions` = format OpenAI standard → marche direct avec `LLMClient`.
- ⚠️ Mistral non servi (nom rejeté) → pour Mistral, backend #1 (AMD/MAX) ou #3 (Colab).
- 💡 Démo : en live, Llama a cité un **faux** article (L.3132-2 au lieu de
  L.3121-27) → capté par la vérification. Preuve d'hallucination souveraine réelle.

**Le récit qui gagne** : « notre assistant de confiance tourne, sans changer une
ligne, sur **AMD (MAX/Mojo)** *et* sur **Qualcomm Cloud AI 100** — souveraineté +
frugalité, indépendant du fournisseur ». Le swap live = la preuve.

## Décision
- **Cible principale** : MAX-sur-AMD (#1) — c'est l'angle Mojo/MAX à valoriser.
- **Second backend pour le swap** : Qualcomm Cloud AI 100 (#2). Même si le
  playground n'expose que **Llama**, l'argument hardware-agnostique tient (Llama
  sur Qualcomm ⇄ Mistral sur AMD). Si Mistral passe sur Qualcomm : bonus.
- **Filet de sécurité démo** : Colab via Google AI One (#3) — auto-héberger
  Mistral (MAX ou vLLM) → endpoint OpenAI-compat, garde la souveraineté (poids
  ouverts, on héberge). À défaut, un notebook Jupyter qui joue tout le pipeline.

## À vérifier / TODO
- [ ] Qualcomm playground : URL, expose-t-il `/v1/chat/completions` ? modèles ?
- [ ] MAX-sur-AMD : obtenir l'accès (orga ? AMD Dev Cloud ?) + nom du modèle.
- [ ] Colab : notebook qui sert Mistral en OpenAI-compat (MAX container ou vLLM).
- [ ] Mesurer latence + tokens/s (+ watt si dispo) par backend → panneau frugalité.

## ⚠️ Secrets
Clés/tokens (Qualcomm, Google, MAX) **uniquement dans `.env`** (gitignored).
Ne jamais les coller dans le chat, le code, ou ce fichier.
