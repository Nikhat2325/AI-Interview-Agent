from fastapi import APIRouter
from pydantic import BaseModel

from app.ai import (
    evaluate_answer,
    generate_response,
    generate_adaptive_question,
    get_candidate,
    get_completed_topics,
)

router = APIRouter()


# =========================================================
# Interview Sessions
# =========================================================

sessions = {}


# =========================================================
# Request Model
# =========================================================

class InterviewAPIRequest(BaseModel):
    sessionId: str
    candidate: dict | None = None
    message: str | None = None


# =========================================================
# Candidate Name
# =========================================================

def get_candidate_name(candidate):

    if not candidate:
        return "Candidate"

    if "member" in candidate:
        return candidate["member"].get(
            "name",
            "Candidate"
        )

    return candidate.get(
        "name",
        "Candidate"
    )


# =========================================================
# Candidate Role
# =========================================================

def get_candidate_role(candidate):

    if not candidate:
        return "Software Engineer"

    if "member" in candidate:
        return candidate["member"].get(
            "jobRole",
            "Software Engineer"
        )

    return candidate.get(
        "jobRole",
        "Software Engineer"
    )


# =========================================================
# Interview Stage
# =========================================================

def get_interview_stage(question_number):

    stages = {
        1: "warm-up",
        2: "basic",
        3: "follow-up",
        4: "deeper",
        5: "new-topic",
        6: "scenario",
        7: "new-topic",
        8: "system-design",
        9: "candidate-specific",
        10: "final"
    }

    return stages.get(
        question_number,
        "adaptive"
    )


# =========================================================
# Initial Difficulty Based on Attempts
# =========================================================

def get_initial_difficulty(attempts):

    try:
        attempts = int(attempts)
    except (TypeError, ValueError):
        attempts = 1

    if attempts <= 1:
        return "medium-hard"

    elif attempts <= 3:
        return "medium"

    else:
        return "basic"


# =========================================================
# Get Next Curriculum Topic
# =========================================================

def get_next_topic(session):

    completed_topics = session.get(
        "completed_topics",
        []
    )

    current_index = session.get(
        "topic_index",
        0
    )

    next_index = current_index + 1

    if next_index >= len(completed_topics):
        return None

    next_topic_data = completed_topics[next_index]

    # New format
    if isinstance(next_topic_data, dict):
        return next_topic_data

    # Safety for old format
    if isinstance(next_topic_data, str):

        return {
            "title": next_topic_data,
            "day": None,
            "attempts": 1
        }

    return None


# =========================================================
# Get Current Topic Data
# =========================================================

def get_topic_data(session):

    topics = session.get(
        "completed_topics",
        []
    )

    index = session.get(
        "topic_index",
        0
    )

    if index >= len(topics):
        return None

    topic = topics[index]

    if isinstance(topic, dict):
        return topic

    if isinstance(topic, str):

        return {
            "title": topic,
            "day": None,
            "attempts": 1
        }

    return None


# =========================================================
# Clean AI Generated Question
# =========================================================

def clean_question(question, fallback):

    if not question:
        question = fallback

    question = str(question).strip()

    prefixes = [
        "Question:",
        "Follow-up question:",
        "Next question:"
    ]

    for prefix in prefixes:

        if question.lower().startswith(
            prefix.lower()
        ):

            question = question[
                len(prefix):
            ].strip()

    question = question.replace(
        "**",
        ""
    ).strip()

    return question


# =========================================================
# Determine Understanding
# =========================================================

def get_understanding_level(evaluation):

    if not isinstance(evaluation, dict):
        return "basic"

    level = evaluation.get(
        "understanding_level",
        "basic"
    )

    if level is None:
        return "basic"

    return str(level).lower().strip()


# =========================================================
# Should Move To Next Topic?
# =========================================================

def should_move_to_next_topic(
    understanding_level,
    topic_question_count
):

    # Strong / good answer
    # -> immediately next topic

    if understanding_level in [
        "strong",
        "good"
    ]:

        return True, "strong_answer"

    # Maximum 2 questions per topic
    # -> force next topic

    if topic_question_count >= 2:

        return True, "maximum_two_questions_reached"

    # Weak / basic / partial
    # -> one follow-up

    return False, "follow_up_required"


# =========================================================
# Generate Question For New Topic
# =========================================================

def generate_new_topic_question(
    session,
    current_question,
    candidate_answer,
    evaluation,
    next_topic_data
):

    topic = next_topic_data["title"]

    attempts = next_topic_data.get(
        "attempts",
        1
    )

    difficulty = get_initial_difficulty(
        attempts
    )

    question = generate_adaptive_question(

        candidate_name=session[
            "candidate_name"
        ],

        role=session[
            "role"
        ],

        previous_question=current_question,

        previous_answer=candidate_answer,

        evaluation=evaluation,

        current_topic=topic,

        stage="new-topic",

        asked_topics=session[
            "asked_topics"
        ],

        next_topic=topic,

        difficulty=difficulty
    )

    fallback = (
        f"What is the main purpose of "
        f"{topic}?"
    )

    return clean_question(
        question,
        fallback
    )


# =========================================================
# Generate Follow-up Question
# =========================================================

def generate_followup_question(
    session,
    current_question,
    candidate_answer,
    evaluation,
    current_topic,
    understanding_level
):

    if understanding_level == "basic":

        followup_stage = "follow-up"
        difficulty = "basic"

    elif understanding_level == "partial":

        followup_stage = "deeper"
        difficulty = "medium"

    else:

        followup_stage = "deeper"
        difficulty = "medium"

    question = generate_adaptive_question(

        candidate_name=session[
            "candidate_name"
        ],

        role=session[
            "role"
        ],

        previous_question=current_question,

        previous_answer=candidate_answer,

        evaluation=evaluation,

        current_topic=current_topic,

        stage=followup_stage,

        asked_topics=session[
            "asked_topics"
        ],

        next_topic=None,

        difficulty=difficulty
    )

    fallback = (
        f"Can you explain the main concept "
        f"of {current_topic} in your own words?"
    )

    return clean_question(
        question,
        fallback
    )


# =========================================================
# POST /api/interview
# =========================================================

@router.post("/api/interview")
def interview(request: InterviewAPIRequest):

    session_id = request.sessionId


    # =====================================================
    # START INTERVIEW
    # =====================================================

    if session_id not in sessions:

        if not request.candidate:

            return {
                "reply": (
                    "Candidate information is required "
                    "to start the interview."
                ),
                "done": False
            }

        candidate = request.candidate

        candidate_name = get_candidate_name(
            candidate
        )

        role = get_candidate_role(
            candidate
        )


        # =================================================
        # Get Full Candidate
        # =================================================

        full_candidate = get_candidate(
            candidate_name
        )

        if not full_candidate:

            return {
                "reply": "Candidate not found.",
                "done": True
            }


        # =================================================
        # Get Eligible Topics
        #
        # get_completed_topics() should already filter:
        # passed == True
        # skipped != True
        # =================================================

        completed_topics = get_completed_topics(
            full_candidate
        )

        print(
            "========== ELIGIBLE TOPICS =========="
        )

        print(
            completed_topics
        )

        print(
            "====================================="
        )


        if not completed_topics:

            return {
                "reply": (
                    "No eligible curriculum topics "
                    "found for this candidate."
                ),
                "done": True
            }


        # =================================================
        # FIRST TOPIC
        # =================================================

        first_topic_data = completed_topics[0]

        first_topic = first_topic_data[
            "title"
        ]

        first_attempts = first_topic_data.get(
            "attempts",
            1
        )

        first_difficulty = get_initial_difficulty(
            first_attempts
        )


        print(
            "========== FIRST TOPIC =========="
        )

        print(
            "Topic:",
            first_topic
        )

        print(
            "Attempts:",
            first_attempts
        )

        print(
            "Initial difficulty:",
            first_difficulty
        )

        print(
            "================================="
        )


        # =================================================
        # Generate First Question
        # =================================================

        first_question = generate_response(

            candidate_name=candidate_name,

            role=role,

            topic=first_topic,

            question_type="warmup",

            asked_questions=[],

            difficulty=first_difficulty
        )


        first_question = clean_question(
            first_question,
            (
                f"What is the main purpose "
                f"of {first_topic}?"
            )
        )


        # =================================================
        # Create Session
        # =================================================

        sessions[session_id] = {

            "sessionId": session_id,

            "candidate": full_candidate,

            "candidate_name": candidate_name,

            "role": role,

            # Eligible curriculum topics
            "completed_topics": completed_topics,

            # Current topic
            "current_topic": first_topic,

            "current_topic_attempts": first_attempts,

            "current_topic_difficulty": first_difficulty,

            # Topic position
            "topic_index": 0,

            # Current question
            "current_question": first_question,

            # Interview history
            "turns": [],

            "evaluations": [],

            "asked_topics": [],

            "asked_questions": [],

            # Questions asked on CURRENT topic
            "topic_question_count": 0,

            # Total answered questions
            "question_number": 1,

            "turn_count": 0
        }


        return {

            "reply": first_question,

            "done": False,

            "questionNumber": 1,

            "stage": "warm-up",

            "topic": first_topic
        }


    # =====================================================
    # EXISTING SESSION
    # =====================================================

    session = sessions[
        session_id
    ]


    # =====================================================
    # No Message
    # =====================================================

    if not request.message:

        return {

            "reply": session[
                "current_question"
            ],

            "done": False,

            "questionNumber": session[
                "question_number"
            ],

            "stage": get_interview_stage(
                session[
                    "question_number"
                ]
            ),

            "topic": session.get(
                "current_topic"
            )
        }


    # =====================================================
    # Current Question
    # =====================================================

    current_question = session[
        "current_question"
    ]

    candidate_answer = request.message

    current_topic = session.get(
        "current_topic"
    )


    # =====================================================
    # Evaluate Answer
    # =====================================================

    evaluation = evaluate_answer(

        current_question,

        candidate_answer
    )


    # =====================================================
    # Save Question
    # =====================================================

    session[
        "asked_questions"
    ].append(
        current_question
    )


    # =====================================================
    # Save Topic
    # =====================================================

    if current_topic:

        if current_topic not in session[
            "asked_topics"
        ]:

            session[
                "asked_topics"
            ].append(
                current_topic
            )


    # =====================================================
    # Increment Topic Question Count
    # =====================================================

    session[
        "topic_question_count"
    ] += 1

    topic_question_count = session[
        "topic_question_count"
    ]


    # =====================================================
    # Save Turn
    # =====================================================

    session[
        "turns"
    ].append({

        "question": current_question,

        "answer": candidate_answer,

        "evaluation": evaluation,

        "topic": current_topic
    })


    session[
        "evaluations"
    ].append(
        evaluation
    )


    # =====================================================
    # Increment Total Answered Questions
    # =====================================================

    session[
        "turn_count"
    ] += 1


    # =====================================================
    # MAX TOTAL QUESTIONS
    # =====================================================

    MAX_QUESTIONS = 10

    if session[
        "turn_count"
    ] >= MAX_QUESTIONS:

        feedback = build_final_feedback(
            session
        )

        return {

            "reply": "Interview completed.",

            "done": True,

            "feedback": feedback,

            "questionNumber": session[
                "question_number"
            ],

            "stage": "final",

            "topic": current_topic
        }


    # =====================================================
    # Evaluation Information
    # =====================================================

    understanding_level = (
        get_understanding_level(
            evaluation
        )
    )


    # =====================================================
    # Adaptive Decision
    # =====================================================

    move_to_next_topic, reason = (
        should_move_to_next_topic(

            understanding_level,

            topic_question_count
        )
    )


    print(
        "========== ADAPTIVE DECISION =========="
    )

    print(
        "Current topic:",
        current_topic
    )

    print(
        "Topic question count:",
        topic_question_count
    )

    print(
        "Understanding:",
        understanding_level
    )

    print(
        "Move to next topic:",
        move_to_next_topic
    )

    print(
        "Reason:",
        reason
    )

    print(
        "Topic index:",
        session[
            "topic_index"
        ]
    )

    print(
        "======================================="
    )


    # =====================================================
    # NEXT TOPIC
    # =====================================================

    if move_to_next_topic:

        next_topic_data = get_next_topic(
            session
        )


        print(
            "NEXT TOPIC DATA:",
            next_topic_data
        )


        # =================================================
        # No More Topics
        # =================================================

        if next_topic_data is None:

            feedback = build_final_feedback(
                session
            )

            return {

                "reply": "Interview completed.",

                "done": True,

                "feedback": feedback,

                "questionNumber": session[
                    "question_number"
                ],

                "stage": "final",

                "topic": current_topic
            }


        # =================================================
        # Move Topic Index
        # =================================================

        session[
            "topic_index"
        ] += 1


        # =================================================
        # New Topic Data
        # =================================================

        next_topic = next_topic_data[
            "title"
        ]

        next_attempts = next_topic_data.get(
            "attempts",
            1
        )

        next_difficulty = (
            get_initial_difficulty(
                next_attempts
            )
        )


        # =================================================
        # Update Session
        # =================================================

        session[
            "current_topic"
        ] = next_topic

        session[
            "current_topic_attempts"
        ] = next_attempts

        session[
            "current_topic_difficulty"
        ] = next_difficulty


        # =================================================
        # RESET CURRENT TOPIC COUNT
        #
        # Very important!
        # =================================================

        session[
            "topic_question_count"
        ] = 0


        # =================================================
        # Next Question Number
        # =================================================

        next_question_number = (
            session[
                "question_number"
            ] + 1
        )

        session[
            "question_number"
        ] = next_question_number


        # =================================================
        # Generate New Topic Question
        # =================================================

        next_question = (
            generate_new_topic_question(

                session=session,

                current_question=current_question,

                candidate_answer=candidate_answer,

                evaluation=evaluation,

                next_topic_data=next_topic_data
            )
        )


        # =================================================
        # Save New Question
        # =================================================

        session[
            "current_question"
        ] = next_question


        # =================================================
        # Response
        # =================================================

        return {

            "reply": next_question,

            "done": False,

            "questionNumber": (
                next_question_number
            ),

            "stage": "new-topic",

            "topic": next_topic
        }


    # =====================================================
    # FOLLOW-UP
    #
    # Candidate was not strong.
    # This can only happen after Question 1 of topic,
    # because Question 2 forces topic transition.
    # =====================================================

    next_question_number = (
        session[
            "question_number"
        ] + 1
    )

    session[
        "question_number"
    ] = next_question_number


    # =====================================================
    # Follow-up Stage
    # =====================================================

    if understanding_level in [
        "weak",
        "basic"
    ]:

        followup_stage = "follow-up"

    else:

        followup_stage = "deeper"


    # =====================================================
    # Generate Follow-up
    # =====================================================

    next_question = (
        generate_followup_question(

            session=session,

            current_question=current_question,

            candidate_answer=candidate_answer,

            evaluation=evaluation,

            current_topic=current_topic,

            understanding_level=understanding_level
        )
    )


    # =====================================================
    # Save Follow-up
    # =====================================================

    session[
        "current_question"
    ] = next_question


    # =====================================================
    # Response
    # =====================================================

    return {

        "reply": next_question,

        "done": False,

        "questionNumber": (
            next_question_number
        ),

        "stage": followup_stage,

        "topic": current_topic
    }


# =========================================================
# Final Feedback
# =========================================================

def build_final_feedback(session):

    evaluations = session[
        "evaluations"
    ]

    strengths = []

    gaps = []

    next_steps = []


    # =====================================================
    # Analyze Evaluations
    # =====================================================

    for evaluation in evaluations:

        if not isinstance(
            evaluation,
            dict
        ):
            continue


        # =================================================
        # Score
        # =================================================

        score = evaluation.get(
            "score",
            0
        )


        if isinstance(
            score,
            (int, float)
        ):

            if score >= 8:

                strengths.append(
                    "Demonstrated strong technical understanding."
                )

            elif score >= 6:

                strengths.append(
                    "Demonstrated reasonable understanding "
                    "of technical concepts."
                )


        # =================================================
        # Missing Points
        # =================================================

        missing_points = evaluation.get(
            "missing_points",
            []
        )

        if isinstance(
            missing_points,
            list
        ):

            for point in missing_points:

                if point not in gaps:

                    gaps.append(point)


        # =================================================
        # Improvement Feedback
        # =================================================

        improvements = evaluation.get(
            "improvement_feedback",
            []
        )

        if isinstance(
            improvements,
            list
        ):

            for item in improvements:

                if item not in next_steps:

                    next_steps.append(item)


    # =====================================================
    # Defaults
    # =====================================================

    if not strengths:

        strengths.append(
            "Demonstrated willingness to explain "
            "technical concepts."
        )


    if not gaps:

        gaps.append(
            "More depth can be added to technical "
            "explanations."
        )


    if not next_steps:

        next_steps.append(
            "Practice explaining technical concepts "
            "with practical examples."
        )


    # =====================================================
    # Average Score
    # =====================================================

    scores = [

        e.get(
            "score",
            0
        )

        for e in evaluations

        if isinstance(
            e,
            dict
        )

        and isinstance(
            e.get("score"),
            (int, float)
        )
    ]


    if scores:

        average_score = round(
            sum(scores) / len(scores),
            2
        )

    else:

        average_score = 0


    # =====================================================
    # Final Feedback
    # =====================================================

    return {

        "summary": (
            f"Interview completed after "
            f"{session['turn_count']} questions. "
            f"Average technical score: "
            f"{average_score}/10."
        ),

        "average_score": average_score,

        "strengths": list(
            dict.fromkeys(
                strengths
            )
        )[:5],

        "gaps": list(
            dict.fromkeys(
                gaps
            )
        )[:5],

        "next": list(
            dict.fromkeys(
                next_steps
            )
        )[:5]
    }