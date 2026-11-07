
from pathlib import Path
from uuid import uuid4
from io import BytesIO
from html import unescape
from html.parser import HTMLParser
import re
import zipfile
import tempfile
import subprocess
import shutil

from docx import Document
from pypdf import PdfReader
from fastapi import HTTPException, UploadFile


UPLOAD_DIRECTORY = Path("uploads/resumes")
MAX_FILE_SIZE = 5 * 1024 * 1024

TESSERACT_EXE = (
    r"C:\Users\mainu\Desktop\tesseract.exe"
)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".rtf",
    ".odt", ".html", ".htm", ".png", ".jpg", ".jpeg"
}


class ResumeHTMLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_content = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip_content = True

        if tag in ("p", "div", "br", "li", "tr", "h1", "h2", "h3"):
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip_content = False

        if tag in ("p", "div", "li", "tr"):
            self.text_parts.append("\n")

    def handle_data(self, data):
        if not self.skip_content:
            self.text_parts.append(data)

    def get_text(self):
        return "\n".join(self.text_parts)


def extract_html_text(content: bytes) -> str:
    decoded = content.decode("utf-8", errors="replace")
    parser = ResumeHTMLParser()
    parser.feed(decoded)
    return unescape(parser.get_text())


def extract_txt_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("Unable to decode text file.")


def extract_rtf_text(content: bytes) -> str:
    raw = content.decode("latin-1", errors="replace")

    if not raw.lstrip().startswith("{\\rtf"):
        raise ValueError("Invalid RTF document.")

    raw = re.sub(r"\{\\\*[^{}]*\}", "", raw)
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\(?:par|line|tab)\b ?", "\n", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", raw)
    raw = re.sub(r"[{}]", "", raw)

    return raw.strip()


def extract_docx_text(content: bytes) -> str:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("Invalid DOCX document.")

    document = Document(BytesIO(content))
    parts = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)

    for table in document.tables:
        for row in table.rows:
            parts.append(
                " | ".join(
                    cell.text.strip()
                    for cell in row.cells
                )
            )

    return "\n".join(parts)


def extract_odt_text(content: bytes) -> str:
    from xml.etree import ElementTree

    with zipfile.ZipFile(BytesIO(content)) as archive:
        if "content.xml" not in archive.namelist():
            raise ValueError("Invalid ODT document.")

        xml_content = archive.read("content.xml")

    root = ElementTree.fromstring(xml_content)

    return "\n".join(
        text.strip()
        for text in root.itertext()
        if text.strip()
    )


def extract_doc_text(content: bytes) -> str:
    libreoffice = (
        shutil.which("libreoffice")
        or shutil.which("soffice")
    )
    antiword = shutil.which("antiword")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_file = temp_path / "resume.doc"
        source_file.write_bytes(content)

        if libreoffice:
            output_dir = temp_path / "converted"
            output_dir.mkdir()

            result = subprocess.run(
                [
                    libreoffice,
                    "--headless",
                    "--convert-to",
                    "txt:Text",
                    "--outdir",
                    str(output_dir),
                    str(source_file)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            output_file = output_dir / "resume.txt"

            if result.returncode == 0 and output_file.exists():
                return output_file.read_text(
                    encoding="utf-8",
                    errors="replace"
                )

        if antiword:
            result = subprocess.run(
                [antiword, str(source_file)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout

    raise ValueError(
        "DOC extraction requires LibreOffice or antiword. "
        "Install one of these tools and try again."
    )


def configure_tesseract():
    import pytesseract

    if not Path(TESSERACT_EXE).is_file():
        raise FileNotFoundError(
            f"Tesseract executable not found: {TESSERACT_EXE}"
        )

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

    return pytesseract


def extract_image_ocr(content: bytes) -> str:
    try:
        from PIL import Image

        pytesseract = configure_tesseract()

        with Image.open(BytesIO(content)) as image:
            image.verify()

        with Image.open(BytesIO(content)) as image:
            image = image.convert("RGB")

            extracted_text = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--psm 3"
            )

        return extracted_text.strip()

    except ImportError as exc:
        raise ValueError(
            "Image OCR requires Pillow and pytesseract. "
            "Install them using pip."
        ) from exc

    except Exception as exc:
        raise ValueError(
            f"Image OCR extraction failed: {exc}"
        ) from exc


def extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))

    if reader.is_encrypted:
        raise ValueError(
            "Password-protected PDFs are not supported."
        )

    text_parts = []

    for page in reader.pages:
        text_parts.append(page.extract_text() or "")

    extracted_text = "\n".join(text_parts).strip()

    if extracted_text:
        return extracted_text

    try:
        from pdf2image import convert_from_bytes

        pytesseract = configure_tesseract()

        images = convert_from_bytes(
            content,
            dpi=200,
            fmt="png"
        )

        extracted_text = "\n".join(
            pytesseract.image_to_string(
                image,
                lang="eng"
            )
            for image in images
        )

    except ImportError as exc:
        raise ValueError(
            "This PDF appears to be scanned. "
            "Install pdf2image, pytesseract and Pillow."
        ) from exc

    except Exception as exc:
        raise ValueError(
            f"Scanned PDF OCR failed: {exc}. "
            "Check Tesseract OCR and Poppler installation."
        ) from exc

    return extracted_text.strip()


def validate_file(extension: str, content: bytes) -> None:
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file.")

    elif extension in {".docx", ".odt"}:
        if not zipfile.is_zipfile(BytesIO(content)):
            raise ValueError("Invalid Office document.")

    elif extension == ".doc":
        if not content.startswith(b"\xD0\xCF\x11\xE0"):
            raise ValueError("Invalid DOC file.")

    elif extension in {".jpg", ".jpeg"}:
        if not content.startswith(b"\xFF\xD8\xFF"):
            raise ValueError("Invalid JPEG image.")

    elif extension == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Invalid PNG image.")

    elif extension == ".rtf":
        if not content.lstrip().startswith(b"{\\rtf"):
            raise ValueError("Invalid RTF file.")

    elif extension in {".html", ".htm"}:
        if b"<" not in content:
            raise ValueError("Invalid HTML file.")


def extract_resume_text(extension: str, content: bytes) -> str:
    extractors = {
        ".pdf": extract_pdf_text,
        ".docx": extract_docx_text,
        ".doc": extract_doc_text,
        ".txt": extract_txt_text,
        ".rtf": extract_rtf_text,
        ".odt": extract_odt_text,
        ".html": extract_html_text,
        ".htm": extract_html_text,
        ".png": extract_image_ocr,
        ".jpg": extract_image_ocr,
        ".jpeg": extract_image_ocr
    }

    extractor = extractors.get(extension)

    if extractor is None:
        raise ValueError("Unsupported resume format.")

    return extractor(content)


async def process_resume(file: UploadFile) -> tuple[str, str]:
    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Upload PDF, DOCX, DOC, TXT, RTF, ODT, "
                "HTML, PNG or JPG."
            )
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Resume must not exceed 5 MB."
        )

    try:
        validate_file(extension, content)

        text = extract_resume_text(
            extension,
            content
        )

        if not text or not text.strip():
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text was found. "
                    "The document may be scanned, "
                    "image-only or unreadable."
                )
            )

        UPLOAD_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True
        )

        generated_filename = f"{uuid4().hex}{extension}"
        destination = UPLOAD_DIRECTORY / generated_filename
        destination.write_bytes(content)

        relative_path = str(
            Path("uploads") / "resumes" / generated_filename
        )

        return text.strip(), relative_path

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Unable to process this resume file."
        ) from exc


def delete_resume_file(relative_path: str) -> None:
    path = Path(relative_path)

    if path.parent == Path("uploads/resumes"):
        if path.exists() and path.is_file():
            path.unlink()
