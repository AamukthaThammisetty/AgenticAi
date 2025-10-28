import os
import httpx
import json
from fastapi import HTTPException
from dotenv import load_dotenv
from datetime import datetime
from bson import ObjectId

load_dotenv()

def serialize_mongo_doc(doc):
    """Convert ObjectId and datetime fields to serializable strings."""
    if not isinstance(doc, dict):
        return doc
    
    serialized = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            serialized[k] = str(v)
        elif isinstance(v, datetime):
            serialized[k] = v.isoformat()
        elif isinstance(v, dict):
            serialized[k] = serialize_mongo_doc(v)
        elif isinstance(v, list):
            serialized[k] = [serialize_mongo_doc(item) if isinstance(item, dict) else item for item in v]
        else:
            serialized[k] = v
    return serialized


class GeminiScoringService:
    def __init__(self):
        self.gemini_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        )
        self.api_key = os.getenv("GOOGLE_API_KEY")

    async def score_candidates(self, job: dict, candidates: list):
        """
        Use Gemini to evaluate and rank candidates based on their GitHub repositories and profile data.
        
        Args:
            job: Job details dictionary
            candidates: List of candidate dictionaries (not a single candidate)
        
        Returns:
            List of scored candidates
        """
        
        # FIX: Ensure we're working with a list
        if not isinstance(candidates, list):
            raise ValueError("candidates must be a list")

        # Clean up MongoDB docs before sending to Gemini
        cleaned_candidates = [serialize_mongo_doc(c) for c in candidates]
        cleaned_job = serialize_mongo_doc(job)

        prompt = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "You are an AI technical recruiter.\n"
                                "Analyze the given JOB DETAILS and CANDIDATES DATA (including GitHub repositories).\n"
                                "Infer their hands-on experience, evaluate how well their GitHub skills match the job, "
                                "and summarize why each should be hired.\n\n"
                                "Provide ONLY a JSON array with the following structure (no explanations or extra text):\n"
                                "[\n"
                                "  {\n"
                                "    \"name\": string,\n"
                                "    \"github_url\": string,\n"
                                "    \"linkedin_url\": string or null,\n"
                                "    \"hands_on_experience\": string,\n"
                                "    \"skill_matching_score\": number (0-100),\n"
                                "    \"matched_skills\": [string],\n"
                                "    \"summary\": string (why this candidate fits the role)\n"
                                "  }\n"
                                "]\n\n"
                                "Rank the candidates by best match first.\n\n"
                               f"JOB DETAILS:\n{json.dumps(cleaned_job, indent=2)}\n\n"
                               f"CANDIDATES DATA:\n{json.dumps(cleaned_candidates, indent=2)}"
                            )
                        }
                    ],
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gemini_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=prompt,
                timeout=90.0,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Gemini API error: {response.text}",
            )

        data = response.json()
        raw_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        # Clean Gemini response (remove code block formatting)
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        # Try to extract structured JSON
        try:
            structured_output = json.loads(raw_text)
            
            # Ensure it's a list
            if not isinstance(structured_output, list):
                raise ValueError("Gemini response is not a list")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Gemini returned invalid JSON: {e}")
            print(f"Raw response: {raw_text[:500]}")
            # Return fallback for all candidates
            return [
                {
                    "name": c.get("name", c.get("login", "Unknown")),
                    "github_url": c.get("html_url", ""),
                    "linkedin_url": None,
                    "hands_on_experience": "Not assessed",
                    "skill_matching_score": 0,
                    "matched_skills": [],
                    "summary": "Scoring unavailable - JSON parse error"
                }
                for c in candidates
            ]

        # Normalize and rank
        normalized = []
        for c in structured_output:
            if isinstance(c, dict):
                # Ensure github_url is a valid string
                github_url = c.get("github_url")
                if not github_url or not isinstance(github_url, str):
                    # Try to find it from the original candidates
                    name = c.get("name", "")
                    for candidate in candidates:
                        if candidate.get("name") == name or candidate.get("login") == name:
                            github_url = candidate.get("html_url", "")
                            break
                
                normalized.append({
                    "name": c.get("name", "Unknown"),
                    "github_url": github_url or "",
                    "linkedin_url": c.get("linkedin_url"),
                    "hands_on_experience": c.get("hands_on_experience", "Not specified"),
                    "skill_matching_score": int(c.get("skill_matching_score", 0)),
                    "matched_skills": c.get("matched_skills", []) if isinstance(c.get("matched_skills"), list) else [],
                    "summary": c.get("summary", "No summary provided.")
                })

        # Sort candidates by skill score (descending)
        ranked = sorted(normalized, key=lambda x: x.get("skill_matching_score", 0), reverse=True)

        # Ensure we always return a valid list
        if not ranked:
            print("⚠️ No candidates were normalized, returning fallback")
            return [
                {
                    "name": c.get("name", c.get("login", "Unknown")),
                    "github_url": c.get("html_url", ""),
                    "linkedin_url": None,
                    "hands_on_experience": "Not assessed",
                    "skill_matching_score": 0,
                    "matched_skills": [],
                    "summary": "Normalization failed"
                }
                for c in candidates
            ]

        return ranked
