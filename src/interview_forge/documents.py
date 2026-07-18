from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from the document types supported by the MVP."""
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return _decode_text(content)
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix == ".docx":
        from docx import Document

        document = Document(BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return extract_image_text(content)
    raise ValueError("仅支持 PDF、DOCX、TXT、Markdown 和常见图片文件。")


def extract_image_text(content: bytes) -> str:
    """Run local OCR on an image and return text in reading order."""
    from PIL import Image

    try:
        image = Image.open(BytesIO(content)).convert("RGB")
    except (OSError, ValueError) as exc:
        raise ValueError("图片无法读取，请重新截图或转换为 PNG/JPG 后重试。") from exc

    result = _ocr_engine()(image)
    lines = _ocr_text_lines(result)
    if not lines:
        raise ValueError("没有从截图中识别到文字，请使用更清晰、分辨率更高的截图。")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _ocr_engine() -> Any:
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise RuntimeError("图片 OCR 组件尚未安装，请重新运行 requirements.txt 安装依赖。") from exc
    return RapidOCR()


def _ocr_text_lines(result: Any) -> list[str]:
    """Normalize RapidOCR 3.x output while tolerating its legacy tuple output."""
    texts = getattr(result, "txts", None)
    if texts is None and isinstance(result, tuple) and result:
        records = result[0] or []
        texts = [record[1] for record in records if len(record) > 1]
    return [str(text).strip() for text in (texts or []) if str(text).strip()]


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise ValueError("文本编码无法识别，请转换为 UTF-8 后重试。")
