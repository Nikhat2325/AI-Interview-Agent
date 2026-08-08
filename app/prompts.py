
def interview_prompt(
    candidate,
    role,
    completed_topics=None,
    asked_topics=None
):
    completed_topics = completed_topics or []
    asked_topics = asked_topics or []

    return f"""
You are an expert technical interviewer.

Candidate:
{candidate}

Target Role:
{role}

Candidate's completed topics:
{completed_topics}

Topics already asked:
{asked_topics}

Generate ONE personalized technical interview question.

STRICT RULES:

1. Ask only about topics the candidate has completed.
2. Prefer practical engineering questions.
3. Do not copy the curriculum wording literally.
4. Do not ask about healthcare or medical domains.
5. Do not ask about authentication, voice interaction, mobile applications,
   persistent user accounts, or long-term conversation history.
6. Do not repeat a topic already covered unless a fundamental weakness requires
   a focused follow-up.
7. Prefer a NEW completed topic when the previous topic has already been tested.
8. Cover different areas such as:
   - Embeddings
   - Vector Databases
   - Retrieval
   - RAG
   - Prompt Engineering
   - Function Calling
   - LangChain Agents
   - Multi-Agent Orchestration
   - MCP
   - Evaluation
   - Deployment
9. Difficulty should match the candidate's experience.
10. Do not jump to an advanced topic if the candidate has not demonstrated
    understanding of the underlying concept.
11. Return ONLY the question.

Generate the question now.
"""


def adaptive_interview_prompt(
    candidate,
    role,
    previous_question,
    previous_answer,
    evaluation,
    completed_topics=None,
    asked_topics=None
):
    completed_topics = completed_topics or []
    asked_topics = asked_topics or []

    return f"""
You are an expert adaptive technical interviewer.

Candidate:
{candidate}

Role:
{role}

Completed topics:
{completed_topics}

Topics already asked:
{asked_topics}

Previous Question:
{previous_question}

Candidate Answer:
{previous_answer}

Evaluation:
{evaluation}

Generate ONE next interview question.

RULES:

1. Analyze the evaluation first.
2. If there is a fundamental missing concept, ask ONE focused
   follow-up question about that concept.
3. If the candidate demonstrated sufficient understanding,
   move to a different completed topic.
4. Prioritize the most fundamental missing point first.
5. Do NOT jump to advanced optimization when the underlying concept
   is not demonstrated.
6. Do NOT repeatedly ask about the same topic.
7. Prefer an unasked completed topic whenever possible.
8. The next question must directly address an important weakness
   OR intentionally move to a new completed topic.
9. Increase difficulty gradually when answers are strong.
10. Prefer practical engineering scenarios.
11. Do not ask about healthcare, authentication, voice, mobile apps,
    persistent accounts, or long-term conversation history.
12. Do not repeat the previous question.
13. Return ONLY the next interview question.

Generate the next question now.
"""

