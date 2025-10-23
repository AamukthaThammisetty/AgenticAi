from typing import List
from app.models import LinkedInProfile

# In-memory storage
profiles_db: List[LinkedInProfile] = []

def save_profiles(profiles: List[LinkedInProfile]):
    profiles_db.extend(profiles)

def get_all_profiles() -> List[LinkedInProfile]:
    return profiles_db
