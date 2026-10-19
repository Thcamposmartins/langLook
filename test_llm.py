from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://172.21.240.1:1234/v1",
    api_key="lm-studio",
    model="qwen2.5-coder-1.5b-instruct",
    temperature=0.2,
    max_retries=1,
    timeout=120,
)

messages = [
    ("system", "You answer only in rhymes."),
    ("human", "What is your favorite color?"),
]

try:
    response = llm.invoke(messages)

    print("Resposta do modelo:")
    print(response.content)

    print("\nMetadados de uso:")
    print(response.usage_metadata)

except Exception as exc:
    print(f"Erro ao chamar o LM Studio: {exc}")
    raise
