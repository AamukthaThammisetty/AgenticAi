from app.services import fetch_linkedin

import concurrent.futures
from functools import partial
from app.model import PeopleRequest

def scrape_all(job: PeopleRequest):
    print("Scrape_all called...")
    print("Scraping all people...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        linkedin_future = executor.submit(fetch_linkedin, job.keyword, job.location)
        
        linkedin_results = linkedin_future.result()

    linkedin_people = []
    if isinstance(linkedin_results, list):
        linkedin_people = linkedin_results
    elif isinstance(linkedin_results, dict):
        if "error" not in linkedin_results:
            linkedin_people = linkedin_results.get("people", [])

    
    all_people = linkedin_people 
    return all_people
