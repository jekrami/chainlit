from ollama_client import ollama_chat
from prompts import MASTER_SYSTEM_PROMPT
from passes import ANALYSIS_PASSES

def run_deep_analysis(contract_text: str) -> dict:
    """
    Runs all legal analysis passes sequentially.
    """

    results = {}
    accumulated_context = ""

    for p in ANALYSIS_PASSES:
        user_prompt = f"""
Original contract text (Persian, RTL):

----------------
{contract_text}
----------------

Current analysis focus:
{p['title']}
{p['focus']}

Previous findings (for context only, may be challenged):
{accumulated_context}
"""

        print(f"Running {p['title']} ...")

        output = ollama_chat(
            system_prompt=MASTER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        results[p["id"]] = {
            "title": p["title"],
            "output": output.strip(),
        }

        # Accumulate cautiously (context, not truth)
        accumulated_context += f"\n\n{p['title']}:\n{output.strip()}"

    return results
