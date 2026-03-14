from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

# Dummy Job Dataset
dummy_jobs = [
    {
        "title": "Machine Learning Engineer",
        "skills": ["Python", "NLP", "FastAPI", "Docker", "TensorFlow", "LangChain", "FAISS"],
        "min_experience" : 0
    },
    {
        "title": "Backend Developer",
        "skills": ["Node.js", "Express", "MongoDB", "REST APIs", "Docker", "Redis"],
        "min_experience" : 0
    },
    {
        "title": "Data Scientist",
        "skills": ["Python", "Pandas", "Scikit-learn", "Machine Learning", "Statistics", "SQL"],
        "min_experience" : 0
    },
    {
        "title": "Cloud Engineer",
        "skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Linux", "Terraform"],
        "min_experience" : 0
    },
    {
        "title": "AI Engineer",
        "skills": ["Transformers", "HuggingFace", "RAG", "LangChain", "Python", "NLP"],
        "min_experience" : 0
    }
]


# Store Jobs in FAISS
def build_job_vector_store():

    job_texts = [
        job["title"] + " Skills: " + " ".join(job["skills"])
        for job in dummy_jobs
    ]

    embeddings = model.encode(job_texts)

    dimension = embeddings.shape[1]

    # index = faiss.IndexFlatL2(dimension) # Eulidean dist
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dimension) #dot product 
    index.add(np.array(embeddings))

    # Save index
    faiss.write_index(index, "jobs_faiss.index")

    # Save metadata
    with open("jobs_metadata.pkl", "wb") as f:
        pickle.dump(dummy_jobs, f)

    print("Jobs stored in FAISS successfully.")

# Extract years of experience from reusme
def extract_years_of_experience(text):

    match = re.search(r'(\d+)\+?\s*years?', text.lower())

    if match:
        return int(match.group(1))

    return 0

# Convert Resume Sections to Query Vector
def embed_resume_query(sections):

    combined_text = (
        "Skills: " + " ".join(sections.get("skills", []))
    )

    embedding = model.encode([combined_text])

    return embedding


# Search Matching Jobs
def search_jobs(sections, resume_text, top_k=3):

    index = faiss.read_index("jobs_faiss.index")

    with open("jobs_metadata.pkl", "rb") as f:
        jobs = pickle.load(f)

    resume_exp = extract_years_of_experience(resume_text)
    
    query_embedding = embed_resume_query(sections)
    faiss.normalize_L2(query_embedding)

    distances, indices = index.search(np.array(query_embedding), top_k)

    results = []

    for score, idx in zip(distances[0],indices[0]):
        job = jobs[idx]

        # experience filtering
        if resume_exp >= job["min_experience"]:
           results.append({
                "title": job["title"],
                "skills": job["skills"],
                "required_experience": job["min_experience"],
                "similarity_score": float(score)
                })

    return results