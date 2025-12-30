import json
import requests
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:14b-instruct"  # Using same model as ollama_client for consistency

def load_analysis_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_presentation_prompt(analysis_json: dict) -> list:
    system_prompt = """
You are operating STRICTLY in presentation and translation mode.

You are NOT allowed to analyze, reason, summarize, evaluate, recommend, or improve anything.

The input JSON is FINAL and AUTHORITATIVE.

Your ONLY task is to present its contents in Persian (Farsi).

MANDATORY RULES:
- You MUST write ONLY in Persian (Farsi).
- You MUST NOT write any English words, sentences, headings, or labels.
- If a legal term has no exact Persian equivalent, you may keep the English term ONLY inside parentheses.
- You MUST NOT add, remove, or modify meaning.
- You MUST NOT perform legal analysis.
- You MUST NOT use analytical labels such as “PASS”, “analysis”, “recommendation”, or similar.
- You MUST NOT address the reader directly.
- You MUST NOT give advice.

STYLE REQUIREMENTS:
- Formal Iranian legal writing
- RTL
- Neutral, descriptive tone
- Declarative statements only

STRUCTURE:
Present the content under clear Persian legal headings such as:
- مشخصات کلی سند
- طرفین قرارداد
- موضوع قرارداد
- تعهدات طرفین
- شرایط مالی
- مدت قرارداد
- شرایط فسخ و خاتمه
- مسئولیت‌ها
- نکات و ابهامات (فقط اگر در JSON ذکر شده)

If the JSON states uncertainty or missing information, explicitly state:
«در متن قرارداد تصریح نشده است.»
"""

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "Here is the authoritative legal analysis JSON:\n\n"
                       + json.dumps(analysis_json, ensure_ascii=False, indent=2)
        }
    ]

def call_ollama(messages: list) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()

    data = response.json()
    return data["message"]["content"]

def generate_persian_presentation(
    analysis_json_path: str,
    output_path: str = "presentation_fa.txt"
):
    analysis_json = load_analysis_json(analysis_json_path)
    messages = build_presentation_prompt(analysis_json)

    persian_text = call_ollama(messages)

    Path(output_path).write_text(persian_text, encoding="utf-8")
    return persian_text

if __name__ == "__main__":
    result = generate_persian_presentation(
        analysis_json_path="analysis_result.json",
        output_path="presentation_fa.txt"
    )
    print("Presentation-layer translation completed.")
