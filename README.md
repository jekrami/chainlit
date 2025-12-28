# Multi-Model Persian Contract Analyzer

This project is a sophisticated legal analysis tool designed to interpret and answer questions about Iranian legal contracts. It leverages a multi-model Retrieval-Augmented Generation (RAG) pipeline, local Ollama models, and a user-friendly interface to provide precise, Persian-first legal analysis.

This repository offers two user interface options: **Chainlit** (a modern, chat-based UI) and **Gradio** (a flexible, component-based UI).

## Core Features

-   **Persian-First Legal Analysis:** Optimized for the nuances of Iranian contract law, civil law, and commercial agreements.
-   **Dual UI Options:** Choose between a sleek Chainlit interface or a functional Gradio interface.
-   **Multi-Model Reasoning:** Utilizes three distinct Ollama models in parallel (Analyst, Verifier, Synthesizer) to ensure high accuracy and resolve ambiguities.
-   **RAG Pipeline:** Employs a robust RAG system with `pymupdf` for text extraction, FAISS for vector storage, and a hybrid retrieval model with keyword boosting.
-   **Local & Private:** All processing is done locally, ensuring the privacy and security of sensitive legal documents. No data is sent to external cloud APIs.

## Architecture

The system follows a parallel multi-model architecture:

1.  **User Input:** The user uploads a PDF and asks a question in the UI.
2.  **RAG Retrieval:** The system retrieves the most relevant text chunks from the document using a combination of semantic search and keyword boosting.
3.  **Parallel Analysis:** The user's question and the retrieved context are sent to two different Ollama models simultaneously:
    *   **Primary Legal Analyst Model** (`partai/dorna-llama3`)
    *   **Secondary Verification Model** (`mshojaei77/gemma3persian`)
4.  **Synthesis:** The responses from the first two models are sent to a third **Synthesizer Model** (`llama3`), which resolves conflicts, preserves factual data, and generates a single, coherent, and legally conservative answer in formal Persian.
5.  **Final Answer:** The synthesized answer is streamed back to the user in the UI.

## Setup and Installation

### 1. Prerequisites

-   **Python 3.9+**
-   **Ollama:** You must have Ollama installed and running. Follow the instructions at [ollama.com](https://ollama.com/).

### 2. Install Ollama Models

You need to pull the required models. Open your terminal and run the following commands:

```bash
ollama pull partai/dorna-llama3
ollama pull mshojaei77/gemma3persian
ollama pull llama3
ollama pull paraphrase-multilingual-mpnet-base-v2
```

### 3. Install Python Dependencies

Clone the repository and install the required Python packages using `pip`:

```bash
git clone <repository-url>
cd <repository-directory>
pip install -r requirements.txt
```

## How to Run the Application

### 1. Start the Ollama Server

Before running the application, ensure the Ollama server is running in the background.

```bash
ollama serve
```

### 2. Choose Your Interface

You can run either the Chainlit or the Gradio version of the application.

#### To Run the Chainlit Version:

In a separate terminal, run the following command from the project's root directory:

```bash
chainlit run app.py
```
Then, open your web browser and navigate to `http://localhost:8000`.

#### To Run the Gradio Version:

In a separate terminal, run the following command from the project's root directory:

```bash
python app_gradio.py
```
Then, open your web browser and navigate to the local URL provided in the terminal (usually `http://127.0.0.1:7860`).

## Project Structure

| File                      | Purpose                                                                          |
| ------------------------- | -------------------------------------------------------------------------------- |
| `app.py`                  | The main entry point for the **Chainlit** application.                           |
| `app_gradio.py`           | The main entry point for the **Gradio** application.                             |
| `requirements.txt`        | A list of all Python dependencies required for the project.                      |
| `config.py`               | Stores all configuration variables, such as model names and RAG parameters.      |
| `document_processor.py`   | Handles PDF parsing, text extraction, RTL correction, and text chunking.           |
| `rag_pipeline.py`         | Manages the FAISS vector store, embeddings, and the hybrid retrieval logic.        |
| `llm_handler.py`          | Manages all interactions with the Ollama models, including parallel execution.   |
| `vector_db.pkl`           | **Generated:** Stores the FAISS index and document chunks.                       |
| `rag_chat_history.json`   | **Generated:** Stores the conversation history for a session.                    |
| `documents_metadata.json` | **Generated:** Stores metadata about uploaded documents.                         |
