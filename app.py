from flask import Flask, render_template, request
import os
from resume_parser import pdf_resume, docx_resume
from vectorize import search_jobs
import time 

app = Flask(__name__)


UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/analyze', methods = ['POST'])
def analyse():
    total_start = time.perf_counter()
    uploaded_file = request.files["resume"]

    if uploaded_file.filename == "":
        return "No file selected"
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
    uploaded_file.save(file_path)
    ext = (uploaded_file.filename).split(".")[-1].lower()

    with open(file_path, 'rb') as f:
        extract_start = time.perf_counter()
        if ext=='pdf':
          text, headings, sections, images, bboxes = pdf_resume(f)

        elif ext=='docx':
          text, headings, sections, images, bboxes = docx_resume(f)
        
        else:
           return "Unsupported file type!"
        extract_end = time.perf_counter()
        
        
    match_start = time.perf_counter()
    matches = search_jobs(sections,text)
    match_end = time.perf_counter()

    render_start = time.perf_counter()
    response = render_template(
       'job.html',
       jobs = matches,
       sections = sections
       )
    
    render_end = time.perf_counter()
    total_end = time.perf_counter()

    #latency check
    print(f"Resume parsing time: {(extract_end-extract_start)*1000:.3f} ms")
    print(f"Search stage time: {(match_end-match_start)*1000:.3f} ms")
    print(f"Render time: {(render_end-render_start)*1000:.3f} ms")
    print(f"Full pipeline time: {(total_end-total_start)*1000:.3f} ms")

    return response



if __name__=='__main__':
    app.run(debug = True)