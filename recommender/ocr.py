import os
import pdfplumber
from PIL import Image
#import pytesseract
import easyocr # more accurate
import docx2pdf
#import pdf2image #requires poppler installation
import fitz #PyMuPdf
import tempfile
import io
#import flask
# import requests
# from fastapi import FastAPI, HTTPException
import streamlit as st
from Layout_detection_and_Semantic_segmentation import process_document_for_layout_and_semantic

#app = FastAPI(title = "Resume")

#@app.post("/upload")
# def upload_file():
#     file = requests.files['Resume']
#     filename = file.filename.lower()
#     if filename.endswith('.pdf'):
#         pdf_resume(file)
#     elif filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg'):
#         img_resume(file)        
#     elif filename.endswith('.docx'):
#         docx_resume(file)
#     else:
#         print("Enter only pdf/jpg/docx")
        
#pdf to text
def pdf_resume(file):
    file_bytes = file.read()
    result = ""
    images = []

    # Render images using PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        # create a PIL Image from pix
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # convert PIL image to PNG bytes
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        images.append(buf.getvalue())
    doc.close()

    # Extract text
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            result += page.extract_text() or ""

    return [result, images]


# image to text
def img_resume(file): """Image parser (easyocr) is not even close to accurate. Change is the end"""
    # read the uploaded file bytes
    img_bytes = file.read()

    # For OCR: easyocr works with numpy arrays or PIL; keep it simple:
    reader = easyocr.Reader(['en'])
    # easyocr can accept bytes via numpy; use PIL to open then pass to reader.readtext
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    # get numpy array for easyocr
    import numpy as np
    np_img = np.array(pil_img)

    result = reader.readtext(np_img, detail=0)

    # return OCR result and list of image bytes (keep same shape as pdf_resume)
    return [result, [img_bytes]]


# docx to text
def docx_resume(file):
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, file.name)
        file.seek(0)
        with open(docx_path, "wb") as f:
            f.write(file.read())

        pdf_path = os.path.join(tmpdir, "resume.pdf")
        # convert docx -> pdf
        docx2pdf.convert(docx_path, pdf_path)

        # open the PDF and pass the file object to pdf_resume exactly once
        with open(pdf_path, "rb") as pdf_file:
            text, images = pdf_resume(pdf_file)

    return [text, images]


#f = io.open('D:\\python\\job_rec\\recommender\\Screenshot (337).png',encoding='utf8')
with open('D:\\python\\job_rec\\recommender\\ss.png','rb') as f:
    print(img_resume(f))
# with open('D:\\python\\job_rec\\recommender\\RESUME.pdf','r') as file:
#     filename = file.filename.lower()
#     if filename.endswith('.pdf'):
#         text = pdf_resume(file)
#     elif filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg'):
#         text = img_resume(file)        
#     elif filename.endswith('.docx'):
#         text = docx_resume(file)
#     else:
#         print("Enter only pdf/jpg/docx")

#streamlit ui      
# st.set_page_config(page_title="Resume Parsing", page_icon="🤖", layout="wide")
# st.title("📄 Resume Parsing")

# st.sidebar.header("Upload Document")
# uploaded_file = st.sidebar.file_uploader(
#     "Upload a PDF, DOCX, or Image file",
#     type=["pdf", "docx", "png", "jpg", "jpeg"]
# )

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
# if "document_text" not in st.session_state:
#     st.session_state.document_text = ""

# if uploaded_file is not None:
#     file_type = uploaded_file.name.split(".")[-1].lower()
#     with st.spinner("🔍 Extracting text..."):
#         if file_type == "pdf":
#             text,image = pdf_resume(uploaded_file)
#         elif file_type == "docx":
#             text,image = docx_resume(uploaded_file)
#         elif file_type in ["png", "jpg", "jpeg"]:
#             text,image = img_resume(uploaded_file)
#         else:
#             text = "Unsupported file type!"
#             image = "Invalid"
#     st.session_state.document_text = text
#     st.session_state.document_image = image
#     doc_results = process_document_for_layout_and_semantic(file_bytes=uploaded_file.read(), image_bytes_list=image)

    

# # ---------- Show extracted text ----------
# if st.session_state.document_text:
#     with st.expander("📜 Extracted Document Text"):
#         st.text_area("", st.session_state.document_text, height=200)
            
#     with st.expander("📜 Extracted Image"):
#         images = []
#         for img_bytes in st.session_state.document_image:
#             # img_bytes is expected to be raw image bytes (PNG/JPEG)
#             img = Image.open(io.BytesIO(img_bytes))
#             images.append(img)
#             st.image(img, use_container_width=True)

# # ---------- Chat Interface ----------
# st.subheader("💬 Chat with Document")

# user_input = st.text_input("Ask something about the document...", key="user_input")
# if st.button("Send") and user_input.strip():
#     user_msg = {"role": "user", "content": user_input}
#     st.session_state.chat_history.append(user_msg)

#     # Dummy bot response (replace with LangChain or API call)
#     response = f"I received your question.\n(Soon, I’ll analyze your document for a real answer!)"
#     bot_msg = {"role": "assistant", "content": response}
#     st.session_state.chat_history.append(bot_msg)

# # ---------- Display Chat ----------
# for chat in st.session_state.chat_history:
#     if chat["role"] == "user":
#         st.markdown(f"🧑‍💻 **You:** {chat['content']}")
#     else:
#         st.markdown(f"🤖 **Bot:** {chat['content']}")