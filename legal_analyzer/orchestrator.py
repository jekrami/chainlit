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
        # Build the analysis instructions from the new structure
        allowed_actions = "\n".join([f"  • {item}" for item in p['allowed']])
        forbidden_actions = "\n".join([f"  • {item}" for item in p['forbidden']])
        
        user_prompt = f"""
Original contract text (Persian, RTL):

----------------
{contract_text}
----------------

Current analysis focus:
{p['title']}

Objective:
{p['objective']}

You are ALLOWED to:
{allowed_actions}

You are FORBIDDEN from:
{forbidden_actions}

Quote Policy: {p['quote_policy']}
Silence Policy: {p['silence_policy']}

Required Output Format:
{p['output_format']}

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
