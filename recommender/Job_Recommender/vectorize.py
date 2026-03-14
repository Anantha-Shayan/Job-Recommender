from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

model = SentenceTransformer("all-MiniLM-L6-v2")

# Dummy Job Dataset
dummy_jobs = [
    {
        "title": "Machine Learning Engineer",
        "description": "Python NLP FastAPI Docker TensorFlow LangChain FAISS"
    },
    {
        "title": "Backend Developer",
        "description": "Node.js Express MongoDB REST APIs Docker Redis"
    },
    {
        "title": "Data Scientist",
        "description": "Python Pandas Scikit-learn Machine Learning Statistics SQL"
    },
    {
        "title": "Cloud Engineer",
        "description": "AWS Docker Kubernetes CI/CD Linux Terraform"
    },
    {
        "title": "AI Engineer",
        "description": "Transformers HuggingFace RAG LangChain Python NLP"
    }
]


# Store Jobs in FAISS
def build_job_vector_store():

    job_texts = [
        job["title"] + " " + job["description"]
        for job in dummy_jobs
    ]

    embeddings = model.encode(job_texts)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    # Save index
    faiss.write_index(index, "jobs_faiss.index")

    # Save metadata
    with open("jobs_metadata.pkl", "wb") as f:
        pickle.dump(dummy_jobs, f)

    print("Jobs stored in FAISS successfully.")


# Convert Resume Sections to Query Vector
def embed_resume_query(sections):

    combined_text = (
        "Skills: " + " ".join(sections.get("skills", [])) + "\n" +
        "Projects: " + " ".join(sections.get("projects", [])) + "\n" +
        "Experience: " + " ".join(sections.get("experience", []))
    )

    embedding = model.encode([combined_text])

    return embedding


# Search Matching Jobs
def search_jobs(sections, top_k=3):

    index = faiss.read_index("jobs_faiss.index")

    with open("jobs_metadata.pkl", "rb") as f:
        jobs = pickle.load(f)

    query_embedding = embed_resume_query(sections)

    distances, indices = index.search(np.array(query_embedding), top_k)

    results = []

    for idx in indices[0]:
        results.append(jobs[idx])

    return results