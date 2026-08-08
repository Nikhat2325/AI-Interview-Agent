import json
import os
from dotenv import load_dotenv
from groq import Groq

# =========================================================
# GROQ SETUP
# =========================================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# CANDIDATES
# =========================================================

def load_candidates():
    with open(
        "data/candidates.json",
        encoding="utf-8"
    ) as f:
        return json.load(f)["candidates"]


def get_candidate(name):
    candidates = load_candidates()

    for candidate in candidates:
        if candidate["member"]["name"].lower() == name.lower():
            return candidate

    return None


# =========================================================
# CURRICULUM
# =========================================================

def load_curriculum():
    with open(
        "data/curriculum.json",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def get_completed_topics(candidate):
    """
    Candidate ke successfully completed curriculum topics
    return karta hai.
    """

    return [
        mission["title"]
        for mission in candidate.get("missions", [])
        if mission.get("passed") is True
    ]


def get_relevant_curriculum(candidate):
    """
    Candidate ke completed topics ke corresponding
    curriculum days return karta hai.

    IMPORTANT:
    Curriculum ka original order preserve kiya gaya hai.
    """

    curriculum = load_curriculum()

    completed_topics = {
        topic.lower().strip()
        for topic in get_completed_topics(candidate)
    }

    relevant_days = []

    for day in curriculum.get("days", []):

        title = day.get("title", "").lower().strip()

        # Exact / strong title matching first
        matched = False

        for topic in completed_topics:

            if topic == title:
                matched = True
                break

            # Topic ke meaningful words
            topic_words = [
                word
                for word in topic.split()
                if len(word) > 4
            ]

            if topic_words:

                match_count = sum(
                    1
                    for word in topic_words
                    if word in title
                )

                # At least half meaningful words match
                if match_count >= max(1, len(topic_words) // 2):
                    matched = True
                    break

        if matched:
            relevant_days.append(day)

    return relevant_days


# =========================================================
# CURRICULUM CONTEXT
# =========================================================

def build_curriculum_context(candidate):
    """
    LLM ke liye clean curriculum context banata hai.
    """

    relevant_curriculum = get_relevant_curriculum(candidate)

    return [
        {
            "day": item.get("day"),
            "title": item.get("title"),
            "type": item.get("type"),
            "tools": item.get("tools", []),
            "objectives": item.get("objectives", [])
        }
        for item in relevant_curriculum
    ]


# =========================================================
# INITIAL INTERVIEW QUESTION
# =========================================================
def generate_response(
    candidate_name,
    role,
    topic,
    question_type="warmup",
    asked_questions=None
):
    candidate = get_candidate(candidate_name)

    if not candidate:
        return "Candidate not found"

    member = candidate["member"]

    asked_questions = asked_questions or []

    prompt = f"""
You are an expert technical interviewer.

Candidate:
Name: {member['name']}
Role: {role}
Experience: {member['yearsExperience']} years
Education: {member['education']}

CURRENT CURRICULUM TOPIC:
{topic}

QUESTION TYPE:
{question_type}

ALREADY ASKED QUESTIONS:
{asked_questions}

Generate exactly ONE interview question.

INTERVIEW RULES:

1. The question MUST be directly related to the CURRENT CURRICULUM TOPIC.
2. Do NOT return the topic title.
3. Do NOT return the curriculum title.
4. Generate an actual interview question.
5. For warmup:
   - ask a simple fundamental question
   - test basic understanding
   - do not ask advanced system design
6. For basic:
   - test the core concept
7. For followup:
   - build directly on the previous concept
8. For deeper:
   - test deeper understanding or reasoning
9. For scenario:
   - use a practical software engineering situation
10. For system_design:
   - ask a system/design question only after fundamentals are established
11. Do not jump to unrelated topics.
12. Do not repeat an already asked question.
13. Match difficulty to candidate experience.
14. Return ONLY the question.
15. Do not write explanations.
16. Do not write "Question:".
17. Do not write the topic name separately.

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
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

# =========================================================
# ANSWER EVALUATION
# =========================================================

def evaluate_answer(
    question,
    answer
):
    """
    Candidate ke answer ko evaluate karta hai.
    """

    prompt = f"""
You are an expert technical interviewer.

QUESTION
--------
{question}

CANDIDATE ANSWER
----------------
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
    "improvement_feedback": [],
    "understanding_level": "weak",
    "should_follow_up": true
}}


RULES
-----

score:
- integer from 0 to 10

technical_accuracy:
- number between 0 and 1

understanding_level:
- weak
- basic
- good
- strong

should_follow_up:
- true if an important fundamental concept is missing
- false if the candidate demonstrated sufficient understanding

missing_points:
- mention only meaningful technical gaps
- prioritize fundamental concepts first

improvement_feedback:
- provide concise actionable technical feedback

IMPORTANT:
Do not invent missing concepts that are not necessary
for answering the question.

Evaluate only what the question actually asked.

Focus on:
- correctness
- conceptual understanding
- reasoning
- practical understanding
- engineering judgment
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    result = response.choices[0].message.content.strip()

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
            "understanding_level": "weak",
            "should_follow_up": True,
            "raw_response": result
        }


# =========================================================
# ADAPTIVE QUESTION
# =========================================================
# =========================================================
# ADAPTIVE QUESTION
# =========================================================

def generate_adaptive_question(
    candidate_name,
    role,
    previous_question,
    previous_answer,
    evaluation,
    current_topic,
    stage,
    asked_topics=None,
    next_topic=None
):
    """
    Generates exactly ONE next interview question.

    IMPORTANT:
    Topic selection is controlled by interview.py.

    This function ONLY generates a question for the
    topic selected by interview.py.
    """

    # -----------------------------------------------------
    # Get candidate
    # -----------------------------------------------------

    candidate = get_candidate(candidate_name)

    if not candidate:
        return "Candidate not found"

    member = candidate["member"]

    # -----------------------------------------------------
    # Safe values
    # -----------------------------------------------------

    asked_topics = asked_topics or []

    if not current_topic:
        return "Unable to determine current interview topic."

    # -----------------------------------------------------
    # Evaluation values
    # -----------------------------------------------------

    understanding_level = "basic"
    should_follow_up = True

    if isinstance(evaluation, dict):

        understanding_level = evaluation.get(
            "understanding_level",
            "basic"
        )

        should_follow_up = evaluation.get(
            "should_follow_up",
            True
        )

    # -----------------------------------------------------
    # IMPORTANT
    #
    # interview.py controls topic movement.
    #
    # If next_topic is provided, interview.py has explicitly
    # decided to move to that topic.
    #
    # Otherwise stay on current_topic.
    # -----------------------------------------------------

    if next_topic:
        question_topic = next_topic
        moving_to_new_topic = True
    else:
        question_topic = current_topic
        moving_to_new_topic = False

    # -----------------------------------------------------
    # Curriculum context
    # -----------------------------------------------------

    curriculum_context = build_curriculum_context(
        candidate
    )

    # -----------------------------------------------------
    # Stage instructions
    # -----------------------------------------------------

    if moving_to_new_topic:

        stage_instruction = f"""
A topic transition has been explicitly authorized
by the interview controller.

The NEW CURRENT TOPIC is:

{question_topic}

Start this new topic from the BASIC/FUNDAMENTAL level.

Ask a simple conceptual question about this new topic.

Do NOT ask a scenario question.
Do NOT ask a system design question.
Do NOT ask an advanced implementation question.

The candidate is seeing this topic for the first time.
"""

    elif stage == "warm-up":

        stage_instruction = """
Ask a very simple fundamental question about the
CURRENT TOPIC.

Test basic conceptual understanding.

Do NOT ask implementation questions.

Do NOT ask architecture questions.

Do NOT ask system-design questions.

Do NOT ask optimization questions.
"""

    elif stage == "basic":

        stage_instruction = """
Ask a basic conceptual question about the CURRENT TOPIC.

Test the core idea.

The question should naturally follow from the
previous question and answer.

Do NOT introduce another topic.
"""

    elif stage == "follow-up":

        stage_instruction = """
Stay STRICTLY on the CURRENT TOPIC.

Build directly on the previous question and answer.

Ask ONE logical follow-up question.

If the candidate has a weakness, clarify the
fundamental concept.

Do NOT introduce another topic.
"""

    elif stage == "deeper":

        stage_instruction = """
Stay STRICTLY on the CURRENT TOPIC.

Ask a deeper question about the same topic.

The question may test:

- reasoning
- implementation understanding
- practical usage
- trade-offs
- debugging

Do NOT introduce another topic.
"""

    elif stage == "scenario":

        stage_instruction = """
Ask ONE practical software-engineering scenario
involving the CURRENT TOPIC.

The candidate should apply the CURRENT TOPIC
to solve the situation.

Do NOT introduce unrelated technologies.
"""

    elif stage == "system-design":

        stage_instruction = """
Ask ONE system-design question involving the
CURRENT TOPIC.

The system-design question must naturally belong
to the CURRENT TOPIC.

Do NOT introduce unrelated technologies.
"""

    elif stage == "candidate-specific":

        stage_instruction = """
Ask ONE practical technical question about the
CURRENT TOPIC that can reasonably relate to the
candidate's role or experience.

Keep it technically focused.

Do NOT introduce another topic.
"""

    elif stage == "final":

        stage_instruction = f"""
Ask ONE final meaningful technical question.

The question must be about:

{question_topic}

Do NOT introduce an unrelated topic.
"""

    else:

        stage_instruction = """
Ask ONE appropriate technical question about the
CURRENT TOPIC.

Do NOT introduce another topic.
"""

    # -----------------------------------------------------
    # Answer-based instructions
    # -----------------------------------------------------

    if should_follow_up:

        answer_instruction = """
The evaluation indicates that an important
fundamental concept may still be missing.

Stay on the CURRENT TOPIC.

Ask the MOST FUNDAMENTAL useful follow-up.

Do NOT jump to another topic.

Do NOT ask an advanced question.
"""

    elif understanding_level == "weak":

        answer_instruction = """
The candidate demonstrated weak understanding.

Stay on the CURRENT TOPIC.

Ask a simpler fundamental question that helps
clarify the concept.

Do NOT move to another topic.
"""

    elif understanding_level == "basic":

        answer_instruction = """
The candidate demonstrated basic understanding.

Ask the next logical question about the
CURRENT TOPIC.

Move gradually from:

definition
to
understanding
to
application.

Do NOT jump to advanced concepts.
"""

    elif understanding_level == "good":

        answer_instruction = """
The candidate demonstrated good understanding.

Ask a slightly deeper practical or reasoning
question about the CURRENT TOPIC.

Do NOT introduce another topic unless the
interview controller explicitly supplied a
NEW CURRENT TOPIC.
"""

    elif understanding_level == "strong":

        answer_instruction = """
The candidate demonstrated strong understanding.

Do not ask another basic definition question.

If the interview controller supplied a NEW
CURRENT TOPIC, ask a basic question about that
new topic.

Otherwise ask a deeper practical question about
the CURRENT TOPIC.
"""

    else:

        answer_instruction = """
Ask an appropriate question about the CURRENT TOPIC.

Do not introduce another topic.
"""

    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    prompt = f"""
You are an expert technical interviewer.

Generate EXACTLY ONE interview question.

==================================================
CANDIDATE
==================================================

Name:
{member.get('name', candidate_name)}

Role:
{role}

Experience:
{member.get('yearsExperience', 0)} years

Education:
{member.get('education', 'Not provided')}

==================================================
CURRENT TOPIC
==================================================

{question_topic}

==================================================
CURRENT STAGE
==================================================

{stage}

==================================================
PREVIOUS QUESTION
==================================================

{previous_question}

==================================================
CANDIDATE ANSWER
==================================================

{previous_answer}

==================================================
EVALUATION
==================================================

{evaluation}

==================================================
TOPICS ALREADY ASKED
==================================================

{asked_topics}

==================================================
CURRICULUM
==================================================

{curriculum_context}

==================================================
TOPIC CONTROL
==================================================

THIS IS A STRICT RULE.

The question MUST be about:

{question_topic}

You MUST NOT choose the topic yourself.

The interview controller has already selected
the topic.

Do NOT jump to another curriculum topic.

For example:

If the CURRENT TOPIC is:

Embeddings Explained

then valid questions include:

- What are word embeddings?
- How do embeddings represent semantic relationships?
- Why are similar words represented by similar vectors?
- What are the limitations of word embeddings?

Invalid questions include:

- What is a vector database?
- What is RAG?
- What is LangChain?
- What are AI agents?
- What is MCP?

Those topics are NOT allowed unless they are the
CURRENT TOPIC.

==================================================
TOPIC TRANSITION
==================================================

NEXT TOPIC:

{next_topic}

If NEXT TOPIC is None:

STAY on:

{current_topic}

If NEXT TOPIC is provided:

{next_topic}

then the interview controller has explicitly
authorized the topic transition.

In that case:

START THE NEW TOPIC FROM BASIC LEVEL.

Do NOT immediately ask a difficult question.

==================================================
STAGE INSTRUCTIONS
==================================================

{stage_instruction}

==================================================
ANSWER INSTRUCTIONS
==================================================

{answer_instruction}

==================================================
QUESTION PROGRESSION
==================================================

Use this progression:

LEVEL 1
Basic definition
        ↓
LEVEL 2
Conceptual understanding
        ↓
LEVEL 3
Practical application
        ↓
LEVEL 4
Scenario / debugging
        ↓
LEVEL 5
System design / trade-offs

Do not jump from LEVEL 1 directly to LEVEL 5.

==================================================
STRICT RULES
==================================================

1. Ask exactly ONE question.

2. Return ONLY the question.

3. Do not return an explanation.

4. Do not return reasoning.

5. Do not return evaluation.

6. Do not mention the candidate's score.

7. Do not mention understanding_level.

8. Do not mention stage.

9. Do not mention topic separately.

10. Do not mention next topic.

11. Do not write "Question:".

12. Do not write "Here's the next question:".

13. Do not write "Based on the candidate's answer".

14. Do not provide the answer.

15. Do not use markdown.

16. Do not repeat the previous question.

17. Do not introduce unrelated technologies.

18. Do not ask about healthcare.

19. Do not ask about medical systems.

20. Do not ask about authentication.

21. Do not ask about voice interaction.

22. Do not ask about mobile applications.

23. Do not ask about persistent user accounts.

24. Do not ask about long-term conversation history.

25. Do not randomly select another curriculum topic.

26. If CURRENT TOPIC is Embeddings Explained,
    stay on embeddings.

27. If CURRENT TOPIC is Vector Databases Overview,
    stay on vector databases.

28. If CURRENT TOPIC is RAG,
    stay on RAG.

29. Only change topic when the interview controller
    explicitly provides NEXT TOPIC.

==================================================
FINAL OUTPUT
==================================================

Return exactly ONE natural-language interview question.

Nothing else.
"""

    # -----------------------------------------------------
    # Groq
    # -----------------------------------------------------

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[

            {
                "role": "system",
                "content": (
                    "You are a strict technical interviewer. "
                    "Never change the supplied topic. "
                    "Return exactly one interview question."
                )
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.1
    )

    # -----------------------------------------------------
    # Get result
    # -----------------------------------------------------

    result = response.choices[0].message.content.strip()

    # -----------------------------------------------------
    # Remove common prefixes
    # -----------------------------------------------------

    prefixes = [
        "Question:",
        "Here's the next question:",
        "Here is the next question:",
        "Follow-up question:",
        "Next question:"
    ]

    for prefix in prefixes:

        if result.lower().startswith(
            prefix.lower()
        ):

            result = result[
                len(prefix):
            ].strip()

    # -----------------------------------------------------
    # Remove markdown
    # -----------------------------------------------------

    result = result.replace(
        "**",
        ""
    ).strip()

    # -----------------------------------------------------
    # Safety fallback
    # -----------------------------------------------------

    if not result:

        return (
            f"What is the basic purpose of "
            f"{question_topic}?"
        )

    return result