
from app.ai import (
    generate_response,
    evaluate_answer,
    get_candidate,
    get_relevant_curriculum,
    generate_adaptive_question
)

from app.prompts import (
    interview_prompt,
    adaptive_interview_prompt
)


# =========================
# Candidate Agent
# =========================

def candidate_agent(candidate_name):

    return get_candidate(candidate_name)


# =========================
# Retrieval Agent
# =========================

def retrieval_agent(candidate):

    completed_topics = [
        mission["title"]
        for mission in candidate.get("missions", [])
        if mission.get("passed") is True
    ]

    curriculum = get_relevant_curriculum(candidate)

    return {
        "completed_topics": completed_topics,
        "curriculum": curriculum
    }


# =========================
# Interviewer Agent
# =========================

def interviewer_agent(
    candidate_name,
    role,
    completed_topics=None,
    asked_topics=None
):

    candidate = candidate_agent(candidate_name)

    if not candidate:
        return "Candidate not found"

    prompt = interview_prompt(
        candidate=candidate,
        role=role,
        completed_topics=completed_topics,
        asked_topics=asked_topics
    )

    return generate_response(prompt)


# =========================
# Evaluator Agent
# =========================

def evaluator_agent(question, answer):

    return evaluate_answer(
        question,
        answer
    )


# =========================
# Adaptive Interviewer Agent
# =========================

def adaptive_interviewer_agent(
    candidate_name,
    role,
    previous_question,
    previous_answer,
    evaluation,
    completed_topics=None,
    asked_topics=None
):

    candidate = candidate_agent(candidate_name)

    if not candidate:
        return "Candidate not found"

    prompt = adaptive_interview_prompt(
        candidate=candidate,
        role=role,
        previous_question=previous_question,
        previous_answer=previous_answer,
        evaluation=evaluation,
        completed_topics=completed_topics or [],
        asked_topics=asked_topics or []
    )

    return generate_response(prompt)


# =========================
# Initial Interview
# =========================

def interview_orchestrator(
    candidate_name,
    role,
    asked_topics=None
):

    candidate = candidate_agent(candidate_name)

    if not candidate:
        return {
            "error": "Candidate not found"
        }

    context = retrieval_agent(candidate)

    question = interviewer_agent(
        candidate_name=candidate_name,
        role=role,
        completed_topics=context["completed_topics"],
        asked_topics=asked_topics or []
    )

    return {
        "candidate": candidate["member"],
        "context": context,
        "question": question
    }


# =========================
# Adaptive Interview
# =========================

def adaptive_interview_orchestrator(
    candidate_name,
    role,
    question,
    answer,
    asked_topics=None
):

    candidate = candidate_agent(candidate_name)

    if not candidate:
        return {
            "error": "Candidate not found"
        }

    context = retrieval_agent(candidate)

    completed_topics = context["completed_topics"]

    evaluation = evaluator_agent(
        question,
        answer
    )

    next_question = adaptive_interviewer_agent(
        candidate_name=candidate_name,
        role=role,
        previous_question=question,
        previous_answer=answer,
        evaluation=evaluation,
        completed_topics=completed_topics,
        asked_topics=asked_topics or []
    )

    return {
        "candidate": candidate["member"],
        "previous_question": question,
        "answer": answer,
        "evaluation": evaluation,
        "next_question": next_question
    }
