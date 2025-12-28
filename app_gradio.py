import gradio as gr
import os
import json
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

# Initialize the LLM handler once
llm_handler = LlmHandler()

# --- Helper Functions for Global Persistence ---
def append_to_global_chat_history(user_query, assistant_answer):
    """Appends a single turn to the global chat history file."""
    history_entry = {"user": user_query, "assistant": assistant_answer}

    full_history = []
    if os.path.exists(CHAT_HISTORY_PATH):
        with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
            try:
                full_history = json.load(f)
            except json.JSONDecodeError:
                pass # Handle case where file is empty or corrupt

    full_history.append(history_entry)

    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(full_history, f, ensure_ascii=False, indent=4)

def save_metadata():
    with open(DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(documents_metadata, f, ensure_ascii=False, indent=4)

# --- Gradio UI Functions ---

def process_uploaded_file(file):
    """Handles the file upload and processing."""
    if file is None:
        return "لطفاً یک فایل را برای پردازش آپلود کنید."

    try:
        text_chunks = process_document(file.name)
        if not text_chunks:
            return "خطا: نتوانستم هیچ متنی از فایل استخراج کنم."

        # Add to the global RAG pipeline and save to disk
        rag_pipeline.add_documents(text_chunks)
        rag_pipeline.save(VECTOR_DB_PATH)

        # Update and save global metadata
        documents_metadata[os.path.basename(file.name)] = {"processed": True}
        save_metadata()

        return f"✅ فایل `{os.path.basename(file.name)}` با موفقیت به پایگاه دانش اضافه شد."
    except Exception as e:
        return f"یک خطای غیرمنتظره رخ داد: {e}"

async def chat_interface_fn(message, history):
    """Handles the chat interaction for the Gradio ChatInterface."""
    if not rag_pipeline.index:
        yield "هنوز هیچ سندی در پایگاه دانش وجود ندارد. لطفاً ابتدا یک فایل را آپلود کنید."
        return

    # Let the user know the system is working.
    yield "در حال جستجو و تحلیل..."

    retrieved_context = rag_pipeline.retrieve(message)

    if not retrieved_context:
        yield "نتوانستم اطلاعات مرتبطی در اسناد موجود پیدا کنم."
        return

    # Generate the answer
    final_answer = await llm_handler.get_synthesized_answer(message, retrieved_context)

    # Append to the global, persistent chat log
    append_to_global_chat_history(message, final_answer)

    # Yield the final answer to the user
    yield final_answer

# --- Gradio Interface Definition ---

with gr.Blocks() as demo:
    gr.Markdown(
        """
        # ⚖️ تحلیلگر قراردادهای حقوقی ایران
        این ابزار به شما کمک می‌کند تا اسناد حقوقی خود را با استفاده از هوش مصنوعی تحلیل کرده و به سوالات خود پاسخ دهید.
        لطفاً ابتدا یک فایل PDF را آپلود کنید و پس از مشاهده پیام موفقیت، سوالات خود را در کادر چت بپرسید.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            file_uploader = gr.File(label="۱. آپلود فایل PDF قرارداد", file_types=[".pdf"])
            upload_status = gr.Textbox(label="۲. وضعیت پردازش فایل", interactive=False, rtl=True)
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="چت با سند", height=500, rtl=True)
            msg = gr.Textbox(label="۳. سوال خود را بپرسید", placeholder="سوال خود را در مورد قرارداد اینجا تایپ کنید...", rtl=True)
            clear = gr.Button("پاک کردن گفتگو")

    # Wire up the components
    file_uploader.upload(fn=process_uploaded_file, inputs=file_uploader, outputs=upload_status)

    # The chat submission logic
    msg.submit(chat_interface_fn, [msg, chatbot], [chatbot])

    # The clear button logic
    clear.click(lambda: None, None, chatbot, queue=False)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css="footer {display: none !important}")
