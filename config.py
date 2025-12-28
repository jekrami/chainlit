# Ollama models
PRIMARY_LEGAL_ANALYST_MODEL = "partai/dorna-llama3"
SECONDARY_VERIFICATION_MODEL = "mshojaei77/gemma3persian"
SYNTHESIZER_MODEL = "llama3"
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"

# Ollama API endpoint
OLLAMA_API_ENDPOINT = "http://localhost:11434/api/generate"

# RAG configuration
CHUNK_SIZE = 350
CHUNK_OVERLAP = 100
TOP_K = 10

# Keyword boosting
KEYWORD_BOOST_CONFIG = {
    "مبلغ": 1.5,
    "تاریخ": 1.5,
    "ماده": 1.2,
    "تبصره": 1.2,
    "فسخ": 1.5,
    "جریمه": 1.5,
    "تعهد": 1.3,
}

# LLM parameters
LLM_TEMPERATURE = 0.1
LLM_TOP_P = 0.8
