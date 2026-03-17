from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import json
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

# Store Jobs in FAISS
def build_job_vector_store():

    with open("jobs.json", "r", encoding="utf-8") as f:
        dummy_jobs = json.load(f)

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

    print(f"{len(dummy_jobs)} jobs stored in FAISS successfully.")

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

        threshold = 0.33
        res_skills = [] # clean resume skills
        for line in sections.get("skills", []):
            parts = re.split(r'[,\|;/]', line)
            for part in parts:
                res_skills.append(part.strip().lower())

        
        mis_skills = list(set(skill.lower() for skill in job["skills"]) - set(res_skills)) #word matching

        res_skill_embed = model.encode(res_skills)
        mis_skills_embed = model.encode(mis_skills)
        faiss.normalize_L2(res_skill_embed)
        faiss.normalize_L2(mis_skills_embed)


        final_missing = []

        for skill, skill_emb in zip(mis_skills, mis_skills_embed):

            similarities = np.dot(res_skill_embed, mis_skills_embed.T)

            if np.max(similarities) < 0.82:
                final_missing.append(skill)
        
        #scoring
            



        if resume_exp >= job["min_experience"] and score > threshold:    
        # score > threshold because here if score is high, relevance is high. Unlike in Euclidean distance where distance would replace score and condition would be dist < threshold
           results.append({
                "title": job["title"],
                "company": job.get("company"),
                "location": job.get("location"),
                "description": job.get("description"),
                "url": job.get("url"),
                "skills": job["skills"],
                "missing_skills": final_missing,
                "required_experience": job["min_experience"],
                "similarity_score": float(score)
                })

    return results