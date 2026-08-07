import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


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


    prompt = f"""
You are an expert AI technical interviewer.

Candidate Details:
Name: {member['name']}
Role: {member['jobRole']}
Experience: {member['yearsExperience']} years
Education: {member['education']}

Completed AI learning topics:
{missions}


Generate one personalized technical interview question
for the role: {role}

Only return the question.
"""


    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.7
    )


    return response.choices[0].message.content
def evaluate_answer(question, answer):

    prompt = f"""
You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the candidate's answer.

Return ONLY valid JSON.
Do not use markdown.
Do not use ```json.

Use exactly this structure:

{{
    "score": 0,
    "technical_accuracy": 0.0,
    "missing_points": [],
    "improvement_feedback": []
}}

Score must be between 0 and 10.
Technical accuracy must be between 0 and 1.
"""


    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.2
    )


    import json

    result = response.choices[0].message.content

    try:
        return json.loads(result)

    except json.JSONDecodeError:

        return {
            "score": 0,
            "technical_accuracy": 0,
            "missing_points": [],
            "improvement_feedback": [
                "AI returned an invalid evaluation format."
            ],
            "raw_response": result
        }