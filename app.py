from flask import Flask, render_template, request
import os
from resume_parser import pdf_resume, docx_resume
from vectorize import search_jobs

app = Flask(__name__)


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze', methods = ['POST'])
def analyse():
    uploaded_file = request.files["resume"]

    if uploaded_file.filename == "":
        return "No file selected"
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
    uploaded_file.save(file_path)
    ext = (uploaded_file.filename).split(".")[-1].lower()

    with open(file_path, 'rb') as f:
        if ext=='pdf':
          text, headings, sections, images, bboxes = pdf_resume(f)

        elif ext=='docx':
          text, headings, sections, images, bboxes = docx_resume(f)
        
        else:
           return "Unsupported file type!"
        
    matches = search_jobs(sections,text)

    return render_template(
       'job.html',
       jobs = matches,
       sections = sections
    )


if __name__=='__main__':
    app.run(debug = True)