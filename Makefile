# Hackathon Assemblée 2026 — commandes rapides
# uv gère l'env Python (.venv créé automatiquement).

.PHONY: setup smoke bdd db env clean

setup:        ## Crée l'env + installe les deps minimales
	uv sync
	@test -f .env || (cp .env.example .env && echo "-> .env créé depuis .env.example (à remplir)")

smoke:        ## Smoke test end-to-end (mode mock, sans vraies clés)
	uv run python -m src.cli

bdd:          ## Scénarios Gherkin (behave)
	uv run behave

db:           ## Ajoute l'accès PostgreSQL direct (optionnel : psycopg)
	uv sync --extra db

env:          ## Rappel : copie le template d'env
	cp -n .env.example .env && echo "-> .env prêt (à remplir)"

clean:        ## Nettoie caches Python
	rm -rf .venv .pytest_cache **/__pycache__

help:         ## Liste les commandes
	@grep -E '^[a-z]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'
