# layout_detection_and_semantic_segmentation.py
from typing import List, Tuple, Dict, Any
from PIL import Image
import io
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
import easyocr
import numpy as np

# -------------------------------------------------------------------------
# Utilities: bbox conversions & normalization
# -------------------------------------------------------------------------
def bbox_from_easyocr_bbox(easy_bbox: List[List[float]]) -> Tuple[float, float, float, float]:
    """
    easyocr bbox format: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    Return xmin, ymin, xmax, ymax
    """
    xs = [p[0] for p in easy_bbox]
    ys = [p[1] for p in easy_bbox]
    return float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))


def normalize_bbox(bbox: Tuple[float, float, float, float], page_width: float, page_height: float) -> List[int]:
    """
    Normalize bbox to 0-1000 integer coordinates for LayoutLM.
    bbox = (x0, y0, x1, y1) in original pixel/PDF coordinates.
    """
    x0, y0, x1, y1 = bbox
    # clamp
    x0 = max(0.0, min(x0, page_width))
    x1 = max(0.0, min(x1, page_width))
    y0 = max(0.0, min(y0, page_height))
    y1 = max(0.0, min(y1, page_height))

    def scale_x(x): return int(round((x / page_width) * 1000))
    def scale_y(y): return int(round((y / page_height) * 1000))

    nx0, ny0, nx1, ny1 = scale_x(x0), scale_y(y0), scale_x(x1), scale_y(y1)
    # ensure valid integers in [0,1000]
    nx0, ny0, nx1, ny1 = max(0, nx0), max(0, ny0), min(1000, nx1), min(1000, ny1)
    return [nx0, ny0, nx1, ny1]


# -------------------------------------------------------------------------
# Extract word bboxes from PDFs (text layer) using PyMuPDF or pdfplumber
# -------------------------------------------------------------------------
def extract_words_bboxes_pymupdf(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Uses PyMuPDF to extract word-level bboxes for each page.
    Returns list where each element is a dict:
      {
        "page_index": int,
        "width": page_width,
        "height": page_height,
        "words": [ (word_text, (x0,y0,x1,y1)), ... ]
      }
    Coordinates are in PDF coordinate space (points).
    """
    res = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        for i in range(len(doc)):
            page = doc.load_page(i)
            rect = page.rect
            page_width, page_height = rect.width, rect.height
            words = page.get_text("words")  # list of tuples: (x0, y0, x1, y1, "word", block_no)
            words_list = []
            for w in words:
                x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
                if (text or "").strip():
                    words_list.append((text, (x0, y0, x1, y1)))
            res.append({
                "page_index": i,
                "width": page_width,
                "height": page_height,
                "words": words_list
            })
    finally:
        doc.close()
    return res


def extract_words_bboxes_pdfplumber(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Alternate extractor using pdfplumber. Coordinates are in points:
    returns same structure as PyMuPDF extractor.
    """
    res = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            w, h = page.width, page.height
            words = page.extract_words()  # list of dicts with 'x0', 'top', 'x1', 'bottom', 'text'
            words_list = []
            for wdict in words:
                text = wdict.get("text", "").strip()
                if not text:
                    continue
                x0, y0, x1, y1 = wdict["x0"], wdict["top"], wdict["x1"], wdict["bottom"]
                words_list.append((text, (x0, y0, x1, y1)))
            res.append({
                "page_index": i,
                "width": w,
                "height": h,
                "words": words_list
            })
    return res


# -------------------------------------------------------------------------
# Extract token bboxes from image (scanned PDFs / images)
# -------------------------------------------------------------------------
def extract_bboxes_from_image_bytes_easyocr(img_bytes: bytes, languages: List[str] = ["en"]) -> Dict[str, Any]:
    """
    Uses EasyOCR to extract bounding boxes and text from a single image.
    Returns:
      {
        "width": img_width,
        "height": img_height,
        "words": [ (text, (x0,y0,x1,y1)), ... ]
      }
    """
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    np_img = np.array(pil_img)
    reader = easyocr.Reader(languages, gpu=False)  # set gpu=True if GPU available
    raw = reader.readtext(np_img, detail=1)  # list of (bbox, text, confidence)
    words = []
    for bbox, text, conf in raw:
        if (text or "").strip():
            xmin, ymin, xmax, ymax = bbox_from_easyocr_bbox(bbox)
            words.append((text, (xmin, ymin, xmax, ymax)))
    width, height = pil_img.width, pil_img.height
    return {"width": width, "height": height, "words": words}


def extract_bboxes_from_image_pytesseract(img_bytes: bytes) -> Dict[str, Any]:
    """
    Uses pytesseract to extract word boxes and text from a single image.
    Returns same format as easyocr function above.
    """
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    words = []
    n = len(data["text"])
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue
        x = int(data["left"][i]); y = int(data["top"][i])
        w = int(data["width"][i]); h = int(data["height"][i])
        words.append((txt, (x, y, x + w, y + h)))
    return {"width": pil_img.width, "height": pil_img.height, "words": words}


# -------------------------------------------------------------------------
# Build LayoutLM-style per-page inputs: tokens + normalized bboxes
# -------------------------------------------------------------------------
def build_layoutlm_page_inputs_from_pdf_bytes(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    If the PDF has a text layer, prefer PyMuPDF extractor.
    Returns list per page:
      {
        "page_index": int,
        "page_image": PIL.Image or None,
        "tokens": [token1, token2, ...],
        "bboxes": [[x0,y0,x1,y1], ...]  # normalized 0-1000 ints
        "original_bboxes": [(x0,y0,x1,y1), ...],  # original coords in PDF pts
        "width": original_width, "height": original_height
      }
    """
    pages = extract_words_bboxes_pymupdf(file_bytes)
    out_pages = []
    for p in pages:
        tokens = []
        bboxes = []
        original = []
        w, h = p["width"], p["height"]
        for (word, obox) in p["words"]:
            tokens.append(word)
            original.append(obox)
            bboxes.append(normalize_bbox(obox, w, h))
        out_pages.append({
            "page_index": p["page_index"],
            "page_image": None,
            "tokens": tokens,
            "bboxes": bboxes,
            "original_bboxes": original,
            "width": w,
            "height": h
        })
    return out_pages


def build_layoutlm_page_inputs_from_image_bytes_list(img_bytes_list: List[bytes], use_easyocr: bool = True) -> List[Dict[str, Any]]:
    """
    For scanned PDF pages or standalone images.
    img_bytes_list: list of raw image bytes (one entry per page)
    Returns same structure as build_layoutlm_page_inputs_from_pdf_bytes, but for images.
    """
    out_pages = []
    for i, b in enumerate(img_bytes_list):
        if use_easyocr:
            page_data = extract_bboxes_from_image_bytes_easyocr(b)
        else:
            page_data = extract_bboxes_from_image_pytesseract(b)
        tokens = []
        bboxes = []
        original = []
        w, h = page_data["width"], page_data["height"]
        for (word, obox) in page_data["words"]:
            tokens.append(word)
            original.append(obox)
            bboxes.append(normalize_bbox(obox, w, h))
        # keep page image PIL for visualization downstream:
        pil_img = Image.open(io.BytesIO(b)).convert("RGB")
        out_pages.append({
            "page_index": i,
            "page_image": pil_img,
            "tokens": tokens,
            "bboxes": bboxes,
            "original_bboxes": original,
            "width": w,
            "height": h
        })
    return out_pages


# -------------------------------------------------------------------------
# Simple heuristic semantic segmentation (header-based) - useful as a fallback
# -------------------------------------------------------------------------
HEADER_KEYWORDS = {
    "skills": ["skills", "technical skills", "technical proficiencies", "skillset"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "summary": ["summary", "professional summary", "profile", "about me"],
    "languages": ["languages", "spoken languages"],
    "tools": ["tools", "tools & technologies", "technologies", "tech stack"],
    "libraries": ["libraries", "frameworks", "packages"]
}


def simple_header_grouping(page_tokens: List[str], page_boxes: List[List[int]], page_width: int, page_height: int) -> Dict[str, List[str]]:
    """
    Very simple rule: find tokens that equal a header keyword (case-insensitive),
    then collect subsequent tokens that are vertically below the header and before the next header.
    This is a heuristic fallback ONLY — used for prototyping.
    Returns dict mapping section->list of token strings (joined later).
    """
    # build list of (token, bbox, y_center)
    items = []
    for t, b in zip(page_tokens, page_boxes):
        x0, y0, x1, y1 = b
        y_center = (y0 + y1) / 2
        items.append({"token": t, "bbox": b, "y_center": y_center})
    # detect header tokens by text match:
    headers = []
    lowered_tokens = [t.lower() for t in page_tokens]
    for idx, tok in enumerate(lowered_tokens):
        for section, keywords in HEADER_KEYWORDS.items():
            for kw in keywords:
                if tok.strip().startswith(kw):  # header candidate
                    headers.append({"index": idx, "section": section, "y": items[idx]["y_center"]})
                    break
    # if no headers found, return empty groups
    if not headers:
        return {}
    # sort headers by y (top to bottom)
    headers = sorted(headers, key=lambda x: x["y"])
    groups = {h["section"]: [] for h in headers}
    # for each header, take tokens until next header.y
    for i, h in enumerate(headers):
        top_y = h["y"]
        bottom_y = headers[i + 1]["y"] if i + 1 < len(headers) else page_height + 1
        for it in items:
            if it["y_center"] > top_y and it["y_center"] < bottom_y:
                groups[h["section"]].append(it["token"])
    # join tokens into small strings per section
    groups = {k: [" ".join(groups[k]).strip()] if groups[k] else [] for k in groups}
    return groups


# -------------------------------------------------------------------------
# Public wrapper: main entrypoint used by your Streamlit app
# -------------------------------------------------------------------------
def process_document_for_layout_and_semantic(file_bytes: bytes = None,
                                             image_bytes_list: List[bytes] = None,
                                             prefer_pdf_text_layer: bool = True,
                                             use_easyocr: bool = True) -> Dict[str, Any]:
    """
    Main wrapper. You can call this from your Streamlit app.
    Provide either:
      - file_bytes (PDF bytes)  -> will attempt to extract text-layer boxes (PyMuPDF),
        and also will render page images for possible OCR/visual models; OR
      - image_bytes_list -> for scanned pages or images.

    Returns:
    {
      "pages": [
        {
          "page_index": int,
          "page_image": PIL.Image or None,
          "tokens": [...],
          "bboxes": [[x0,y0,x1,y1], ...],  # normalized 0-1000
          "original_bboxes": [...],
          "width": ...,
          "height": ...
        }, ...
      ],
      "simple_section_groups": { "page_0": {section: [text, ...]}, ... }
    }
    """
    pages_out = []
    simple_groups = {}

    if file_bytes is not None and prefer_pdf_text_layer:
        try:
            pages_out = build_layoutlm_page_inputs_from_pdf_bytes(file_bytes)
            # also produce page_image for each page by rendering with PyMuPDF to pass downstream if needed:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for p in pages_out:
                page_idx = p["page_index"]
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # render double resolution
                pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                p["page_image"] = pil_img
            doc.close()
        except Exception:
            # fallback to pdfplumber + image OCR path
            pages_out = []
            image_bytes_list = image_bytes_list or []
    # if pages_out empty and we have images (scanned)
    if not pages_out and image_bytes_list:
        pages_out = build_layoutlm_page_inputs_from_image_bytes_list(image_bytes_list, use_easyocr=use_easyocr)

    # build simple heuristic groupings for each page as an immediate fallback
    for p in pages_out:
        page_index = p["page_index"]
        groups = simple_header_grouping(p["tokens"], p["bboxes"], p["width"], p["height"])
        simple_groups[f"page_{page_index}"] = groups

    return {"pages": pages_out, "simple_section_groups": simple_groups}



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1].endswith(".pdf"):
        with open(sys.argv[1], "rb") as f:
            out = process_document_for_layout_and_semantic(file_bytes=f.read())
            import json
            print(json.dumps({"pages": [{"page_index": p["page_index"], "n_tokens": len(p["tokens"])} for p in out["pages"]]}, indent=2))
    else:
        print("Usage: python layout_detection_and_semantic_segmentation.py <file.pdf>")
