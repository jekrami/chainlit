import chainlit as cl
import os
import json
import tempfile
from document_processor import process_document
from rag_pipeline import RagPipeline
from llm_handler import LlmHandler

# --- Global State for Shared Knowledge Base ---
rag_pipeline = RagPipeline()
documents_metadata = {}

# --- File Paths for Persistence ---
VECTOR_DB_PATH = "vector_db.pkl"
CHAT_HISTORY_PATH = "rag_chat_history.json"
DOCUMENTS_METADATA_PATH = "documents_metadata.json"

# --- Initialization ---
# Load the shared, persistent knowledge base at startup.
if os.path.exists(VECTOR_DB_PATH):
    rag_pipeline.load(VECTOR_DB_PATH)
if os.path.exists(DOCUMENTS_METADATA_PATH):
    with open(DOCUMENTS_METADATA_PATH, "r", encoding="utf-8") as f:
        documents_metadata = json.load(f)

# --- Helper Functions for Global Persistence ---
def append_to_global_chat_history(user_query, assistant_answer):
    """Appends a single turn to the global chat history file."""
    history_entry = {"user": user_query, "assistant": assistant_answer}

    # Read the existing history, append, and write back.
    # This is not the most efficient for very large files, but it is robust.
    full_history = []
    if os.path.exists(CHAT_HISTORY_PATH):
        with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
            full_history = json.load(f)

    full_history.append(history_entry)

    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(full_history, f, ensure_ascii=False, indent=4)

def save_metadata():
    with open(DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(documents_metadata, f, ensure_ascii=False, indent=4)

@cl.on_chat_start
async def on_chat_start():
    # Initialize session-specific components
    cl.user_session.set("llm_handler", LlmHandler())
    # The current conversation's history is kept in the session for privacy.
    cl.user_session.set("session_chat_history", [])

    await cl.Message(
        content="**سلام!** شما می‌توانید یک فایل PDF جدید آپلود کنید یا در مورد اسناد قبلاً تحلیل‌شده سوال بپرسید.",
        author="تحلیلگر قرارداد"
    ).send()

    files = await cl.AskFileMessage(
        content="در صورت تمایل، یک فایل PDF جدید برای تحلیل آپلود کنید.",
        accept=["application/pdf"],
        max_size_mb=100,
        timeout=300,
        author="سیستم"
    ).send()

    if files:
        uploaded_file = files[0]
        msg = cl.Message(content=f"در حال پردازش فایل: `{uploaded_file.name}`...", author="سیستم")
        await msg.send()

        try:
            text_chunks = process_document(uploaded_file.path)
            if not text_chunks:
                await msg.update(content=f"خطا در پردازش فایل `{uploaded_file.name}`.")
                return

            # Add to the global RAG pipeline with source tracking
            rag_pipeline.add_documents(text_chunks, source_name=uploaded_file.name)
            rag_pipeline.save(VECTOR_DB_PATH)

            # Update and save global metadata
            documents_metadata[uploaded_file.name] = {"processed": True}
            save_metadata()

            await msg.update(content=f"✅ فایل `{uploaded_file.name}` با موفقیت به پایگاه دانش اضافه شد.")

        except Exception as e:
            await msg.update(content=f"یک خطای غیرمنتظره رخ داد: {e}")

@cl.on_message
async def on_message(message: cl.Message):
    llm_handler = cl.user_session.get("llm_handler")
    session_chat_history = cl.user_session.get("session_chat_history")

    if not rag_pipeline.index:
        await cl.Message(content="هنوز هیچ سندی در پایگاه دانش وجود ندارد.", author="سیستم").send()
        return

    # Retrieve context with source tracking
    retrieved_context, sources = rag_pipeline.retrieve(message.content, return_sources=True)

    if not retrieved_context:
        await cl.Message(content="نتوانستم اطلاعات مرتبطی پیدا کنم.", author="تحلیلگر قرارداد").send()
        return

    msg = cl.Message(content="", author="تحلیلگر قرارداد")
    await msg.stream_token("در حال تحلیل... ")

    final_answer = await llm_handler.get_synthesized_answer(message.content, retrieved_context)

    # Add source information to the answer
    unique_sources = list(set(sources))
    source_info = "\n\n---\n📄 **منابع استفاده شده:**\n"
    for src in unique_sources:
        source_info += f"• {src}\n"

    final_answer_with_sources = final_answer + source_info

    await cl.Message(content=final_answer_with_sources).send()

    # Update the session-specific history for the current conversation view
    session_chat_history.append({"user": message.content, "assistant": final_answer_with_sources})
    cl.user_session.set("session_chat_history", session_chat_history)

    # Append to the global, persistent chat log
    append_to_global_chat_history(message.content, final_answer_with_sources)
