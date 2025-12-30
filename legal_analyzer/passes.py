ANALYSIS_PASSES = [

    # PASS 1
    {
        "id": 1,
        "title": "PASS 1 — Formal & Structural Grounding",
        "objective": """
Extract ONLY formal and structural data from the contract.
""",
        "allowed": [
            "Identify apparent contract type (بیع، اجاره، پیمانکاری، خدماتی، نامعین)",
            "Extract parties, roles, titles",
            "Extract dates, clause numbering, headings"
        ],
        "forbidden": [
            "Any legal interpretation",
            "Risk analysis",
            "Validity or enforceability judgment"
        ],
        "quote_policy": "Verbatim quotation mandatory",
        "silence_policy": "If an item is missing, write exactly: «ذکر نشده است»",
        "output_format": """
- نوع قرارداد:
- طرفین و عناوین:
- تاریخ‌ها:
- ساختار و شماره‌بندی:
"""
    },

    # PASS 2
    {
        "id": 2,
        "title": "PASS 2 — Subject Matter & Obligation Classification",
        "objective": """
Identify the subject of contract and classify obligations.
""",
        "allowed": [
            "Extract موضوع قرارداد",
            "List تعهدات each party",
            "Classify obligations as تعهد به نتیجه / تعهد به وسیله"
        ],
        "forbidden": [
            "Penalty analysis",
            "Risk or breach discussion"
        ],
        "quote_policy": "Verbatim for obligations",
        "silence_policy": "If unclear, write: «ابهام دارد»",
        "output_format": """
- موضوع قرارداد:
- تعهدات طرف اول:
- تعهدات طرف دوم:
- طبقه‌بندی تعهدات:
"""
    },

    # PASS 3
    {
        "id": 3,
        "title": "PASS 3 — Duration & Financial Terms",
        "objective": """
Map temporal and financial elements of the contract.
""",
        "allowed": [
            "Extract مدت قرارداد",
            "Extract مبلغ، نحوه پرداخت، عوضین"
        ],
        "forbidden": [
            "Assuming hidden payments",
            "Penalty calculation"
        ],
        "quote_policy": "Exact clauses only",
        "silence_policy": "If missing, state: «مقرره‌ای ندارد»",
        "output_format": """
- مدت قرارداد:
- مبلغ / عوض قرارداد:
- نحوه پرداخت:
"""
    },

    # PASS 4
    {
        "id": 4,
        "title": "PASS 4 — Termination, Breach & Remedies",
        "objective": """
Identify clauses relating to فسخ، انفساخ، اقاله، وجه التزام، خسارت.
""",
        "allowed": [
            "Quote فسخ clauses",
            "Quote ضمانت اجرا clauses"
        ],
        "forbidden": [
            "Explaining legal effect",
            "Predicting court outcome"
        ],
        "quote_policy": "Strict verbatim quotation",
        "silence_policy": "If absent, write: «شرطی در این خصوص یافت نشد»",
        "output_format": """
- فسخ:
- انفساخ:
- اقاله:
- ضمانت اجرا / وجه التزام:
"""
    },

    # PASS 5
    {
        "id": 5,
        "title": "PASS 5 — Risk, Ambiguity & Legal Silence",
        "objective": """
Detect ambiguity, vague language, and contractual silence.
""",
        "allowed": [
            "Highlight vague terms",
            "Point out missing clauses"
        ],
        "forbidden": [
            "Legal default explanation",
            "Risk scoring"
        ],
        "quote_policy": "Quote risky phrases",
        "silence_policy": "Use: «سکوت قراردادی»",
        "output_format": """
- عبارات مبهم:
- سکوت‌های مهم:
- ریسک‌های نگارشی:
"""
    },

    # PASS 6
    {
        "id": 6,
        "title": "PASS 6 — Iranian Legal Defaults",
        "objective": """
State default Iranian legal rules for identified silences.
""",
        "allowed": [
            "Refer to قانون مدنی ایران",
            "Cite article numbers when applicable"
        ],
        "forbidden": [
            "Assuming parties' intent"
        ],
        "quote_policy": "Legal terms must remain Persian",
        "silence_policy": "If no default exists, state: «حکم صریح قانونی وجود ندارد»",
        "output_format": """
- قواعد تکمیلی قانون مدنی:
- مواد قابل اعمال:
"""
    },

    # PASS 7
    {
        "id": 7,
        "title": "PASS 7 — Conceptual Legal Model",
        "objective": """
Build a conceptual legal model of power and risk allocation.
""",
        "allowed": [
            "Compare rights vs obligations",
            "Describe balance or imbalance"
        ],
        "forbidden": [
            "Final judgment",
            "Practical legal advice"
        ],
        "quote_policy": "Paraphrase allowed",
        "silence_policy": "If neutral, write: «تعادل نسبی دارد»",
        "output_format": """
- توازن حقوق و تعهدات:
- تخصیص ریسک:
"""
    },

    # PASS 8
    {
        "id": 8,
        "title": "PASS 8 — Final Enforceability Assessment",
        "objective": """
Assess integrity, enforceability, and critical fixes.
""",
        "allowed": [
            "Overall assessment",
            "Risk level (Low / Medium / High)",
            "List critical missing clauses"
        ],
        "forbidden": [
            "Replacing judicial decision",
            "Drafting full replacement contract"
        ],
        "quote_policy": "Summary allowed",
        "silence_policy": "N/A",
        "output_format": """
- ارزیابی کلی:
- سطح ریسک:
- اصلاحات حیاتی:
"""
    },
]
