from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional
from fastapi.responses import StreamingResponse

from src.agent import parse_jd, rank_candidates_stream
from src.services.github_scraper import fetch_github_candidates
import src.utils.json_parser as jp
from src.db.mongo import jd_collection

router = APIRouter()

class JDRequest(BaseModel):
    job_title : str
    job_description: str

class ParsedJDResponse(BaseModel):
    job_id: str
    message: str

class CandidateSearchRequest(BaseModel):
    job_id: str
    max_users: int = 10

class CandidateRankRequest(BaseModel):
    job_id: str

class JDListResponse(BaseModel):
    job_id: str
    job_title: Optional[str]
    candidates_fetched: bool
    candidate_count: Optional[int] = 0
    candidates_ranked: bool

def serialize_id(obj):
    obj["_id"] = str(obj["_id"])
    return obj

@router.post("/parse-jd", response_model=ParsedJDResponse)
async def parse_job_description(request: JDRequest):
    try:
        result = parse_jd(request.job_description)
        parsed_output = jp.parse(result)

        job_title = request.job_title

        doc = {
            "original_jd": request.job_description,
            "parsed_jd": parsed_output,
            "job_title": job_title,
            "candidates_fetched": False,
            "candidates_ranked" : False
        }

        inserted = jd_collection.insert_one(doc)

        return {
            "job_id": str(inserted.inserted_id),
            "message": f"Job description parsed successfully for '{job_title}'"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD Parsing Failed: {str(e)}")

@router.post("/search-candidates")
async def search_github_candidates(request: CandidateSearchRequest):

    try:
        jd_data = jd_collection.find_one({"_id": ObjectId(request.job_id)})
        if not jd_data:
            raise HTTPException(status_code=404, detail="JD not found in database")

        if jd_data.get("candidates_fetched", False) and "candidates" in jd_data:
            return {
                "job_id": request.job_id,
                "count": len(jd_data["candidates"]),
                "candidates": jd_data["candidates"],
                "message": "Returning already fetched candidates from database"
            }

        parsed_output = jd_data.get("parsed_jd", {})
        if not parsed_output:
            raise HTTPException(status_code=400, detail="Parsed JD missing in database")

        candidates = fetch_github_candidates(parsed_output, max_users=request.max_users)

        update_result = jd_collection.update_one(
            {"_id": ObjectId(request.job_id)},
            {
                "$set": {
                    "candidates": candidates,
                    "candidates_fetched": True
                }
            }
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update JD with candidates")

        return {
            "job_id": request.job_id,
            "count": len(candidates),
            "candidates": candidates,
            "message": "Candidates fetched and stored successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub Search Failed: {str(e)}")

@router.get("/list", response_model=List[JDListResponse])
async def list_all_jds():
    try:
        all_jds = jd_collection.find({})
        jd_list = []
        for jd in all_jds:
            jd_list.append({
                "job_id": str(jd["_id"]),
                "job_title": jd.get("job_title", "Unknown"),
                "candidates_fetched": jd.get("candidates_fetched", False),
                "candidate_count": len(jd.get("candidates", [])) if jd.get("candidates") else 0,
                "candidates_ranked": jd.get("candidates_ranked", False),
            })
        return jd_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch JD list: {str(e)}")

@router.post("/rank-candidates")
async def rank_candidates_for_jd(request: CandidateRankRequest):
    try:
        jd_data = jd_collection.find_one({"_id": ObjectId(request.job_id)})
        if not jd_data:
            raise HTTPException(status_code=404, detail="JD not found in database")

        if jd_data.get("candidates_ranked"):
            return {
                "status": "SUCCESS",
                "message": "Candidates have already been ranked. Returning existing results.",
                "ranked_candidates": jd_data.get("ranked_candidates", []),
                "summary": jd_data.get("ranking_summary", ""),
                "total_ranked": len(jd_data.get("ranked_candidates", []))
            }

        # 3️⃣ Extract JD and candidate data
        parsed_jd = jd_data.get("parse_jd", {})
        candidates = jd_data.get("candidates", [])
        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates found in JD document")

        # 4️⃣ Run ranking
        final_data = await rank_candidates_stream(parsed_jd, candidates)
        ranked = final_data.get("ranked_candidates", [])
        summary = final_data.get("summary", "")

        # 5️⃣ Update DB with ranking results
        jd_collection.update_one(
            {"_id": ObjectId(request.job_id)},
            {
                "$set": {
                    "ranked_candidates": ranked,
                    "ranking_summary": summary,
                    "candidates_ranked": True
                }
            }
        )

        return {
            "status": "SUCCESS",
            "message": "Candidates ranked successfully",
            "ranked_candidates": ranked,
            "summary": summary,
            "total_ranked": len(ranked)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")

@router.get("/get-job/{job_id}")
async def get_job(job_id: str):
    jd_data = jd_collection.find_one({"_id": ObjectId(job_id)})
    if not jd_data:
        raise HTTPException(status_code=404, detail="JD not found in database")

    return {
        "status": "SUCCESS",
        "message": "Returning existing results.",
        "ranked_candidates": jd_data.get("ranked_candidates", []),
        "candidates_fetched": jd_data.get("candidates_fetched", False),
        "candidates": jd_data.get("candidates", []),
        "candidate_count": len(jd_data.get("candidates", [])) if jd_data.get("candidates") else 0,
        "candidates_ranked": jd_data.get("candidates_ranked", False),
        "summary": jd_data.get("ranking_summary", ""),
    }
