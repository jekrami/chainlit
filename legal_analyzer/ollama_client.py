import requests
import json
from typing import Dict

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:14b-instruct"

def ollama_chat(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    top_p: float = 0.9,
) -> str:
    """
    Single, controlled call to Ollama.
    GPU usage is handled internally by Ollama.
    """

    payload: Dict = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": temperature,
            "top_p": top_p,
        },
        "stream": False,
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=600)
    response.raise_for_status()

    data = response.json()
    return data["message"]["content"]
