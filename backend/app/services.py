# app/services.py
from serpapi import GoogleSearch
import os

def search_linkedin_profiles(job_title: str, location: str = None):
    query = f"site:linkedin.com/in {job_title}"
    if location:
        query += f" {location}"

    params = {
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),  # Store this in .env
        "num": 10
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    linkedin_profiles = []
    for res in results.get("organic_results", []):
        link = res.get("link")
        if "linkedin.com/in" in link:
            linkedin_profiles.append(link)

    return linkedin_profiles
