import fitz  # PyMuPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

def correct_rtl_text(text):
    """
    Corrects visually ordered (often reversed) Persian text for logical processing.
    """
    # This function should be used carefully. Text from PyMuPDF is often
    # already in a logical order, but sometimes it can be visually ordered.
    # Applying bidi correction to already logical text can scramble it.
    # We apply it here assuming the possibility of visually ordered text.
    reshaped_text = reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def normalize_text(text):
    """
    Normalizes Persian/Arabic numerals and common character variations.
    """
    persian_nums = "۰۱۲۳۴۵۶۷۸۹"
    arabic_nums = "٠١٢٣٤٥٦٧٨٩"
    english_nums = "0123456789"

    translation_table = str.maketrans(persian_nums + arabic_nums, english_nums * 2)
    text = text.translate(translation_table)

    # Standardize common character variations
    text = text.replace('ي', 'ی')
    text = text.replace('ك', 'ک')

    # Remove zero-width non-joiner, which can interfere with tokenization
    text = text.replace('\u200c', ' ')

    return text

def process_document(pdf_path):
    """
    Processes an uploaded PDF document by extracting, correcting, normalizing, and chunking text.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        # Normalize text first to standardize characters
        normalized_text = normalize_text(full_text)

        # Apply RTL correction line-by-line to avoid scrambling paragraphs
        lines = normalized_text.split('\n')
        corrected_lines = [correct_rtl_text(line) for line in lines]
        final_text = "\n".join(corrected_lines)

        # Use a text splitter optimized for legal documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "،", " ", ""],  # Prioritize splitting on semantic boundaries
        )

        chunks = text_splitter.split_text(final_text)
        return chunks

    except Exception as e:
        print(f"Error processing document: {e}")
        return []
