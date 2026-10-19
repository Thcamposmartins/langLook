from prometheus_client import Counter, Histogram, make_asgi_app


# Quantidade de requisições HTTP
HTTP_REQUESTS = Counter(
    "poc_http_requests_total",
    "Total de requisições HTTP",
    ["method", "endpoint", "status"],
)


# Tempo das requisições HTTP
HTTP_REQUEST_DURATION = Histogram(
    "poc_http_request_duration_seconds",
    "Tempo das requisições HTTP",
    ["method", "endpoint"],
)


# Execuções do LangGraph
GRAPH_RUNS = Counter(
    "poc_langgraph_runs_total",
    "Total de execuções do LangGraph",
    ["status"],
)


# Tempo de execução de cada node
NODE_DURATION = Histogram(
    "poc_langgraph_node_duration_seconds",
    "Tempo de execução dos nodes do LangGraph",
    ["node"],
)


# Chamadas ao LLM
LLM_CALLS = Counter(
    "poc_llm_calls_total",
    "Total de chamadas ao LLM",
    ["node", "status"],
)


# Tokens
LLM_TOKENS = Counter(
    "poc_llm_tokens_total",
    "Total de tokens utilizados",
    ["direction"],
)


# Aplicação ASGI que o Prometheus acessará
metrics_app = make_asgi_app()