from fastapi import APIRouter, HTTPException
from datetime import datetime
from dotenv import load_dotenv
import os
import httpx

from app.db import candidates_collection, jobs_collection  # your existing db setup

load_dotenv()

router = APIRouter(prefix="/linkedin", tags=["LinkedIn Ranking"])

# Load environment variables
SCRAPE_URL = os.getenv("SCRAPE_URL")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
RAPID_API_HOST = os.getenv("RAPID_API_HOST")

# ✅ Predefined LinkedIn URLs for testing
LINKEDIN_PROFILES = [
    "https://www.linkedin.com/in/sundar-pichai/",
    "https://www.linkedin.com/in/satyanadella/",
    "https://www.linkedin.com/in/arvindkrishnaibm/",
    "https://www.linkedin.com/in/shantanu-narayen/",
    "https://www.linkedin.com/in/parag-agrawal/"
]


def score_candidate(profile: dict, job: dict) -> float:
    """Simple scoring logic based on keyword match between job and LinkedIn data."""
    text = (
        (profile.get("headline", "") or "") + " " +
        (profile.get("about", "") or "") + " " +
        " ".join(profile.get("skills", []) or [])
    ).lower()

    job_keywords = (
        job.get("job_title", "").lower() + " " +
        job.get("job_desc", "").lower()
    ).split()

    score = sum(1 for word in job_keywords if word in text)
    return round(score / len(job_keywords) * 100 if job_keywords else 0, 2)


@router.post("/scrape_and_rank/{job_id}")
async def scrape_and_rank(job_id: str):
    """Scrape predefined LinkedIn profiles, score and rank them according to job post."""

    # 1️⃣ Fetch job details
    job = await jobs_collection.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found in database")

    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": RAPID_API_HOST,
    }

    ranked_candidates = []

    async with httpx.AsyncClient(timeout=40.0) as client:
        for url in LINKEDIN_PROFILES:
            try:
                params = {"linkedin_url": url}
                response = await client.get(SCRAPE_URL, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"⚠️ Failed to fetch {url}: {e}")
                continue

            # Some APIs return `data` inside another dict
            profile_data = data.get("data") if isinstance(data, dict) else data
            if not profile_data:
                continue

            score = score_candidate(profile_data, job)

            candidate = {
                "job_id": job_id,
                "name": profile_data.get("name", "Unknown"),
                "headline": profile_data.get("headline", ""),
                "location": profile_data.get("location", ""),
                "about": profile_data.get("about", ""),
                "skills": profile_data.get("skills", []),
                "linkedin_url": url,
                "avatar_url": profile_data.get("profile_pic_url", ""),
                "score": score,
                "searched_at": datetime.now(),
            }

            ranked_candidates.append(candidate)

    # 2️⃣ Rank by score (descending)
    ranked_candidates.sort(key=lambda x: x["score"], reverse=True)

    # 3️⃣ Store in MongoDB
    if ranked_candidates:
        await candidates_collection.insert_many(ranked_candidates)

    # 4️⃣ Limit to required number of candidates
    top_n = job.get("no_of_candidates", len(ranked_candidates))
    top_ranked = ranked_candidates[:top_n]

    return {
        "job_id": job_id,
        "top_candidates": top_ranked,
        "count": len(top_ranked)
    }
