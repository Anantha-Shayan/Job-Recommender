from sentence_transformers import SentenceTransformer
from endee import EndeeClient, Precision
import openai
import numpy as np
import pickle
import json
import re
import time
import os


model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

ENDEE_URL = os.getenv("ENDEE_URL", "http://endee:8080")
client = EndeeClient(ENDEE_URL)

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

    embeddings = get_model().encode(job_texts)

    dimension = embeddings.shape[1]

    # index = faiss.IndexFlatL2(dimension) # Eulidean dist
    try:
        client.create_index(
            name='job_index',
            dimension=dimension,
            space_type="cosine",
            precision=Precision.INT8
        )
    except:
        print("Index already exists")

    # Save index
    index = client.get_index('job_index')

    points = []
    for i, (job, vector) in enumerate(zip(jobs, embeddings)):
        points.append({
            "id": str(i),
            "vector": vector.tolist(),
            "meta": job
        })

    index.upsert(points)

    print(f"{len(jobs)} jobs stored in Endee successfully.")

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

    embedding = get_model().encode([combined_text])

    return embedding[0].tolist()


# Search Matching Jobs
def search_jobs(sections, resume_text, top_k=3):

    index = client.get_index('job_index')

    resume_exp = extract_years_of_experience(resume_text)
    
    query_embedding = embed_resume_query(sections)
    results_db = index.query(
        vector=query_embedding,
        top_k=top_k
    )

    # for _ in range(10):
    #     start = time.perf_counter()
    # distances, indices = index.search(np.array(query_embedding), top_k)
    #     end = time.perf_counter()
    #     times.append((end - start) * 1000)

    # avg_time = sum(times) / len(times)
    # print(f"Average FAISS Search Time: {avg_time:.3f} ms")

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

    res_skill_embed = get_model().encode(res_skills)

    results = []
    threshold = 0.33

    for i, item in enumerate(results_db):
        job = item["meta"]
        score = item["similarity"]

        # Experience filter
        if resume_exp < job.get("min_experience", 0):
            continue

        # Missing skill detection
        mis_skills = list(
            set(skill.lower() for skill in job.get("skills", [])) - set(res_skills)
        )

        final_missing = []

        if mis_skills:
            mis_skills_embed = get_model().encode(mis_skills)

            for skill, skill_emb in zip(mis_skills, mis_skills_embed):
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
                ),
                "explanation": "Your profile aligns well; detailed AI explanation is disabled for speed."
                })

    return results