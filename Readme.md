# 🚀 AI-Powered Job Recommendation System

An intelligent job recommendation system that matches candidates to relevant job roles based on their resume using semantic similarity.

Powered by **ENDEE**.

---

## 📌 Overview

This extracts information from a candidate’s resume once uploaded, converts it into embeddings, and performs similarity search with stored job embeddings to recommend the most relevant jobs.

It also highlights **missing skills** and **AI powered improvements and suggestions**, helping users understand how to improve their profile.

---

## ⚙️ Features

- 📄 Resume parsing (Only PDF/DOCX. Image, scanned pdfs not supported for now )
- 🧠 Semantic similarity using sentence embeddings
- 📊 Match score for each job
- ❗ Missing skills identification
- 🤖 AI Powered suggestions
- 🌐 Clean frontend for job recommendations
- 🔁 Persistent job storage using `jobs.json`

---

## 🏗️ Tech Stack

### Backend
- Python
- Flask

### Machine Learning
- Sentence Transformers (`all-MiniLM-L6-v2`)
- NumPy

### Retrieval System
- Endee

### Frontend
- HTML + Tailwind CSS

---

## 📂 Project Structure

```text
recommendation_system/<br>
│<br>
├── app.py # Flask backend<br>
├── build_vector_store.py # Embedding & indexing logic<br>
├── jobs.json # Job dataset<br>
├── templates/<br> # Frontend
│ └── home.html
│ └── jobs.html
├── static/ # Static assets (if any)<br>
├── uploads/ # Uploaded resumes<br>
├── requirements.txt<br>
└── README.md<br>
```

---


## 🔄 How It Works

### 1. Resume Upload
- User uploads a resume (PDF/DOCX only. Images and scanned pdfs not supported yet)

### 2. Text Extraction
- Resume is parsed into raw text. Requiered sections (e.g., skills) are extracted.

### 3. Embedding Generation
- Extracted text and sections are converted into vector embeddings

### 4. Similarity Search
- Resume embeddings are compared with pre-stored job embeddings for top-k similarity.

### 5. Ranking
- Jobs are ranked based on match score

### 6. Skill Gap Analysis
- Missing skills are identified by comparing resume vs job requirements.<br>
  AI powered suggestions and improvements are provided.

---

## 🧠 Core Logic

- Uses **cosine similarity** between embeddings
- Jobs are pre-processed and stored in a structured format (`jobs.json`)
- Resume embedding is matched against job embeddings

---


---

# 🚀 Setup Guide: Running Recommendation System with endee vectordb

## 1. Prerequisites

- **Docker** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Python 3.8+** (for the recommendation system)
- **Git** (optional, for cloning the repo)

## 2. Clone the Repository

```bash
git clone https://github.com/<your-org-or-username>/endee.git
cd endee/recommendation_system
```

## 3. Prepare Data Directory for endee vectordb

### Linux / Mac

```bash
mkdir -p ../endee-data
chmod 777 ../endee-data
```

### Windows (PowerShell)

```powershell
mkdir ..\endee-data
# No chmod needed, but ensure your user has full access to this folder
```

## 4. Run endee vectordb with Docker

### Linux / Mac

```bash
docker build -f infra/Dockerfile \
  --build-arg BUILD_ARCH=avx2 \
  --build-arg DEBUG=false \
  -t endee:latest .
```

### Windows (PowerShell)

```powershell
mkdir -p /workspaces/endee/data
sudo chown 1000:1000 /workspaces/endee/data

docker rm -f endee 2>/dev/null || true
docker run -d --name endee \
  -p 8080:8080 \
  -v /workspaces/endee/data:/data \
  -e NDD_DATA_DIR=/data \
  -e NDD_SERVER_PORT=8080 \
  -e NDD_LOG_LEVEL=info \
  -e NDD_NUM_THREADS=0 \
  endee:latest
```
> If you get a permissions error, ensure Docker Desktop is allowed to access your drive and the `endee-data` folder.

## 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 6. Configure Your App to Use endee vectordb

- By default, the vectordb server runs at `http://localhost:8080`.
- Ensure your app connects to this endpoint.

## 7. Run the Recommendation System

```bash
python app.py
```

## 8. Stopping and Cleaning Up

To stop the vectordb server:

```bash
docker stop endee-server
```

To remove the container:

```bash
docker rm endee-server
```

---

## ⚠️ Current Limitations<br>
Skill extraction is rule-based (can be improved with NLP)<br>
Match scoring may not always align perfectly with human intuition<br>
No user authentication (yet)<br>
Limited dataset (depends on jobs.json)<br>

## 🔥 Future Improvements
✅ Better skill extraction using NLP / LLMs<br>
✅ Weighted scoring (skills > experience > keywords)<br>
✅ Real-time job scraping (LinkedIn, Indeed APIs)<br>
✅ Deploy using Docker + Cloud (AWS/GCP)<br>
✅ Expand Endee into a full retrieval engine<br>
✅ Add recruiter-side AI Hiring Copilot<br>
✅ Resume feedback & improvement suggestions<br>

💡 Use Cases<br>
Students preparing for placements<br>
Job seekers improving resumes<br>
Recruiters screening candidates<br>
Demonstration of ML + backend integration<br>

🧑‍💻 Author

Anantha Shayan
BTech CSE (AI & ML)
