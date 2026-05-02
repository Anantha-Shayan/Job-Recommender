import os
import pdfplumber
from PIL import Image
from PIL import ImageDraw
import pandas as pd
#import pytesseract
#import easyocr # more accurate
#import docx2pdf # requires MSWord(Windows) to be installed
#import pdf2image #requires poppler installation
import fitz #PyMuPdf
import tempfile
import io
#import flask
# import requests
# from fastapi import FastAPI, HTTPException
#import streamlit as st
# from Layout_detection_and_Semantic_segmentation import process_document_for_layout_and_semantic
#import pythoncom
import subprocess
import os
import tempfile
import hashlib


# PDF PARSER (Line-Based Section Detection)
def pdf_resume(file):
    file.seek(0)
    file_bytes = file.read()
    result_text = ""
    images = []
    word_bboxes = []   # kept for compatibility
    headings = {}
    headings_area = {}

    # Render images using PyMuPDF (kept for layout pipeline compatibility)
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        images.append(buf.getvalue())
    doc.close()

    # Simple line based parser
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        sections = {}
        section_keywords = [
            "skills",
            "technical skills",
            "experience",
            "work experience",
            "education",
            "achievements",
            "projects",
            "summary",
            "professional summary"
        ]

        current_section = None

        for page_num, page in enumerate(pdf.pages):

            page_text = page.extract_text() or ""
            result_text += page_text + "\n"

            lines = page_text.split('\n')

            for raw_line in lines:
                clean_line = raw_line.strip()
                lower_line = clean_line.lower()

                if not clean_line:
                    continue

                # Heading detection
                is_heading = (
                    any(keyword in lower_line for keyword in section_keywords)
                    and len(clean_line.split()) <= 4
                    and not clean_line.endswith(".")
                )

                if is_heading:
                    # Normalize section name
                    for keyword in section_keywords:
                        if keyword in lower_line:
                            current_section = keyword
                            break

                    if current_section not in sections:
                        sections[current_section] = []

                    continue  #prevents heading itself from being added

                # Collect content under active section
                if current_section:
                    sections[current_section].append(clean_line)

        headings_area = sections  # For compatibility with old UI structure

    return result_text, headings, headings_area, images, word_bboxes


#docx parser
def docx_resume(file):

    # Create a persistent cache directory
    CACHE_DIR = "cache_pdfs"
    os.makedirs(CACHE_DIR, exist_ok=True)

    file.seek(0)
    file_bytes = file.read()

    # Generate unique hash for file
    file_hash = hashlib.md5(file_bytes).hexdigest()

    # Define cached paths
    docx_path = os.path.join(CACHE_DIR, f"{file_hash}.docx")
    pdf_path = os.path.join(CACHE_DIR, f"{file_hash}.pdf")

    # Save docx if not cached
    if not os.path.exists(docx_path):
        with open(docx_path, "wb") as f:
            f.write(file_bytes)

    # Convert if pdf not cached
    if not os.path.exists(pdf_path):
        try:
            subprocess.run([
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                docx_path,
                "--outdir", CACHE_DIR
            ], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LibreOffice conversion failed: {e}")

    with open(pdf_path, "rb") as pdf_file:
        return pdf_resume(pdf_file)
    

# ==========================================
# STREAMLIT UI
# # ==========================================

# st.set_page_config(page_title="Resume Parsing", page_icon="🤖", layout="wide")
# st.title("📄 Resume Parsing")

# st.sidebar.header("Upload Document")
# uploaded_file = st.sidebar.file_uploader(
#     "Upload a PDF or DOCX file",
#     type=["pdf", "docx"]
# )

# if uploaded_file is not None:
#     file_type = uploaded_file.name.split(".")[-1].lower()

#     with st.spinner("🔍 Extracting text..."):
#         if file_type == "pdf":
#             text, headings, headings_area, image, word_bboxes = pdf_resume(uploaded_file)
#         elif file_type == "docx":
#             text, headings, headings_area, image, word_bboxes = docx_resume(uploaded_file)
#         else:
#             st.error("Unsupported file type")
#             st.stop()

#     st.session_state.document_text = text
#     st.session_state.document_headings = headings
#     st.session_state.document_headings_area = headings_area
#     st.session_state.document_image = image
#     st.session_state.bboxes = word_bboxes

#     uploaded_file.seek(0)
#     doc_results = process_document_for_layout_and_semantic(
#         file_bytes=uploaded_file.read(),
#         image_bytes_list=image
#     )


# # ==========================================
# # DISPLAY RESULTS
# # ==========================================

# if "document_text" in st.session_state:

#     with st.expander("📜 Extracted Document Text"):
#         st.text_area("Text Output", st.session_state.document_text, height=200)

#         with st.expander("📂 Parsed Sections"):
#             st.json(st.session_state.document_headings_area)


# # ==========================================
# # CHAT PLACEHOLDER
# # ==========================================

# st.subheader("💬 Chat with Document")

# user_input = st.text_input("Ask something about the document...")

# if st.button("Send") and user_input.strip():
#     st.write("🤖 Bot: Resume chat coming soon!")