from fastapi import File, UploadFile, HTTPException, APIRouter
from app.model import Job
import os
from app.db import jobs_collection 
from typing import List
from datetime import datetime
import uuid

router = APIRouter(prefix="/jobs", tags=["Jobs"])



@router.post("/create")
async def create_job(job: Job):
    job.job_id = str(uuid.uuid4())
    job.posted_at = datetime.now()
    job_dict = job.dict()
    result = await jobs_collection.insert_one(job_dict)
    job_dict["_id"] = str(result.inserted_id)
    return {"message": "Job created successfully", "job": job_dict}


@router.get("/", response_model=List[Job])
async def get_jobs():
    """Fetch all job postings from MongoDB"""
    jobs_cursor =  jobs_collection.find()
    jobs = await jobs_cursor.to_list(length=None)
    return jobs


@router.get("/{job_id}", response_model=Job)
def get_job_by_id(job_id: str):
    """Fetch a single job by its ID"""
    for job in jobs_collection:
        if job.job_id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")
