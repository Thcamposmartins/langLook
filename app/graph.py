from time import perf_counter
from typing import Literal, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.llm import llm
from app.metrics import (
    GRAPH_RUNS,
    LLM_CALLS,
    LLM_TOKENS,
    NODE_DURATION,
)


class AssistantState(TypedDict, total=False):
    question: str
    intent: str
    answer: str


def classify_question(state: AssistantState):
    question = state["question"].lower()

    technical_terms = [
        "java",
        "python",
        "api",
        "docker",
        "kubernetes",
        "database",
        "sql",
        "programação",
        "código",
        "langchain",
        "langgraph",
    ]

    intent = "technical"

    if not any(term in question for term in technical_terms):
        intent = "general"

    return {
        "intent": intent
    }


def call_llm(
    node_name: str,
    system_prompt: str,
    question: str,
):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "question": question
            }
        )

        LLM_CALLS.labels(
            node=node_name,
            status="success",
        ).inc()

        usage = response.usage_metadata or {}

        input_tokens = usage.get(
            "input_tokens",
            0,
        )

        output_tokens = usage.get(
            "output_tokens",
            0,
        )

        if input_tokens:
            LLM_TOKENS.labels(
                direction="input",
            ).inc(input_tokens)

        if output_tokens:
            LLM_TOKENS.labels(
                direction="output",
            ).inc(output_tokens)

        return response.content

    except Exception:
        LLM_CALLS.labels(
            node=node_name,
            status="error",
        ).inc()

        raise


def answer_technical(state: AssistantState):

    answer = call_llm(
        node_name="technical",
        system_prompt="""
        Você é um assistente especializado
        em engenharia de software.

        Responda em português.
        Seja técnico e objetivo.
        Use exemplos quando forem úteis.
        """,
        question=state["question"],
    )

    return {
        "answer": answer
    }


def answer_general(state: AssistantState):

    answer = call_llm(
        node_name="general",
        system_prompt="""
        Você é um assistente geral.

        Responda em português de forma clara,
        objetiva e concisa.
        """,
        question=state["question"],
    )

    return {
        "answer": answer
    }


def route_question(
    state: AssistantState,
) -> Literal["technical", "general"]:

    if state["intent"] == "technical":
        return "technical"

    return "general"


def timed_node(name, function):

    def wrapper(state):

        start = perf_counter()

        try:
            return function(state)

        finally:
            duration = perf_counter() - start

            NODE_DURATION.labels(
                node=name
            ).observe(duration)

    return wrapper


builder = StateGraph(AssistantState)


builder.add_node(
    "classify",
    timed_node(
        "classify",
        classify_question,
    ),
)

builder.add_node(
    "technical",
    timed_node(
        "technical",
        answer_technical,
    ),
)

builder.add_node(
    "general",
    timed_node(
        "general",
        answer_general,
    ),
)


builder.add_edge(
    START,
    "classify",
)


builder.add_conditional_edges(
    "classify",
    route_question,
    {
        "technical": "technical",
        "general": "general",
    },
)


builder.add_edge(
    "technical",
    END,
)

builder.add_edge(
    "general",
    END,
)


graph = builder.compile()


def run_assistant(question: str):

    try:

        result = graph.invoke(
            {
                "question": question
            }
        )

        GRAPH_RUNS.labels(
            status="success"
        ).inc()

        return result

    except Exception:

        GRAPH_RUNS.labels(
            status="error"
        ).inc()

        raise