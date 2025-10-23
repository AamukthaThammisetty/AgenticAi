# routes/people.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel
from app.services import fetch_linkedin  # import your function

router = APIRouter(prefix="/people", tags=["LinkedIn People"])

class Person(BaseModel):
    name: str
    occupation: str
    location: str
    link: str
    platform: str

@router.get("/search", response_model=List[Person])
async def search_people(
    keyword: str = Query(..., description="Keyword to search for"),
    location: str = Query(..., description="Location for the search")
):
    """
    Search LinkedIn people based on keyword and location.
    """
    try:
        results = fetch_linkedin(keyword, location)
        if not results:
            raise HTTPException(status_code=404, detail="No profiles found")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
