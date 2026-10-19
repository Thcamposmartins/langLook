# Arquitetura — LangChain + LangGraph Observability POC

> Documento de arquitetura de referência. Diagramas em [Mermaid](https://mermaid.js.org/) (renderizam no GitHub).

## 1. Visão geral

Assistente conversacional que classifica perguntas (técnica vs. geral) e responde via LLM local (LM Studio). A aplicação é instrumentada com métricas Prometheus e observável no Grafana. Tudo orquestrado por um grafo LangGraph.

**Características-chave**

- LLM 100% local (LM Studio, OpenAI-compatible) — sem dependência de nuvem.
- Orquestração declarativa via LangGraph (state machine).
- Observabilidade pull via Prometheus + Grafana.
- A app roda no host; Prometheus e Grafana rodam em contêineres.

## 2. Diagrama de Contexto (C4 Nível 1)

```mermaid
flowchart LR
    User([Desenvolvedor / Cliente])

    subgraph System["POC (sistema)"]
        App["Assistente LangGraph<br/>FastAPI"]
    end

    LLM[(LM Studio<br/>modelo local)]
    Prom[(Prometheus)]
    Graf[(Grafana)]

    User -->|"POST /ask<br/>GET /health"| App
    App -->|"chat/completions"| LLM
    App -->|"GET /metrics (exposição)"| Prom
    Prom -->|"scrape /metrics"| App
    Graf -->|"consulta PromQL"| Prom
    User -->|"dashboards"| Graf
```

## 3. Diagrama de Containers (C4 Nível 2)

```mermaid
flowchart TB
    subgraph Host["Host (WSL/Ubuntu)"]
        AppC["FastAPI + Uvicorn<br/>:8000<br/>app/main.py"]
        LMSC["LM Studio Server<br/>:1234"]
    end

    subgraph Docker["Rede Docker Compose"]
        PromC["Prometheus<br/>:9090"]
        GrafC["Grafana<br/>:3000"]
    end

    Client([Cliente HTTP])

    Client -->|"HTTP :8000"| AppC
    AppC -->|"OpenAI API :1234"| LMSC
    PromC -.->|"host.docker.internal:8000<br/>/metrics"| AppC
    GrafC -->|"http://prometheus:9090"| PromC
```

- `host.docker.internal` (via `extra_hosts: host-gateway`) é a ponte entre os contêineres e a app no host.
- Prometheus e Grafana compartilham a rede default do Compose, então o Grafana resolve `prometheus` por DNS interno.

## 4. Diagrama de Componentes (C4 Nível 3 — App)

```mermaid
flowchart TB
    subgraph App["FastAPI (app/)"]
        MW["HTTP Middleware<br/>main.py"]
        Routes["Rotas<br/>/health, /ask, /metrics"]
        Graph["LangGraph<br/>graph.py"]
        Metrics["metrics.py<br/>Counters/Histograms"]
        MetricsApp["make_asgi_app()<br/>endpoint /metrics"]
        LLMClient["llm.py<br/>ChatOpenAI"]
    end

    LLM[(LM Studio)]

    MW -->|"inc/observe"| Metrics
    Routes --> Graph
    Graph -->|"timed_node"| Metrics
    Graph -->|"call_llm"| LLMClient
    LLMClient -->|"invoke"| LLM
    LLMClient -->|"usage_metadata"| Metrics
    MetricsApp -->|"exposição pull"| Metrics
```

## 5. Fluxo de requisição (`POST /ask`)

```mermaid
sequenceDiagram
    participant C as Cliente
    participant F as FastAPI (middleware)
    participant G as LangGraph
    participant L as LM Studio
    participant M as Métricas

    C->>F: POST /ask {"question"}
    F->>M: start timer (perf_counter)
    F->>G: run_assistant(question)
    G->>G: classify (palavras-chave)
    G->>M: NODE_DURATION[classify]
    G->>G: route → technical|general
    G->>L: invoke (system prompt + question)
    L-->>G: response + usage_metadata
    G->>M: LLM_CALLS[success] + LLM_TOKENS[in/out]
    G->>M: NODE_DURATION[technical|general]
    G-->>F: {question, intent, answer}
    F->>M: HTTP_REQUESTS + HTTP_REQUEST_DURATION
    F-->>C: 200 AskResponse
```

## 6. Fluxo de métricas (observabilidade)

```mermaid
flowchart LR
    subgraph App["FastAPI :8000"]
        Inst["Instrumentação<br/>(Counters/Histograms)"]
        Exp["/metrics<br/>exposição pull"]
    end

    Prom["Prometheus :9090<br/>scrape_interval 15s"]
    Graf["Grafana :3000<br/>datasource provisionado"]

    Inst --> Exp
    Prom -->|"GET /metrics<br/>job: langchain-app"| Exp
    Graf -->|"PromQL"| Prom
```

**Jobs de scrape** (`observability/prometheus.yml`):

- `prometheus` → `localhost:9090` (auto-scrape).
- `langchain-app` → `host.docker.internal:8000/metrics`.

## 7. Topologia de deployment

| Camada        | Onde            | Porta | Observação                                |
|---------------|-----------------|-------|-------------------------------------------|
| FastAPI app   | Host (uvicorn)  | 8000  | Roda fora do Docker; `--reload` em dev    |
| LM Studio     | Host            | 1234  | Modelo OpenAI-compatible; CPU            |
| Prometheus    | Contêiner       | 9090  | Volume `prometheus-data`                  |
| Grafana       | Contêiner       | 3000  | Volume `grafana-data`; datasource prov.   |

```mermaid
flowchart TB
    subgraph Host["Host"]
        A["uvicorn :8000"]
        L["LM Studio :1234"]
    end
    subgraph Compose["docker compose"]
        P["prometheus :9090"]
        G["grafana :3000"]
    end
    A -- "OpenAI API" --> L
    P -. "host.docker.internal:8000" .-> A
    G -- "prometheus:9090 (DNS interno)" --> P
```

## 8. Decisões arquiteturais

| #  | Decisão                                   | Motivo                                                                                  |
|----|-------------------------------------------|-----------------------------------------------------------------------------------------|
| 1  | LLM local via LM Studio                   | POC sem custo de nuvem, dados não saem do host, baixa latência de rede.                 |
| 2  | LangGraph para orquestração               | Estado explícito, roteamento condicional e pontos naturais para instrumentar nodes.     |
| 3  | App no host, obs em contêineres           | `--reload` em dev é simples no host; observabilidade é stateless e cabe em contêiner.   |
| 3a | `host.docker.internal` como ponte        | Único jeito limpo do contêiner alcançar serviço no host (cross-platform).               |
| 4  | Métricas pull (Prometheus)                | Simples, sem agente na app; `/metrics` já vem pronto via `prometheus_client`.           |
| 5  | Provisioning declarativo do Grafana       | DataSource criado automaticamente; sem configuração manual a cada `up`.                |
| 6  | Prefixo `poc_` nas métricas               | Evita colisão com métricas de bibliotecas; fácil de filtrar.                            |
| 7  | `max_tokens=512` no LLM                   | Limita tempo de resposta em CPU (~0.25s/token) abaixo do timeout de 180s.                |
| 8  | Classificação por palavras-chave (sem LLM)| Roteamento determinístico e barato; LLM só no node de resposta.                         |

## 9. Limites e riscos

- **Disponibilidade do LM Studio**: se o servidor cair, `/ask` retorna erro (métrica `llm_calls{status="error"}`).
- **Single-node**: sem réplica nem balanceador; não é arquitetura de produção.
- **Persistência**: sem checkpointing do LangGraph; cada `/ask` é stateless.
- **Segurança**: endpoints sem autenticação; `.env` com chave dummy do LM Studio. Adequado para POC, não para exposição pública.
- **Scrape depende da app no ar**: target `langchain-app` fica DOWN se o uvicorn não estiver rodando.

## 10. Evoluções sugeridas (não implementadas)

- Checkpointing do LangGraph (memória/conversa multi-turno).
- Tracing distribuído (OpenTelemetry + Tempo/Jaeger) — dependências já presentes.
- Conteinerização da app e `docker compose` único.
- Auth no `/ask` (API key) e TLS no uvicorn.
- Alertas no Prometheus (`alertmanager`) e dashboards provisionados via `dashboards/`.
