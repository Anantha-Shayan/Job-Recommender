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
        jobs = json.load(f)

    for job in jobs:
        job["min_experience"] = extract_min_experience(job.get("experience", "0"))

    job_texts = [
        f"""
        Title: {job['title']}
        Skills: {', '.join(job.get('skills', []))}
        Description: {job.get('description', '')}
        Company: {job.get('company', '')}
        """
        for job in jobs
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
        pickle.dump(jobs, f)

    print(f"{len(jobs)} jobs stored in FAISS successfully.")

# Extract years of experience from reusme
def extract_years_of_experience(text):

    match = re.search(r'(\d+)\+?\s*years?', text.lower())

    if match:
        return int(match.group(1))

    return 0

def extract_min_experience(exp_text):
    if not exp_text:
        return 0
    match = re.search(r"\d+", exp_text)
    if match:
        return int(match.group())
    return 0
    

# Convert Resume Sections to Query Vector
def embed_resume_query(sections):

    combined_text = f"""
    Skills: {', '.join(sections.get('skills', []))}
    Projects: {sections.get('projects', '')}
    """

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

    res_skills = [] # clean resume skills
    for line in sections.get("skills", []):
        parts = re.split(r'[,\|;/()]', line)
        for part in parts:
            cleaned = part.strip().lower()
            if cleaned:
                res_skills.append(cleaned)


        
        res_skills = list(set(res_skills))

    if len(res_skills) == 0:
        return []

    res_skill_embed = model.encode(res_skills)
    faiss.normalize_L2(res_skill_embed)

    threshold = 0.33

    for score, idx in zip(distances[0], indices[0]):

        job = jobs[idx]

        # Experience filter
        if resume_exp < job.get("min_experience", 0):
            continue

        # Missing skill detection
        mis_skills = list(
            set(skill.lower() for skill in job.get("skills", [])) - set(res_skills)
        )

        final_missing = []

        if mis_skills:
            mis_skills_embed = model.encode(mis_skills)
            faiss.normalize_L2(mis_skills_embed)

            resume_text_joined = " ".join(res_skills)
            for skill, skill_emb in zip(mis_skills, mis_skills_embed):
                if any(word in resume_text_joined for word in skill.split()):
                    continue

                similarities = np.dot(res_skill_embed, skill_emb)

                if np.max(similarities) < 0.82:
                    final_missing.append(skill)

        # Skill overlap score
        overlap = len(set(res_skills) & set(skill.lower() for skill in job.get("skills", [])))
        skill_score = overlap / max(len(job.get("skills", [])), 1)

        # Final weighted score
        final_score = (0.6 * float(score)) + (0.4 * skill_score)

        if final_score > threshold:    
        # score > threshold because here if score is high, relevance is high. Unlike in Euclidean distance where distance would replace score and condition would be dist < threshold
           results.append({
                "title": job["title"],
                "company": job.get("company",[]),
                "location": job.get("location",[]),
                "description": job.get("description"),
                "url": job.get("url"),
                "skills": job["skills"],
                "missing_skills": final_missing,
                "required_experience": job.get("min_experience", 0),
                "similarity_score": round(final_score * 100, 2),
                "match_label": (
                    "Strong Match" if final_score > 0.65
                    else "Good Match" if final_score > 0.45
                    else "Moderate Match"
                )
                })

    return results