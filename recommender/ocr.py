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
import flask
import requests
from fastapi import FastAPI, HTTPException
import streamlit as st


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
    file_bytes = file.read()    # bytes of file will be stored (all img/pdf/docx are just sequence of bytes)
    result = ""
    images = []

    # Render images
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()

    # Extract text
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:    #io.BytesIO automatically allocates memory in-                                                             
        for page in pdf.pages:                              #RAM and sores the file there instead of in disk
            result += page.extract_text() or ""
            
    return [result, images]
    # global text
        # text = result
        
# image to text
def img_resume(file):
    #pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'
    #img = Image.open('D:\\python\\job_rec\\recommender\\resume.png')
    # print(pytesseract.image_to_string(img))
    img_bytes = file.read()
    reader = easyocr.Reader(['en'])
    result = reader.readtext(img_bytes, detail = 0)
    return [result,file]
    # global text
    # text = result
    
def docx_resume(file):
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir,file.name)
        file.seek(0)
        with open(docx_path,"wb") as f:    # wb = write binary (pdf/img/docx are just a sequence of bytes)
            f.write(file.read())
        # Convert DOCX to PDF
        pdf_path = os.path.join(tmpdir, "resume.pdf")
        docx2pdf.convert(docx_path, pdf_path)  # returns None
        # Open the PDF in binary mode and pass to pdf_resume
        with open(pdf_path, "rb") as pdf_file:
            text,image = pdf_resume(pdf_file)[0],pdf_resume(pdf_file)[1] 
            
    return [text,image]

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
    "Upload a PDF, DOCX, or Image file",
    type=["pdf", "docx", "png", "jpg", "jpeg"]
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_text" not in st.session_state:
    st.session_state.document_text = ""

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("🔍 Extracting text..."):
        if file_type == "pdf":
            text,image = pdf_resume(uploaded_file)
        elif file_type == "docx":
            text,image = docx_resume(uploaded_file)
        elif file_type in ["png", "jpg", "jpeg"]:
            text,image = img_resume(uploaded_file)
        else:
            text = "Unsupported file type!"
            image = "Invalid"
    st.session_state.document_text = text
    st.session_state.document_image = image
    

# ---------- Show extracted text ----------
if st.session_state.document_text:
    with st.expander("📜 Extracted Document Text"):
        st.text_area("", st.session_state.document_text, height=200)
            
    with st.expander("📜 Extracted Image"):
        images = []
        for img_bytes in st.session_state.document_image:
            img = Image.open(io.BytesIO(img_bytes))
            images.append(img)
            st.image(img, use_container_width=True)

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