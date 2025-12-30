from orchestrator import run_deep_analysis
from presentation import generate_persian_presentation

import json
import pdfplumber
import arabic_reshaper
from bidi.algorithm import get_display


def pdf_to_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()
def normalize_rtl(text: str) -> str:
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)


if __name__ == "__main__":

    # 1. PDF → Text → RTL normalization
    contract_text = normalize_rtl(pdf_to_text("contract.pdf"))

    # 2. Deep legal analysis (English, structured)
    analysis = run_deep_analysis(contract_text)

    # 3. Save canonical analysis (DO NOT TRANSLATE)
    with open("analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    print("Deep legal analysis completed.")

    # 4. Presentation-layer translation (optional UI feature)
    persian_presentation = generate_persian_presentation(
        analysis_json_path="analysis_result.json",
        output_path="presentation_fa.txt"
    )

    print("Persian legal presentation generated.")
