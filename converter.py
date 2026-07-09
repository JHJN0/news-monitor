"""공고 파일(PDF/JPG/PNG)을 게시판 에디터 스타일 HTML로 변환한다.

출력 형식 예:
<p style="text-align: center; line-height: 180%;"><span style="font-weight: bold; font-size: 18pt;">제목</span></p>
<p style="text-align: left; line-height: 180%;"><span style="font-size: 12pt;">가. 항목 내용</span></p>
"""
import base64
import html as html_lib
import re

import fitz  # PyMuPDF

ALLOWED_IMAGE_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

# 페이지에서 뽑힌 텍스트가 이보다 짧으면 스캔본으로 보고 이미지로 렌더링한다
MIN_TEXT_LENGTH = 20

# 이보다 작은 임베디드 이미지는 장식(로고·아이콘)으로 보고 건너뛴다
MIN_IMAGE_BYTES = 5000

# 항목 시작 표시: 가. 나. 다. / 1. 2. / ○ ● □ ■ ◦ ▶ ※ · - 등
ITEM_MARKER_RE = re.compile(
    r"^(?:[가-힣]\.\s|\d{1,2}[.)]\s|[○●◎◦□■◇◆▶▷•·※★☆➤>-]\s?)"
)
ATTACHMENT_RE = re.compile(r"^붙\s*임")

LINE_STYLE = "line-height: 180%;"


def _para(inner, align="left"):
    return f'<p style="text-align: {align}; {LINE_STYLE}">{inner}</p>'


def _text_para(text, align="left", size=12, bold=False):
    weight = "font-weight: bold; " if bold else ""
    escaped = html_lib.escape(text)
    return _para(f'<span style="{weight}font-size: {size}pt;">{escaped}</span>', align)


def _blank_para():
    return _para('<span style="font-size: 12pt;"><br /></span>')


def _image_para(mimetype, data):
    b64 = base64.b64encode(data).decode()
    img = (
        f'<img src="data:{mimetype};base64,{b64}" title="" alt=""'
        ' style="vertical-align: baseline; max-width: 100%; height: auto;" />'
    )
    return _para(img, align="center")


def _extract_lines_and_images(doc):
    """PDF에서 텍스트 줄 목록과 이미지(HTML 문단) 목록을 뽑는다."""
    lines = []
    image_paras = []
    for page in doc:
        text = page.get_text().strip()
        if len(text) < MIN_TEXT_LENGTH:
            # 스캔본 페이지는 통째로 이미지로 렌더링
            pix = page.get_pixmap(dpi=150)
            image_paras.append(_image_para("image/png", pix.tobytes("png")))
            continue
        lines.extend(line.strip() for line in text.splitlines())
        for img_info in page.get_images(full=True):
            extracted = doc.extract_image(img_info[0])
            if extracted and len(extracted["image"]) >= MIN_IMAGE_BYTES:
                mimetype = ALLOWED_IMAGE_TYPES.get(
                    extracted["ext"].lower(), "image/png"
                )
                image_paras.append(_image_para(mimetype, extracted["image"]))
    return lines, image_paras


def _build_body_paras(lines):
    """줄 목록을 항목 단위 문단으로 묶는다.
    가./○/1. 같은 표시로 시작하면 새 문단, 아니면 앞 문단에 이어붙인다.
    붙임 부분 앞에는 빈 줄을 넣는다."""
    paras = []
    buffer = ""
    attachment_started = False

    def flush():
        nonlocal buffer
        if buffer:
            paras.append(_text_para(buffer))
            buffer = ""

    for line in lines:
        if not line:
            flush()
            continue
        if ATTACHMENT_RE.match(line) and not attachment_started:
            flush()
            paras.append(_blank_para())
            attachment_started = True
            buffer = line
            continue
        if ITEM_MARKER_RE.match(line):
            flush()
            buffer = line
            continue
        buffer = f"{buffer} {line}" if buffer else line
    flush()
    return paras


def pdf_to_html(data: bytes) -> str:
    """PDF를 게시판 스타일 HTML로 변환한다.
    구조: 제목(가운데·굵게·18pt) → 이미지(가운데) → 항목별 본문(12pt) → 붙임."""
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        lines, image_paras = _extract_lines_and_images(doc)
    finally:
        doc.close()

    lines = [line for line in lines]
    # 첫 번째 내용 있는 줄을 제목으로 사용
    title = ""
    body_lines = []
    for i, line in enumerate(lines):
        if line:
            title = line
            body_lines = lines[i + 1:]
            break

    parts = []
    if title:
        parts.append(_text_para(title, align="center", size=18, bold=True))
        parts.append(_blank_para())
    if image_paras:
        parts.extend(image_paras)
        parts.append(_blank_para())
    parts.extend(_build_body_paras(body_lines))
    if not parts:
        raise ValueError("PDF에서 내용을 추출하지 못했습니다.")
    return "\n".join(parts)


def image_to_html(data: bytes, ext: str) -> str:
    """JPG/PNG 이미지를 게시판 스타일 HTML로 변환한다."""
    return _image_para(ALLOWED_IMAGE_TYPES[ext], data)


def convert_to_html(data: bytes, filename: str) -> str:
    """확장자를 보고 알맞은 변환기를 고른다. 지원하지 않으면 ValueError."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return pdf_to_html(data)
    if ext in ALLOWED_IMAGE_TYPES:
        return image_to_html(data, ext)
    raise ValueError(f"지원하지 않는 형식입니다: .{ext} (pdf, jpg, png만 가능)")
