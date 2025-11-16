# README – AgenticAI Talent Finder

## Project Overview
AgenticAI Talent Finder is an AI-powered recruitment automation system that parses job descriptions, retrieves relevant GitHub profiles, evaluates candidates using multi-agent reasoning, and ranks them based on relevance.  
The system integrates CrewAI, Gemini LLM, FastAPI, MongoDB, and Next.js to streamline and automate the hiring workflow.

---

# How to Run the Project

## 1. Clone the Repository
```bash
git clone <your-repository-link>
cd agentic-ai-talent-finder
Backend Setup (FastAPI + Python)
2. Create a Virtual Environment
bash
Copy code
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
3. Install Backend Dependencies
bash
Copy code
pip install -r requirements.txt
4. Add API Keys
Create a .env file inside the backend folder:

ini
Copy code
GEMINI_API_KEY=your_key
GITHUB_API_KEY=your_key
MONGO_URL=your_mongodb_url
5. Start the FastAPI Server
bash
Copy code
uvicorn main:app --reload
Backend runs at:
http://127.0.0.1:8000

Frontend Setup (Next.js)
6. Navigate to Frontend
bash
Copy code
cd frontend
7. Install Node Modules
bash
Copy code
npm install
8. Run Frontend
bash
Copy code
npm run dev
Frontend runs at:
http://localhost:3000

Workflow / Execution Process
Recruiter enters or uploads a job description in the Next.js dashboard.

Backend (FastAPI) sends the job description to CrewAI and Gemini.

JD Parser Agent extracts:

required skills

experience levels

tech stack

keywords

Candidate Ranking Agent fetches GitHub profiles and analyzes:

repositories

programming languages

activity and contributions

AI assigns a relevance score and ranks candidates.

Ranked candidate list is shown in the UI with GitHub and LinkedIn links.

Project Structure
bash
Copy code
/backend
    main.py
    agents/
    services/
    models/
    requirements.txt

/frontend
    pages/
    components/
    utils/
    package.json

README.md
Dependencies
Backend
FastAPI

CrewAI

Gemini API

LangChain

Pandas

NumPy

Scikit-learn

Pydantic

MongoDB (pymongo)

Frontend
Next.js

React

Tailwind CSS

Axios

API Testing Guide
1. Parse Job Description
bash
Copy code
POST /parse-jd
{
  "job_description": "Looking for Python developer..."
}
2. Fetch GitHub Candidates
sql
Copy code
GET /fetch-candidates?skills=python,react
3. Rank Candidates
bash
Copy code
POST /rank-candidates
Usage Instructions
Open the web dashboard.

Enter or upload a job description.

Click “Fetch Candidates” to retrieve GitHub profiles.

Click “Rank Candidates” to start AI-based analysis.

View ranked candidates along with:

score

explanation

GitHub link

LinkedIn link
