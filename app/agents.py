from app.ai import generate_response, evaluate_answer


def candidate_agent(candidate_name):
    """
    Retrieves candidate information.
    """
    from app.ai import get_candidate

    candidate = get_candidate(candidate_name)

    if not candidate:
        return None

    return candidate


def retrieval_agent(candidate):
    """
    Retrieves the candidate's completed topics
    and relevant curriculum context.
    """
    from app.ai import get_relevant_curriculum

    completed_topics = [
        mission["title"]
        for mission in candidate["missions"]
        if mission.get("passed") is True
    ]

    curriculum = get_relevant_curriculum(candidate)

    return {
        "completed_topics": completed_topics,
        "curriculum": curriculum
    }


def interviewer_agent(candidate_name, role):
    """
    Generates a personalized interview question.
    """
    return generate_response(candidate_name, role)


def evaluator_agent(question, answer):
    """
    Evaluates candidate's answer.
    """
    return evaluate_answer(question, answer)


def interview_orchestrator(candidate_name, role, answer=None):
    """
    Coordinates the complete interview workflow.
    """

    # 1. Candidate Agent
    candidate = candidate_agent(candidate_name)

    if not candidate:
        return {
            "error": "Candidate not found"
        }

    # 2. Retrieval Agent
    context = retrieval_agent(candidate)

    # 3. Interviewer Agent
    question = interviewer_agent(candidate_name, role)

    result = {
        "candidate": candidate["member"],
        "context": context,
        "question": question
    }

    # 4. Evaluation Agent
    if answer:
        evaluation = evaluator_agent(question, answer)
        result["evaluation"] = evaluation

    return result