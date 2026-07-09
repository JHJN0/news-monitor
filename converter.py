"""공고 파일(PDF/JPG/PNG)을 HTML 조각으로 변환한다."""
import base64

import fitz  # PyMuPDF

ALLOWED_IMAGE_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

# 페이지에서 뽑힌 텍스트가 이보다 짧으면 스캔본으로 보고 이미지로 렌더링한다
MIN_TEXT_LENGTH = 20


def pdf_to_html(data: bytes) -> str:
    """PDF를 페이지별 HTML로 변환. 텍스트 페이지는 XHTML 추출,
    스캔본(텍스트 없는) 페이지는 150dpi 이미지로 렌더링해 넣는다."""
    doc = fitz.open(stream=data, filetype="pdf")
    parts = []
    try:
        for page in doc:
            text = page.get_text().strip()
            if len(text) >= MIN_TEXT_LENGTH:
                parts.append(page.get_text("xhtml"))
            else:
                pix = page.get_pixmap(dpi=150)
                b64 = base64.b64encode(pix.tobytes("png")).decode()
                parts.append(
                    f'<img class="page-image" alt="공고 페이지"'
                    f' src="data:image/png;base64,{b64}">'
                )
    finally:
        doc.close()
    return "\n".join(
        f'<section class="notice-page">{p}</section>' for p in parts
    )


def image_to_html(data: bytes, ext: str) -> str:
    """JPG/PNG 이미지를 base64로 심은 HTML로 변환한다."""
    mimetype = ALLOWED_IMAGE_TYPES[ext]
    b64 = base64.b64encode(data).decode()
    return (
        '<section class="notice-page">'
        f'<img class="page-image" alt="공고 이미지"'
        f' src="data:{mimetype};base64,{b64}">'
        "</section>"
    )


def convert_to_html(data: bytes, filename: str) -> str:
    """확장자를 보고 알맞은 변환기를 고른다. 지원하지 않으면 ValueError."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return pdf_to_html(data)
    if ext in ALLOWED_IMAGE_TYPES:
        return image_to_html(data, ext)
    raise ValueError(f"지원하지 않는 형식입니다: .{ext} (pdf, jpg, png만 가능)")
