from resume_parser import pdf_resume
from vectorize import build_job_vector_store, search_jobs

# Step 1: Build vector DB once
build_job_vector_store()

# Step 2: Parse resume
with open("D:\\python\\job_rec\\sshu_res.pdf", "rb") as f:
    text, headings, sections, images, bboxes = pdf_resume(f)

# Step 3: Search jobs
matches = search_jobs(sections)

print("\nTop Matching Jobs:\n")

for job in matches:
    print(job)