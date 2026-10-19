# LangChain + LangGraph Observability POC

POC de assistente com LangGraph que classifica perguntas (técnica vs. geral), responde via LLM local (LM Studio) e expõe métricas Prometheus observáveis no Grafana.

## Stack

- Python · FastAPI · Uvicorn
- LangChain + LangGraph (LangChain + LangGraph Observability POC)
- LLM local via LM Studio (OpenAI-compatible)
- Prometheus + Grafana (Docker Compose)

## Pré-requisitos

- Python 3.11+
- Docker + Docker Compose
- LM Studio rodando um modelo na rede do host

## Variáveis de ambiente (`.env`)

```
LM_STUDIO_BASE_URL=http://<host>:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=qwen2.5-coder-1.5b-instruct
LM_STUDIO_MAX_TOKENS=512
LM_STUDIO_TIMEOUT=180
```

## Executando

```bash
source .venv/bin/activate
pip install -r requirements.txt

# Observabilidade (Prometheus + Grafana)
docker compose up -d

# App (porta 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

| Método | Rota        | Descrição                          |
|--------|-------------|------------------------------------|
| GET    | `/health`   | Healthcheck                        |
| POST   | `/ask`      | `{ "question": "..." }`            |
| GET    | `/metrics`  | Métricas no formato Prometheus     |

## Observabilidade

- Prometheus: http://localhost:9090 (targets em `/targets`)
- Grafana: http://localhost:3000 (admin / admin)

O Prometheus faz scrape da app em `host.docker.internal:8000`, então a app precisa estar rodando para os targets aparecerem como UP. O datasource do Grafana é provisionado automaticamente.

## Métricas expostas

| Métrica                                  | Tipo       | Labels                         |
|------------------------------------------|------------|--------------------------------|
| `poc_http_requests_total`                | Counter    | method, endpoint, status       |
| `poc_http_request_duration_seconds`      | Histogram  | method, endpoint               |
| `poc_langgraph_runs_total`                | Counter    | status                         |
| `poc_langgraph_node_duration_seconds`     | Histogram  | node                           |
| `poc_llm_calls_total`                    | Counter    | node, status                   |
| `poc_llm_tokens_total`                    | Counter    | direction                      |

## Fluxo

```
/ask → classify → (technical | general) → call_llm → resposta
```

`classify` decide o intent por palavras-chave; `technical` e `general` consultam o LLM com system prompts distintos.
