import json
import yaml
import os
from crewai import Agent, Task, Crew, Process, LLM
from src.services.github_scraper import fetch_github_candidates
import src.utils.json_parser as jp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_yaml(relative_path):
    abs_path = os.path.join(BASE_DIR, relative_path)
    with open(abs_path, "r") as f:
        return yaml.safe_load(f)

llm = LLM(
    model="gemini/gemini-2.0-flash-lite",
    api_key="AIzaSyALJlpyXFzcgyWMHLCSn-zON1gL8e1Z9ww",
    temperature=1
)

agents_config = load_yaml("config/agents.yaml")
tasks_config = load_yaml("config/tasks.yaml")

jd_parser_agent = Agent(
    role=agents_config["jd_parser_agent"]["role"],
    goal=agents_config["jd_parser_agent"]["goal"],
    backstory=agents_config["jd_parser_agent"]["backstory"],
    llm=llm
)

rank_candidates_agent =  Agent(
    role=agents_config["candidate_ranking_agent"]["role"],
    goal=agents_config["candidate_ranking_agent"]["goal"],
    backstory=agents_config["candidate_ranking_agent"]["backstory"],
    llm=llm
)

def parse_jd(job_description: str):
    task_cfg = tasks_config["parse_jd_task"]
    prompt_filled = task_cfg["prompt"].replace("{{job_description}}", job_description)

    jd_task = Task(
        description=task_cfg["description"],
        expected_output=task_cfg["expected_output"],
        agent=jd_parser_agent,
        prompt=prompt_filled
    )

    jd_crew = Crew(
        agents=[jd_parser_agent],
        tasks=[jd_task],
        process=Process.sequential
    )

    result = jd_crew.kickoff()
    return result

async def rank_candidates_stream(parsed_jd: dict, candidates: list):
    task_cfg = tasks_config["evaluate_single_candidate_task"]
    all_results = []

    for candidate in candidates:
        username = candidate.get("username", "unknown_user")

        prompt_filled = (
            task_cfg["prompt"]
            .replace("{{parsed_jd}}", json.dumps(parsed_jd, indent=2))
            .replace("{{candidate}}", json.dumps(candidate, indent=2))
        )

        eval_task = Task(
            description=task_cfg["description"],
            expected_output=task_cfg["expected_output"],
            agent=rank_candidates_agent,
            prompt=prompt_filled
        )

        eval_crew = Crew(
            agents=[rank_candidates_agent],
            tasks=[eval_task],
            process=Process.sequential
        )

        try:
            result = eval_crew.kickoff()

            # Use a safe JSON parse helper (assuming jp.parse safely handles non-JSON strings)
            parsed_result = jp.parse(result)

            # Ensure username consistency
            if parsed_result.get("username") != username:
                parsed_result["username"] = username

        except Exception as e:
            parsed_result = {
                "username": username,
                "score": 0.0,
                "reasoning": "Error during evaluation.",
                "summary": str(e)
            }

        all_results.append(parsed_result)

    # Rank candidates by descending score
    ranked = sorted(all_results, key=lambda x: x.get("score", 0.0), reverse=True)
    for i, c in enumerate(ranked, start=1):
        c["rank"] = i

    final_output = {
        "type": "final_summary",
        "ranked_candidates": ranked,
        "total_users": len(ranked),
        "summary": "Candidates ranked based on GitHub alignment with the JD."
    }

    return final_output
