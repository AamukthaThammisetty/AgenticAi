import httpx
import os
from typing import List, Dict
from fastapi import HTTPException

class GitHubService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = os.getenv("GITHUB_TOKEN")  # Optional but recommended
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    async def search_users(self, job: dict) -> List[Dict]:
        """
        Search GitHub users based on job requirements.
        Automatically limits the number of candidates using job['no_of_candidates'].
        """
        # Build search query from job requirements
        query_parts = []

        # Add required skills to search
        if job.get("required_skills"):
            for skill in job["required_skills"][:3]:  # Limit to top 3 skills
                query_parts.append(f"language:{skill}")

        # Add location if specified
        if job.get("location"):
            location = job["location"].split(",")[0].strip()
            query_parts.append(f"location:{location}")

        # Add follower filter for quality candidates
        query_parts.append("followers:>10")

        # Combine query
        query = " ".join(query_parts)

        # Determine how many candidates to fetch
        candidate_limit = int(job.get("no_of_candidates", 50))  # default to 50
        per_page = min(candidate_limit, 100)  # GitHub API limit per request

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/users",
                params={"q": query, "per_page": per_page},
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GitHub API error: {response.text}"
                )

            data = response.json()
            items = data.get("items", [])[:candidate_limit]  # hard stop at limit
            return items
    
    async def get_user_details(self, username: str) -> Dict:
        """Get detailed information about a GitHub user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{username}",
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {}
    
    async def get_user_repos(self, username: str, limit: int = 30) -> List[Dict]:
        """Get user's public repositories"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{username}/repos",
                params={"sort": "updated", "per_page": limit},
                headers=self.headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return []
