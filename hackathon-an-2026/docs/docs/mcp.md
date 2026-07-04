# Schéma réel des outils MCP

> ⚠️ À REMPLIR SUR PLACE. Ne pas inventer la forme des tools/params.
> Une fois les endpoints/token dispo, capturer la sortie de `describe` :
>
> ```bash
> uv run python -c "from src.mcp.client import moulineuse; import json; print(json.dumps(moulineuse().describe_tools(), indent=2, ensure_ascii=False))"
> ```
>
> Puis coller le JSON ci-dessous et adapter `retrieve()` dans
> [../src/pipeline.py](../src/pipeline.py) (nom réel de l'outil de recherche,
> forme des arguments et des résultats).

## Moulineuse — outils exposés
_(à coller)_

## Parlement — outils exposés
_(à coller)_

## Notes d'auth
_(Bearer ? header custom ? négociation de session `initialize` ? — voir TODO(auth) dans [../src/mcp/client.py](../src/mcp/client.py))_
