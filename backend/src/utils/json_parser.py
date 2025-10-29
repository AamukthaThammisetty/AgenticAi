import json
import re

def parse(raw_output: str):

    if not raw_output:
        return {"error": "Empty response", "raw": raw_output}

    text = str(raw_output).strip()

    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    lines = text.splitlines()
    if len(lines) > 2 and not lines[0].strip().startswith("{"):
        text = "\n".join(lines[1:-1]).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return {"error": "Parsing failed", "raw": text}
