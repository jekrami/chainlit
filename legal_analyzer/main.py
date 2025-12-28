from orchestrator import run_deep_analysis
import json
import pdfplumber
def pdf_to_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

import arabic_reshaper
from bidi.algorithm import get_display

def normalize_rtl(text: str) -> str:
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

if __name__ == "__main__":
    contract_text = normalize_rtl(pdf_to_text("contract.pdf"))
    analysis = run_deep_analysis(contract_text)

    with open("analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    print("Deep legal analysis completed.")
