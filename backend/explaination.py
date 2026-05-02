import google.genai as genai
import os


def generate_explanation(resume_text, job, index):

    if index >= 2:
        return "Explanation skipped to save cost."
    
    prompt = f"""
    You are an AI career assistant.

    Resume:
    {resume_text}

    Job Title: {job['title']}
    Skills Required: {job['skills']}
    Description: {job['description']}

    Provide:
    1. Key missing skills
    2. How to improve profile
    """
    
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    response = client.models.generate_content(
    model="gemini-2.0-flash-exp", contents = prompt
    )

    return response.text