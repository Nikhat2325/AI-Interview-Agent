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

def load_curriculum():

    with open("data/curriculum.json", encoding="utf-8") as f:
        return json.load(f)


def get_relevant_curriculum(candidate):

    curriculum = load_curriculum()

    completed_topics = {
        mission["title"].lower()
        for mission in candidate["missions"]
        if mission.get("passed") is True
    }

    relevant_days = []

    for day in curriculum.get("days", []):

        title = day.get("title", "").lower()

        for topic in completed_topics:

            # Topic ke important words check karna
            topic_words = topic.split()

            if any(word in title for word in topic_words if len(word) > 4):

                relevant_days.append(day)
                break

    return relevant_days


def generate_response(candidate_name, role):

    candidate = get_candidate(candidate_name)

    if not candidate:
        return "Candidate not found"

    member = candidate["member"]

    missions = [
        mission["title"]
        for mission in candidate["missions"]
        if mission.get("passed") is True
    ]

    relevant_curriculum = get_relevant_curriculum(candidate)

    curriculum_context = [
        {
            "day": item.get("day"),
            "title": item.get("title"),
            "type": item.get("type"),
            "tools": item.get("tools", []),
            "objectives": item.get("objectives", [])
        }
        for item in relevant_curriculum
    ]
    prompt = f"""
You are an expert technical interviewer.

Candidate:
Name: {member['name']}
Target Role: {role}
Experience: {member['yearsExperience']} years
Education: {member['education']}

Completed candidate topics:
{missions}

Relevant curriculum:
{curriculum_context}

Generate ONE personalized technical interview question.

STRICT RULES:
1. The question must be based on the candidate's completed topics.
2. Use curriculum only to determine technical depth.
3. Do NOT copy the curriculum scenario literally.
4. Do NOT mention healthcare, medical systems, or healthcare chatbots.
5. Do NOT introduce unrelated domain-specific scenarios.
6. Do NOT ask about persistent user accounts or long-term conversation history.
7. Do NOT ask about voice interaction, authentication, or mobile applications.
8. You may use generic software engineering scenarios.
9. Match difficulty to the candidate's experience.
10. Prefer practical engineering questions over definition-based questions.
11. Return ONLY the question. Do not add introductions or explanations.

Generate the question now.
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
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