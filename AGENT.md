# AGENT.md

Orientações para agentes trabalhando neste repositório.

## Layout

```
app/
  main.py      # FastAPI: monta /metrics, middleware HTTP, rotas /health e /ask
  graph.py     # LangGraph: classify → technical|general → END
  llm.py       # ChatOpenAI apontando para LM Studio (host)
  metrics.py   # Counters/Histograms + make_asgi_app()
observability/
  prometheus.yml                        # scrape configs
  grafana/provisioning/datasources/     # datasource Prometheus
docker-compose.yml                      # prometheus + grafana
```

## Convenções

- Prefixo `poc_` em todas as métricas Prometheus.
- Métricas são definidas em `app/metrics.py` e consumidas em `graph.py` e `main.py`. Nunca defina uma métrica nova fora de `metrics.py`.
- A app roda no host (uvicorn porta 8000), não no Docker. Os contêineres a alcançam via `host.docker.internal`.
- LangGraph nodes são envolvidos por `timed_node()` para medir duração.

## Como adicionar uma métrica

1. Declare em `app/metrics.py` (Counter ou Histogram).
2. Incremente/observe no ponto de uso (`graph.py` ou `main.py`).
3. Não precisa registrar nada: `make_asgi_app()` expõe automaticamente.

## Como adicionar um node do LangGraph

1. Crie a função em `graph.py` recebendo `state: AssistantState`.
2. Registre com `builder.add_node("nome", timed_node("nome", func))`.
3. Conecte com `add_edge` / `add_conditional_edges`.

