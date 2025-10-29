import os
import requests

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")

def fetch_github_candidates(parsed_jd: dict, max_users: int = 10):
    query = parsed_jd.get("github_query", "")
    if not query:
        raise ValueError("No query found in parsed JD output")

    headers = {
        "Accept": "application/vnd.github.text-match+json",
        "Authorization": f"Bearer {GITHUB_API_KEY}",
         "User-Agent": "AgenticAI-Scraper"
    }

    url = f"https://api.github.com/search/users?q={query}&per_page={max_users}"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    users = response.json().get("items", [])

    candidates = []
    for user in users:
        username = user["login"]
        user_profile = fetch_user_details(username, headers)
        candidates.append(user_profile)

    return candidates


def fetch_user_details(username: str, headers: dict):
    headers = {
        "Accept": "application/vnd.github.text-match+json",
        "Authorization": f"Bearer {GITHUB_API_KEY}",
        "User-Agent": "AgenticAI-Scraper"
    }
    user_url = f"{GITHUB_API_URL}/users/{username}"
    repos_url = f"{GITHUB_API_URL}/users/{username}/repos"
    readme_url = f"{GITHUB_API_URL}/repos/{username}/{username}/readme"

    # Fetch user info
    user_resp = requests.get(user_url, headers=headers)
    user_resp.raise_for_status()
    user_data = user_resp.json()

    # Fetch top repos
    repos_resp = requests.get(repos_url, headers=headers, params={"sort": "stars", "per_page": 5})
    repos_resp.raise_for_status()
    repos = repos_resp.json()

    top_repos = [
        {
            "name": repo["name"],
            "url": repo["html_url"],
            "stars": repo["stargazers_count"],
            "topics": repo.get("topics", []),
            "description": repo.get("description")
        }
        for repo in repos
    ]

    # Aggregate skills from repo topics
    skills = list({skill for repo in top_repos for skill in repo.get("topics", [])})

    # Fetch README content (if any)
    readme_content = None
    readme_resp = requests.get(readme_url, headers=headers)
    if readme_resp.status_code == 200:
        readme_data = readme_resp.json()
        if "content" in readme_data:
            import base64
            readme_content = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
    return {
        "username": username,
        "name": user_data.get("name"),
        "bio": user_data.get("bio"),
        "email" : user_data.get("email"),
        "github_url": user_data.get("html_url"),
        "avatar_url": user_data.get("avatar_url"),
        "followers": user_data.get("followers"),
        "public_repos": user_data.get("public_repos"),
        "top_repos": top_repos,
        "skills": skills,
        "profile_readme": readme_content
    }
