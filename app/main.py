from time import perf_counter

from fastapi import FastAPI
from prometheus_client import make_asgi_app
from pydantic import BaseModel

from app.graph import run_assistant
from app.metrics import (
    HTTP_REQUESTS,
    HTTP_REQUEST_DURATION,
    metrics_app,
)


app = FastAPI(
    title="LangChain + LangGraph Observability POC",
    version="0.1.0",
)


app.mount(
    "/metrics",
    metrics_app,
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    intent: str
    answer: str


@app.middleware("http")
async def metrics_middleware(request, call_next):

    start = perf_counter()

    response = await call_next(request)

    duration = perf_counter() - start

    if request.url.path != "/metrics":

        HTTP_REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(response.status_code),
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

    return response


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.post(
    "/ask",
    response_model=AskResponse,
)
def ask(request: AskRequest):

    result = run_assistant(
        request.question
    )

    return AskResponse(
        question=result["question"],
        intent=result["intent"],
        answer=result["answer"],
    )