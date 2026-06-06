import PyPDF2
from core.logger import setup_logger

logger = setup_logger("PDFExtractor")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a given PDF file path."""
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        logger.info(f"Successfully extracted {len(text)} characters from {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        # Return empty string instead of crashing
        text = ""
    return text
