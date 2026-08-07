import json


def load_candidates():

    with open("data/candidates.json") as f:
        return json.load(f)["candidates"]



def get_candidate(name):

    candidates = load_candidates()

    for candidate in candidates:

        if candidate["member"]["name"].lower() == name.lower():
            return candidate

    return None



def generate_response(candidate_name, role):

    candidate = get_candidate(candidate_name)

    if not candidate:
        return "Candidate not found"


    member = candidate["member"]

    missions = [
        m["title"]
        for m in candidate["missions"]
        if m.get("passed")
    ]


    return {
        "candidate": member["name"],
        "role": role,
        "experience": member["yearsExperience"],
        "completed_topics": missions,
        "message":
        "Candidate profile retrieved successfully"
    }