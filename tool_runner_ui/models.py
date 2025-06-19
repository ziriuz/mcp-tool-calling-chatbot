import os
from enum import Enum

import httpx
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


class Models(Enum):
    R1 = "deepseek-r1:1.5b"
    LLAMA_1B = "llama3.2:1b"
    LLAMA_3B = "llama3.2:3b"
    GEMMA = "gemma:2b"
    GEMMA3 = "gemma3:4b"
    GPT_4O_MINI = "gpt-4o-mini"
    QWEN25_CODER_7B = "qwen2.5-coder:7b"
    QWEN3_8B = "qwen3:8b"
    MISTRAL_NEMO = "mistral-nemo:latest"
    MISTRAL = "mistral"

    @staticmethod
    def create_chat(model: Enum, base_url: str = "http://localhost:11434", temperature: float = 0.05):
        if model == Models.GPT_4O_MINI:
            return ChatOpenAI(model=model.value, temperature=temperature, http_client=httpx.Client(verify=False))
        else:
            return ChatOllama(model=model.value, temperature=temperature,
                              base_url=base_url,
                              http_client=httpx.Client(verify=False),
                              timeout=httpx.Timeout(timeout=300.0)
                              )


if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "proj_www"
    print(Models("gpt-4o-mini"))
    chat = Models.create_chat(Models.GPT_4O_MINI)
    print(chat.model_name)
