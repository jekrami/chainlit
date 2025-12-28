import chainlit as cl
import os
import json
from document_processor import process_document
from rag_pipeline import RagPipeline
from llm_handler import LlmHandler

# --- Global Variables & Constants ---
rag_pipeline = None
llm_handler = None
documents_metadata = {}
chat_history = []

# File paths for persistence
VECTOR_DB_PATH = "vector_db.pkl"
CHAT_HISTORY_PATH = "rag_chat_history.json"
DOCUMENTS_METADATA_PATH = "documents_metadata.json"

# --- Helper Functions ---
def save_chat_history():
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=4)

def save_metadata():
    with open(DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(documents_metadata, f, ensure_ascii=False, indent=4)

# --- Chainlit Event Handlers ---
@cl.on_chat_start
async def on_chat_start():
    global rag_pipeline, llm_handler, documents_metadata, chat_history

    # --- Initialization ---
    llm_handler = LlmHandler()
    rag_pipeline = RagPipeline()

    # Load existing data if available
    if os.path.exists(VECTOR_DB_PATH):
        rag_pipeline.load(VECTOR_DB_PATH)

    if os.path.exists(DOCUMENTS_METADATA_PATH):
        with open(DOCUMENTS_METADATA_PATH, "r", encoding="utf-8") as f:
            documents_metadata = json.load(f)

    if os.path.exists(CHAT_HISTORY_PATH):
        with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
            chat_history = json.load(f)

    # Set user session data
    cl.user_session.set("rag_pipeline", rag_pipeline)
    cl.user_session.set("llm_handler", llm_handler)

    # --- Welcome and File Upload ---
    await cl.Message(
        content="**سلام! من یک دستیار تحلیلگر قراردادهای حقوقی مبتنی بر قوانین ایران هستم.**\n\nلطفا یک فایل PDF قرارداد را برای شروع تحلیل آپلود کنید.",
        author="تحلیلگر قرارداد"
    ).send()

    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="لطفا فایل PDF قرارداد خود را اینجا آپلود کنید.",
            accept=["application/pdf"],
            max_size_mb=100,
            timeout=300,  # 5 minutes
            author="سیستم"
        ).send()

    if files:
        uploaded_file = files[0]
        msg = cl.Message(
            content=f"در حال پردازش فایل: `{uploaded_file.name}`... لطفاً چند لحظه صبر کنید.",
            author="سیستم"
        )
        await msg.send()

        # --- Document Processing ---
        try:
            # Save the file temporarily to pass its path
            temp_file_path = f"./{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.content)

            text_chunks = process_document(temp_file_path)

            if not text_chunks:
                await cl.Message(
                    content=f"خطا: نتوانستم هیچ متنی از فایل `{uploaded_file.name}` استخراج کنم. ممکن است فایل خالی یا محافظت‌شده باشد.",
                    author="سیستم"
                ).send()
                return

            # --- RAG Pipeline Indexing ---
            rag_pipeline.add_documents(text_chunks)
            rag_pipeline.save(VECTOR_DB_PATH)

            # Update and save metadata
            documents_metadata[uploaded_file.name] = {"path": temp_file_path, "processed": True}
            save_metadata()

            msg.content = f"✅ فایل `{uploaded_file.name}` با موفقیت پردازش و نمایه شد.\n\n**اکنون می‌توانید سوالات خود را در مورد این قرارداد بپرسید.**"
            await msg.update()

        except Exception as e:
            await cl.Message(
                content=f"یک خطای غیرمنتظره در هنگام پردازش فایل رخ داد: {e}",
                author="سیستم"
            ).send()
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

@cl.on_message
async def on_message(message: cl.Message):
    global chat_history
    rag_pipeline = cl.user_session.get("rag_pipeline")
    llm_handler = cl.user_session.get("llm_handler")

    if not rag_pipeline or not rag_pipeline.index:
        await cl.Message(
            content="خطا: پایگاه داده‌ای برای جستجو وجود ندارد. لطفاً ابتدا یک فایل PDF را با شروع یک چت جدید آپلود کنید.",
            author="سیستم"
        ).send()
        return

    # --- RAG Retrieval ---
    retrieved_context = rag_pipeline.retrieve(message.content)

    if not retrieved_context:
        await cl.Message(
            content="متاسفانه نتوانستم اطلاعات مرتبطی با سوال شما در سند پیدا کنم.",
            author="تحلیلگر قرارداد"
        ).send()
        return

    # --- Multi-Model Reasoning ---
    msg = cl.Message(content="", author="تحلیلگر قرارداد")
    await msg.stream_token("در حال تحلیل و ترکیب پاسخ‌ها... ")

    final_answer = await llm_handler.get_synthesized_answer(message.content, retrieved_context)

    # --- Final Answer and History ---
    await cl.Message(content=final_answer, author="تحلیلگر قرارداد").send()

    chat_history.append({"user": message.content, "assistant": final_answer})
    save_chat_history()
