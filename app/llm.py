import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.getenv(
            "LM_STUDIO_BASE_URL",
            "http://172.21.240.1:1234/v1",
        ),
        api_key=os.getenv(
            "LM_STUDIO_API_KEY",
            "lm-studio",
        ),
        model=os.getenv(
            "LM_STUDIO_MODEL",
            "qwen2.5-coder-1.5b-instruct",
        ),
        temperature=0.2,
        # Limita o tamanho da resposta. Sem isso, o modelo gera centenas de
        # tokens e, rodando em CPU no LM Studio (~0.25s/token), o tempo total
        # ultrapassa o timeout. 512 tokens cabem folgadamente em 180s.
        max_tokens=int(os.getenv("LM_STUDIO_MAX_TOKENS", "512")),
        timeout=int(os.getenv("LM_STUDIO_TIMEOUT", "180")),
        max_retries=1,
    )


llm = create_llm()