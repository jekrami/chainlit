import gradio as gr
import os
import json
import sys
from datetime import datetime
from document_processor import process_document
from rag_pipeline import RagPipeline
from llm_handler import LlmHandler

# Import deep analysis modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'legal_analyzer'))
from legal_analyzer.orchestrator import run_deep_analysis
from legal_analyzer.passes import ANALYSIS_PASSES
import pdfplumber
import arabic_reshaper
from bidi.algorithm import get_display

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

# --- Deep Legal Analysis Functions ---

def pdf_to_text(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def normalize_rtl(text: str) -> str:
    """Normalize RTL text for proper display."""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

# Persian translations for analysis passes
PASS_TITLES_FA = {
    1: "مرحله ۱ — تحلیل ساختاری و شکلی",
    2: "مرحله ۲ — طبقه‌بندی موضوع و تعهدات",
    3: "مرحله ۳ — مدت زمان و شرایط مالی",
    4: "مرحله ۴ — فسخ، نقض و جبران خسارت",
    5: "مرحله ۵ — ریسک، ابهام و خلأ قانونی",
    6: "مرحله ۶ — پیش‌فرض‌های قانونی ایران",
    7: "مرحله ۷ — مدل مفهومی حقوقی",
    8: "مرحله ۸ — ارزیابی نهایی قابلیت اجرا"
}

def run_deep_analysis_with_progress(pdf_file):
    """Run deep legal analysis with progress updates."""
    if pdf_file is None:
        yield None, "❌ لطفاً یک فایل PDF را آپلود کنید.", ""
        return

    try:
        # Extract text from PDF
        yield None, "📄 در حال استخراج متن از PDF...", ""
        contract_text = normalize_rtl(pdf_to_text(pdf_file.name))

        if not contract_text.strip():
            yield None, "❌ خطا: نتوانستم متنی از PDF استخراج کنم.", ""
            return

        # Initialize results
        results = {}
        accumulated_context = ""
        progress_html = ""

        # Run each analysis pass
        for i, p in enumerate(ANALYSIS_PASSES, 1):
            # Update progress
            progress_html = create_progress_html(i, len(ANALYSIS_PASSES), PASS_TITLES_FA[i])
            status_msg = f"🔍 در حال اجرای {PASS_TITLES_FA[i]}..."
            yield progress_html, status_msg, ""

            # Prepare prompt
            from legal_analyzer.prompts import MASTER_SYSTEM_PROMPT
            from legal_analyzer.ollama_client import ollama_chat

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

            # Run analysis
            output = ollama_chat(
                system_prompt=MASTER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            results[p["id"]] = {
                "title": p["title"],
                "title_fa": PASS_TITLES_FA[i],
                "output": output.strip(),
            }

            # Accumulate context
            accumulated_context += f"\n\n{p['title']}:\n{output.strip()}"

        # Generate final report
        progress_html = create_progress_html(8, 8, "✅ تحلیل کامل شد!")
        final_report = format_analysis_results(results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"deep_analysis_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        yield progress_html, f"✅ تحلیل عمیق با موفقیت کامل شد!\n📁 نتایج در فایل {output_file} ذخیره شد.", final_report

    except Exception as e:
        yield None, f"❌ خطا در تحلیل: {str(e)}", ""

def create_progress_html(current_step, total_steps, current_title):
    """Create HTML progress visualization."""
    progress_percent = (current_step / total_steps) * 100

    html = f"""
    <div style="direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <h3 style="color: #1976d2;">📊 پیشرفت تحلیل عمیق حقوقی</h3>
        <div style="background: #f5f5f5; border-radius: 10px; padding: 20px; margin: 10px 0;">
            <div style="margin-bottom: 10px;">
                <strong>مرحله {current_step} از {total_steps}</strong>
            </div>
            <div style="background: #e0e0e0; border-radius: 5px; height: 30px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #4caf50, #8bc34a); height: 100%; width: {progress_percent}%; transition: width 0.3s;"></div>
            </div>
            <div style="margin-top: 10px; color: #555;">
                {current_title}
            </div>
        </div>
        <div style="margin-top: 20px;">
    """

    # Add all steps with status
    for i in range(1, total_steps + 1):
        if i < current_step:
            status = "✅"
            color = "#4caf50"
        elif i == current_step:
            status = "🔄"
            color = "#ff9800"
        else:
            status = "⏳"
            color = "#9e9e9e"

        html += f"""
            <div style="padding: 8px; margin: 5px 0; background: {'#e8f5e9' if i < current_step else '#fff'}; border-right: 4px solid {color}; border-radius: 4px;">
                <span style="font-size: 18px;">{status}</span>
                <strong>{PASS_TITLES_FA.get(i, f'مرحله {i}')}</strong>
            </div>
        """

    html += """
        </div>
    </div>
    """

    return html

def format_analysis_results(results):
    """Format analysis results for display."""
    output = "# 📋 گزارش تحلیل عمیق حقوقی\n\n"
    output += f"**تاریخ تحلیل:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    output += "---\n\n"

    for pass_id in sorted(results.keys()):
        result = results[pass_id]
        output += f"## {result['title_fa']}\n\n"
        output += f"**{result['title']}**\n\n"
        output += f"{result['output']}\n\n"
        output += "---\n\n"

    return output

# --- Gradio UI Functions ---

def get_documents_list():
    """Get formatted list of loaded documents."""
    stats = rag_pipeline.get_document_stats()
    if not stats:
        return "هیچ سندی بارگذاری نشده است."

    doc_list = "📚 **اسناد بارگذاری شده:**\n\n"
    for i, (doc_name, chunk_count) in enumerate(stats.items(), 1):
        doc_list += f"{i}. **{doc_name}** ({chunk_count} بخش)\n"

    return doc_list

def delete_document(doc_name):
    """Delete a specific document from the knowledge base."""
    if not doc_name or doc_name.strip() == "":
        return "لطفاً نام سند را وارد کنید.", get_documents_list()

    success = rag_pipeline.delete_document(doc_name.strip())

    if success:
        # Update metadata
        if doc_name.strip() in documents_metadata:
            del documents_metadata[doc_name.strip()]
        save_metadata()

        # Save updated pipeline
        rag_pipeline.save(VECTOR_DB_PATH)

        return f"✅ سند `{doc_name.strip()}` با موفقیت حذف شد.", get_documents_list()
    else:
        return f"❌ سند `{doc_name.strip()}` یافت نشد.", get_documents_list()

def clear_all_documents_confirmed():
    """Clear all documents from the knowledge base (after confirmation)."""
    rag_pipeline.documents = []
    rag_pipeline.document_sources = []
    rag_pipeline.index = None

    # Clear metadata
    documents_metadata.clear()

    # Remove saved files
    if os.path.exists(VECTOR_DB_PATH):
        os.remove(VECTOR_DB_PATH)
    if os.path.exists(DOCUMENTS_METADATA_PATH):
        os.remove(DOCUMENTS_METADATA_PATH)

    return "✅ همه اسناد با موفقیت حذف شدند.", get_documents_list(), gr.update(visible=False)

def process_uploaded_file(file):
    """Handles the file upload and processing."""
    if file is None:
        return "لطفاً یک فایل را برای پردازش آپلود کنید.", get_documents_list()

    try:
        text_chunks = process_document(file.name)
        if not text_chunks:
            return "خطا: نتوانستم هیچ متنی از فایل استخراج کنم.", get_documents_list()

        # Add to the global RAG pipeline with source tracking
        source_name = os.path.basename(file.name)
        rag_pipeline.add_documents(text_chunks, source_name=source_name)
        rag_pipeline.save(VECTOR_DB_PATH)

        # Update and save global metadata
        from datetime import datetime
        documents_metadata[source_name] = {
            "processed": True,
            "chunks": len(text_chunks),
            "timestamp": datetime.now().isoformat()
        }
        save_metadata()

        return f"✅ فایل `{source_name}` با موفقیت به پایگاه دانش اضافه شد.\n📄 تعداد بخش‌ها: {len(text_chunks)}", get_documents_list()
    except Exception as e:
        return f"یک خطای غیرمنتظره رخ داد: {e}", get_documents_list()

async def chat_interface_fn(message, history):
    """Handles the chat interaction for the Gradio ChatInterface."""
    # Initialize history if None
    if history is None:
        history = []

    if not rag_pipeline.index:
        # Append user message and error response to history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "هنوز هیچ سندی در پایگاه دانش وجود ندارد. لطفاً ابتدا یک فایل را آپلود کنید."})
        yield history
        return

    # Add user message to history
    history.append({"role": "user", "content": message})

    # Let the user know the system is working.
    history.append({"role": "assistant", "content": "در حال جستجو و تحلیل..."})
    yield history

    # Retrieve context with source tracking
    retrieved_context, sources = rag_pipeline.retrieve(message, return_sources=True)

    if not retrieved_context:
        # Update the last assistant message with the error
        history[-1] = {"role": "assistant", "content": "نتوانستم اطلاعات مرتبطی در اسناد موجود پیدا کنم."}
        yield history
        return

    # Generate the answer
    final_answer = await llm_handler.get_synthesized_answer(message, retrieved_context)

    # Add source information to the answer
    unique_sources = list(set(sources))
    source_info = "\n\n---\n📄 **منابع استفاده شده:**\n"
    for src in unique_sources:
        source_info += f"• {src}\n"

    final_answer_with_sources = final_answer + source_info

    # Update the last assistant message with the final answer
    history[-1] = {"role": "assistant", "content": final_answer_with_sources}

    # Append to the global, persistent chat log
    append_to_global_chat_history(message, final_answer_with_sources)

    # Yield the final answer to the user
    yield history

# --- Gradio Interface Definition ---

# Custom CSS for RTL alignment
custom_css = """
footer {display: none !important}
.rtl-title {
    direction: rtl;
    text-align: right;
}
.rtl-title h1, .rtl-title h2, .rtl-title h3, .rtl-title h4 {
    text-align: right !important;
    direction: rtl !important;
}
"""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown(
        """
        <div class="rtl-title">

        # ⚖️ تحلیلگر قراردادهای حقوقی ایران

        این ابزار به شما کمک می‌کند تا اسناد حقوقی خود را با استفاده از هوش مصنوعی تحلیل کرده و به سوالات خود پاسخ دهید.

        </div>
        """
    )

    # Create tabs for different features
    with gr.Tabs():
        # Tab 1: RAG Chat Interface
        with gr.Tab("💬 چت با اسناد"):
            with gr.Row():
                # Left column - Document Management
                with gr.Column(scale=1):
                    gr.Markdown('<div class="rtl-title"><h3>📁 مدیریت اسناد</h3></div>')

                    # Upload section
                    with gr.Group():
                        file_uploader = gr.File(label="آپلود فایل PDF جدید", file_types=[".pdf"])
                        upload_status = gr.Textbox(label="وضعیت پردازش", interactive=False, rtl=True, lines=3)

                    # Documents list
                    with gr.Group():
                        documents_display = gr.Markdown(value=get_documents_list(), rtl=True)
                        refresh_docs_btn = gr.Button("🔄 بروزرسانی لیست", size="sm")

                    # Delete section
                    with gr.Group():
                        gr.Markdown('<div class="rtl-title"><h4>حذف سند</h4></div>')
                        doc_name_input = gr.Textbox(
                            label="نام سند برای حذف",
                            placeholder="نام دقیق فایل را وارد کنید...",
                            rtl=True
                        )
                        with gr.Row():
                            delete_btn = gr.Button("🗑️ حذف سند", variant="stop", size="sm")
                            clear_all_btn = gr.Button("⚠️ حذف همه", variant="stop", size="sm")
                        delete_status = gr.Textbox(label="وضعیت حذف", interactive=False, rtl=True, lines=2)

                    # Confirmation dialog for clearing all documents (initially hidden)
                    with gr.Group(visible=False) as confirm_dialog:
                        gr.Markdown('<div class="rtl-title"><h4>⚠️ تأیید حذف همه اسناد</h4></div>')
                        gr.Markdown("**آیا مطمئن هستید که می‌خواهید همه اسناد را حذف کنید؟**\n\nاین عملیات قابل بازگشت نیست!", rtl=True)
                        with gr.Row():
                            confirm_yes_btn = gr.Button("✅ بله، همه را حذف کن", variant="stop", size="sm")
                            confirm_no_btn = gr.Button("❌ انصراف", variant="secondary", size="sm")

                # Right column - Chat Interface
                with gr.Column(scale=2):
                    gr.Markdown('<div class="rtl-title"><h3>💬 چت با اسناد</h3></div>')
                    chatbot = gr.Chatbot(label="مکالمه", height=500, rtl=True)
                    msg = gr.Textbox(
                        label="سوال خود را بپرسید",
                        placeholder="سوال خود را در مورد قراردادها اینجا تایپ کنید...",
                        rtl=True
                    )
                    with gr.Row():
                        submit_btn = gr.Button("ارسال", variant="primary")
                        clear_chat_btn = gr.Button("پاک کردن گفتگو")

        # Tab 2: Deep Legal Analysis
        with gr.Tab("🔍 تحلیل عمیق حقوقی"):
            gr.Markdown('<div class="rtl-title"><h3>🔍 تحلیل عمیق حقوقی (۸ مرحله)</h3></div>')
            gr.Markdown("""
            <div style="direction: rtl; text-align: right;">
            این ابزار یک تحلیل جامع و چند مرحله‌ای از قرارداد شما انجام می‌دهد که شامل:

            - تحلیل ساختاری و شکلی
            - طبقه‌بندی تعهدات
            - بررسی شرایط مالی و زمانی
            - تحلیل ریسک و ابهامات
            - ارزیابی قابلیت اجرا

            **توجه:** این فرآیند ممکن است چند دقیقه طول بکشد.
            </div>
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    deep_analysis_file = gr.File(
                        label="آپلود فایل PDF قرارداد",
                        file_types=[".pdf"]
                    )
                    deep_analysis_btn = gr.Button(
                        "🚀 شروع تحلیل عمیق",
                        variant="primary",
                        size="lg"
                    )
                    deep_analysis_status = gr.Textbox(
                        label="وضعیت",
                        interactive=False,
                        rtl=True,
                        lines=3
                    )

                with gr.Column(scale=2):
                    deep_analysis_progress = gr.HTML(label="پیشرفت تحلیل")

            with gr.Row():
                deep_analysis_output = gr.Markdown(
                    label="نتایج تحلیل",
                    rtl=True,
                    value="نتایج تحلیل اینجا نمایش داده می‌شود..."
                )

    # Wire up the components - Tab 1: RAG Chat
    file_uploader.upload(
        fn=process_uploaded_file,
        inputs=file_uploader,
        outputs=[upload_status, documents_display]
    )

    refresh_docs_btn.click(
        fn=lambda: get_documents_list(),
        inputs=None,
        outputs=documents_display
    )

    delete_btn.click(
        fn=delete_document,
        inputs=doc_name_input,
        outputs=[delete_status, documents_display]
    )

    # Show confirmation dialog when "Clear All" is clicked
    clear_all_btn.click(
        fn=lambda: gr.update(visible=True),
        inputs=None,
        outputs=confirm_dialog
    )

    # Confirm deletion - clear all documents
    confirm_yes_btn.click(
        fn=clear_all_documents_confirmed,
        inputs=None,
        outputs=[delete_status, documents_display, confirm_dialog]
    )

    # Cancel deletion - hide dialog
    confirm_no_btn.click(
        fn=lambda: (gr.update(visible=False), "عملیات لغو شد."),
        inputs=None,
        outputs=[confirm_dialog, delete_status]
    )

    # The chat submission logic - clear the textbox after submission
    msg.submit(chat_interface_fn, [msg, chatbot], [chatbot]).then(
        lambda: "", None, msg
    )

    submit_btn.click(chat_interface_fn, [msg, chatbot], [chatbot]).then(
        lambda: "", None, msg
    )

    # The clear button logic - return empty list for chatbot
    clear_chat_btn.click(lambda: [], None, chatbot, queue=False)

    # Wire up the components - Tab 2: Deep Legal Analysis
    deep_analysis_btn.click(
        fn=run_deep_analysis_with_progress,
        inputs=deep_analysis_file,
        outputs=[deep_analysis_progress, deep_analysis_status, deep_analysis_output]
    )


if __name__ == "__main__":
    demo.launch()
