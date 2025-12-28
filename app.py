import chainlit as cl
import os
import json
import tempfile
from document_processor import process_document
from rag_pipeline import RagPipeline
from llm_handler import LlmHandler

# --- Global State ---
# These objects are shared across all user sessions.
rag_pipeline = RagPipeline()
documents_metadata = {}
chat_history = []

# --- File Paths for Persistence ---
VECTOR_DB_PATH = "vector_db.pkl"
CHAT_HISTORY_PATH = "rag_chat_history.json"
DOCUMENTS_METADATA_PATH = "documents_metadata.json"

# --- Initialization ---
# Load persistent data when the application starts.
if os.path.exists(VECTOR_DB_PATH):
    rag_pipeline.load(VECTOR_DB_PATH)
if os.path.exists(DOCUMENTS_METADATA_PATH):
    with open(DOCUMENTS_METADATA_PATH, "r", encoding="utf-8") as f:
        documents_metadata = json.load(f)
if os.path.exists(CHAT_HISTORY_PATH):
    with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
        chat_history = json.load(f)

# --- Helper Functions ---
def save_chat_history():
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=4)

def save_metadata():
    with open(DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(documents_metadata, f, ensure_ascii=False, indent=4)

@cl.on_chat_start
async def on_chat_start():
    # Initialize a session-specific LLM handler
    cl.user_session.set("llm_handler", LlmHandler())

    await cl.Message(
        content="**سلام! من یک دستیار تحلیلگر قراردادهای حقوقی مبتنی بر قوانین ایران هستم.**\n\nشما می‌توانید یک فایل PDF جدید آپلود کنید یا در مورد اسناد قبلاً تحلیل‌شده سوال بپرسید.",
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
        msg = cl.Message(
            content=f"در حال پردازش فایل: `{uploaded_file.name}`...",
            author="سیستم"
        )
        await msg.send()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.content)
            temp_file_path = temp_file.name

        try:
            text_chunks = process_document(temp_file_path)
            if not text_chunks:
                await msg.update(content=f"خطا در پردازش فایل `{uploaded_file.name}`.")
                return

            # Add to the global RAG pipeline and save
            rag_pipeline.add_documents(text_chunks)
            rag_pipeline.save(VECTOR_DB_PATH)

            # Update and save global metadata
            documents_metadata[uploaded_file.name] = {"path": "persistent", "processed": True}
            save_metadata()

            await msg.update(content=f"✅ فایل `{uploaded_file.name}` با موفقیت پردازش شد.")

        finally:
            os.remove(temp_file_path)

@cl.on_message
async def on_message(message: cl.Message):
    llm_handler = cl.user_session.get("llm_handler")

    if not rag_pipeline.index:
        await cl.Message(content="هنوز هیچ سندی پردازش نشده است.", author="سیستم").send()
        return

    retrieved_context = rag_pipeline.retrieve(message.content)

    if not retrieved_context:
        await cl.Message(content="نتوانستم اطلاعات مرتبطی پیدا کنم.", author="تحلیلگر قرارداد").send()
        return

    msg = cl.Message(content="", author="تحلیلگر قرارداد")
    await msg.stream_token("در حال تحلیل... ")

    final_answer = await llm_handler.get_synthesized_answer(message.content, retrieved_context)
    await cl.Message(content=final_answer).send()

    # Append to the global chat history and save
    chat_history.append({"user": message.content, "assistant": final_answer})
    save_chat_history()
