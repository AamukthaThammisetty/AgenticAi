from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List
from bson import ObjectId
import asyncio
import logging

from app.model import Candidate
from app.db import jobs_collection, candidates_collection
from app.services.github_service import GitHubService
from app.services.scoring_service import GeminiScoringService

router = APIRouter(prefix="/github", tags=["GitHub"])
logger = logging.getLogger(__name__)

github_service = GitHubService()
scoring_service = GeminiScoringService()


def normalize_job_id(job_id: str):
    """Convert job_id to ObjectId if it's a valid ObjectId string"""
    try:
        return ObjectId(job_id)
    except:
        return job_id


@router.get("/{job_id}/candidates")
async def get_or_search_candidates(job_id: str, limit: int = 50):
    """
    Fetch ranked candidates for a job.
    If no candidates exist, automatically search and add new ones.
    """

    # 1️⃣ Find job with proper ID handling
    normalized_id = normalize_job_id(job_id)
    job = await jobs_collection.find_one(
        {"$or": [{"_id": normalized_id}, {"job_id": job_id}]}
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Use string version of job_id for consistency
    job_id_str = str(job.get("job_id", job["_id"]))
    candidate_limit = int(job.get("no_of_candidates", limit))

    # 2️⃣ Check for existing candidates
    existing_candidates = await candidates_collection.find(
        {"job_id": job_id_str}
    ).sort("score", -1).to_list(length=candidate_limit)

    if existing_candidates:
        for c in existing_candidates:
            c["_id"] = str(c["_id"])
        return {
            "job_id": job_id_str,
            "source": "cached",
            "total_candidates": len(existing_candidates),
            "candidates": existing_candidates,
        }

    # 3️⃣ Search GitHub for candidates
    try:
        github_users = await github_service.search_users(job)
    except Exception as e:
        logger.error(f"GitHub search failed for job {job_id_str}: {e}")
        raise HTTPException(status_code=500, detail="Failed to search GitHub users")

    if not github_users:
        return {
            "job_id": job_id_str,
            "source": "fresh",
            "total_candidates": 0,
            "candidates": [],
            "message": "No candidates found matching criteria"
        }

    # 4️⃣ Fetch user details in parallel (batch processing)
    user_data_tasks = [
        fetch_user_data(user.get("login"))
        for user in github_users
    ]
    user_data_list = await asyncio.gather(*user_data_tasks, return_exceptions=True)

    # Filter out failed requests
    valid_users = [
        user for user in user_data_list 
        if user and not isinstance(user, Exception)
    ]

    if not valid_users:
        logger.warning(f"No valid user data fetched for job {job_id_str}")
        return {
            "job_id": job_id_str,
            "source": "fresh",
            "total_candidates": 0,
            "candidates": [],
            "message": "Failed to fetch user details from GitHub"
        }

    # 5️⃣ Score all candidates in a single Gemini call (batch scoring)
    try:
        # Create a clean copy of job for serialization
        job_data = {k: str(v) if isinstance(v, (ObjectId, datetime)) else v for k, v in job.items()}
        
        # FIX: Pass the entire list, not individual candidates
        logger.info(f"Scoring {len(valid_users)} candidates for job {job_id_str}")
        scored_candidates = await scoring_service.score_candidates(job_data, valid_users)
        logger.info(f"Received {len(scored_candidates)} scored candidates")
    except Exception as e:
        logger.error(f"Gemini scoring failed for job {job_id_str}: {e}", exc_info=True)
        # Fallback: create candidates with default scores
        scored_candidates = [
            {
                "name": user.get("name", user.get("login")),
                "github_url": user.get("html_url"),
                "linkedin_url": None,
                "hands_on_experience": "Not assessed",
                "skill_matching_score": 0,
                "matched_skills": [],
                "summary": "Scoring unavailable"
            }
            for user in valid_users
        ]

    # 6️⃣ Match scored data with user details and save to DB
    candidates = []
    username_to_score = {}
    for score in scored_candidates:
        github_url = score.get("github_url") or ""
        if github_url and isinstance(github_url, str):
            username = github_url.rstrip("/").split("/")[-1]
            if username:
                username_to_score[username] = score

    for user_details in valid_users:
        username = user_details.get("login")
        score_data = username_to_score.get(username, {})
        
        # If no score data found, create default
        if not score_data:
            score_data = {
                "matched_skills": [],
                "skill_matching_score": 0,
                "hands_on_experience": "Not assessed",
                "summary": "No scoring data available"
            }

        candidate_data = {
            "job_id": job_id_str,
            "github_username": username,
            "name": user_details.get("name", username),
            "email": user_details.get("email"),
            "location": user_details.get("location"),
            "bio": user_details.get("bio"),
            "company": user_details.get("company"),
            "blog": user_details.get("blog"),
            "github_url": user_details.get("html_url"),
            "avatar_url": user_details.get("avatar_url"),
            "public_repos": user_details.get("public_repos", 0),
            "followers": user_details.get("followers", 0),
            "following": user_details.get("following", 0),
            "skills": score_data.get("matched_skills", []),
            "score": score_data.get("skill_matching_score", 0),
            "hands_on_experience": score_data.get("hands_on_experience", "Not specified"),
            "summary": score_data.get("summary", "No summary provided."),
            "searched_at": datetime.now(),
        }

        candidates.append(candidate_data)

    # 7️⃣ Bulk insert to MongoDB (FIX: Correct format)
    if candidates:
        try:
            from pymongo import UpdateOne
            
            operations = [
                UpdateOne(
                    filter={"job_id": job_id_str, "github_username": c["github_username"]},
                    update={"$set": c},
                    upsert=True
                )
                for c in candidates
            ]
            await candidates_collection.bulk_write(operations)
        except Exception as e:
            logger.error(f"Failed to save candidates to DB: {e}")
            # Continue anyway - we can still return the results

    # 8️⃣ Sort and return
    sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    return {
        "job_id": job_id_str,
        "source": "fresh",
        "total_candidates": len(sorted_candidates),
        "candidates": sorted_candidates,
    }


async def fetch_user_data(username: str):
    """
    Fetch user details and repositories in parallel.
    Returns combined user data or None on failure.
    """
    try:
        # Fetch details and repos concurrently
        user_details, repos = await asyncio.gather(
            github_service.get_user_details(username),
            github_service.get_user_repos(username),
            return_exceptions=False
        )
        
        # Add repos to user details for Gemini analysis
        user_details["repositories"] = repos
        return user_details
        
    except Exception as e:
        logger.warning(f"Failed to fetch data for user {username}: {e}")
        return None
