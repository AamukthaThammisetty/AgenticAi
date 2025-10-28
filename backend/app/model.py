# app/model.py
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Union
from datetime import datetime


class CandidateScore(BaseModel):
    skills_match: float
    repository_quality: float
    activity_level: float
    community_engagement: float
    profile_completeness: float

class Candidate(BaseModel):
    job_id: str
    github_username: str
    name: str
    email: Optional[str]
    location: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    github_url: str
    avatar_url: str
    public_repos: int
    followers: int
    skills: List[str]
    score: float
    score_breakdown: dict
    top_repositories: List[dict]
    searched_at: datetime



class Job(BaseModel):
    job_id: Optional[str] = None
    job_title: str
    job_description: str
    salary: str
    no_of_candidates:int
    location: str
    skills_required: List[str]
    experience_required: Optional[str] = None
    employment_type: Optional[str] = "Full-time"
    company_name: Optional[str] = "Unknown"
    posted_at: Optional[datetime] = datetime.now()


class ResumeDetails(BaseModel):
    """Pydantic model for resume details extracted from PDF"""
    full_name: str = Field(default="", description="Full name of the candidate")
    skills: List[str] = Field(default_factory=list, description="List of technical skills")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(default=None, description="GitHub profile URL")
    
    @validator('skills', pre=True)
    def ensure_list(cls, v):
        """Ensure skills is always a list"""
        if v is None:
            return []
        if isinstance(v, str):
            # If a single string is provided, wrap it in a list
            return [v] if v else []
        return v
    
    @validator('full_name', pre=True)
    def ensure_string(cls, v):
        """Ensure string fields are always strings, not None"""
        if v is None:
            return ""
        return str(v)
    
    @validator('linkedin_url', 'github_url', pre=True)
    def validate_url(cls, v):
        """Allow empty strings or None for URLs"""
        if v is None or v == "":
            return None
        # Basic URL validation - just check if it starts with http
        if not str(v).startswith(('http://', 'https://')):
            return None
        return str(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "skills": ["Python", "FastAPI", "Machine Learning"],
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "github_url": "https://github.com/johndoe"
            }
        }
