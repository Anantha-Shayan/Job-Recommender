import os
import pdfplumber
from PIL import Image
from PIL import ImageDraw
import pandas as pd
#import pytesseract
#import easyocr # more accurate
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
import pythoncom
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
    file.seek(0)
    file_bytes = file.read()
    result_text = ""
    images = []
    word_bboxes = []

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
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                result_text += page_text
                
                # Collect character bboxes
                for word in page.extract_words():
                    word_bboxes.append({
                        "char": word["text"],
                        "bbox": (word["x0"], word["top"], word["x1"], word["bottom"]),
                        "page": page_num
                    })
    
    if len(result_text.strip()) < 30:
            return ["PDF parsing failed. Please try with .docx", [],[]] #pdf is scanned and we don't have OCR 
                            
    return [result_text, images, word_bboxes]

#OCR quality is very low. Hence this is a trade-off
# # image to text
# """Image parser (easyocr) is not even close to accurate. Change to maybe a paid model in the end"""
# def img_resume(file): 
#     # read the uploaded file bytes
#     img_bytes = file.read()

#     # For OCR: easyocr works with numpy arrays or PIL; keep it simple:
#     reader = easyocr.Reader(['en'])
#     # easyocr can accept bytes via numpy; use PIL to open then pass to reader.readtext
#     pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
#     # get numpy array for easyocr
#     import numpy as np
#     np_img = np.array(pil_img)

#     result = reader.readtext(np_img, detail=0)

#     # return OCR result and list of image bytes (keep same shape as pdf_resume)
#     return [result, [img_bytes]]


# docx to text
def docx_resume(file):
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, file.name)
        file.seek(0)
        with open(docx_path, "wb") as f:
            f.write(file.read())

        pdf_path = os.path.join(tmpdir, "resume.pdf")
        
        # Initialize COM for the Streamlit thread
        pythoncom.CoInitialize()
        try:
            # convert docx -> pdf
            docx2pdf.convert(docx_path, pdf_path)
        finally:
            # Always uninitialize, even if the conversion fails
            pythoncom.CoUninitialize()

        # open the PDF and pass the file object to pdf_resume exactly once
        with open(pdf_path, "rb") as pdf_file:
            text, images, word_bboxes = pdf_resume(pdf_file)

    return [text, images, word_bboxes]


#f = io.open('D:\\python\\job_rec\\recommender\\Screenshot (337).png',encoding='utf8')
# with open('D:\\python\\job_rec\\recommender\\ss.png','rb') as f:
#     print(img_resume(f))
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
st.set_page_config(page_title="Resume Parsing", page_icon="🤖", layout="wide")
st.title("📄 Resume Parsing")

st.sidebar.header("Upload Document")
uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF or DOCX file",
    type=["pdf", "docx"]
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_text" not in st.session_state:
    st.session_state.document_text = ""

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("🔍 Extracting text..."):
        if file_type == "pdf":
            text,image,word_bboxes = pdf_resume(uploaded_file)
        elif file_type == "docx":
            text,image, word_bboxes = docx_resume(uploaded_file)
        else:
            text = "Unsupported file type!"
            image = "Invalid"
            word_bboxes = 'NULL'
    st.session_state.document_text = text
    st.session_state.document_image = image
    st.session_state.bboxes = word_bboxes
    uploaded_file.seek(0)
    doc_results = process_document_for_layout_and_semantic(file_bytes=uploaded_file.read(), image_bytes_list=image)

    

# ---------- Show Extracted Results ----------

if st.session_state.document_text:
    
    # 1. Extracted Text Expander
    with st.expander("📜 Extracted Document Text"):
        st.text_area("Text Output", st.session_state.document_text, height=200)
    
    # 2. Bounding Box Data Expander
    if st.session_state.bboxes and st.session_state.bboxes != 'NULL':
        with st.expander("🔠 Word Bounding Box Coordinates"):
            st.write(f"Total words detected: {len(st.session_state.bboxes)}")
            # Use pandas dataframe for a clean, scrollable table in Streamlit
            st.dataframe(st.session_state.bboxes, use_container_width=True)

    # 3. Extracted Image (With Bounding Box Overlay) Expander
    if st.session_state.document_image and st.session_state.document_image != "Invalid":
        with st.expander("🖼️ Extracted Images"):
            
            # Add a checkbox to toggle bounding boxes
            show_boxes = st.checkbox("Overlay Word  Bounding Boxes (Red)")
            
            for page_idx, img_bytes in enumerate(st.session_state.document_image):
                # Open image from bytes
                img = Image.open(io.BytesIO(img_bytes))
                
                # Draw bounding boxes if checkbox is true and boxes exist
                if show_boxes and st.session_state.bboxes and st.session_state.bboxes != 'NULL':
                    draw = ImageDraw.Draw(img)
                    
                    # Filter boxes for the current page only
                    page_boxes = [b for b in st.session_state.bboxes if b["page"] == page_idx]
                    
                    for box_data in page_boxes:
                        # Draw rectangle using coordinates (x0, top, x1, bottom)
                        draw.rectangle(box_data["bbox"], outline="red", width=1)
                
                # Display the image in Streamlit
                st.image(img, use_container_width=True, caption=f"Page {page_idx + 1}")
                
                
# ---------- Chat Interface ----------
st.subheader("💬 Chat with Document")

user_input = st.text_input("Ask something about the document...", key="user_input")
if st.button("Send") and user_input.strip():
    user_msg = {"role": "user", "content": user_input}
    st.session_state.chat_history.append(user_msg)

    # Dummy bot response (replace with LangChain or API call)
    response = f"I received your question.\n(Soon, I’ll analyze your document for a real answer!)"
    bot_msg = {"role": "assistant", "content": response}
    st.session_state.chat_history.append(bot_msg)

# ---------- Display Chat ----------
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"🧑‍💻 **You:** {chat['content']}")
    else:
        st.markdown(f"🤖 **Bot:** {chat['content']}")