# app/routes/jobs.py
from fastapi import APIRouter
from app.services import search_linkedin_profiles

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])

@router.get("/profiles")
def get_profiles(job_title: str, location: str = None):
    results = search_linkedin_profiles(job_title, location)
    return {"count": len(results), "profiles": results}
