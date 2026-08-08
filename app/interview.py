
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
# Helper: Candidate Name
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
# Helper: Candidate Role
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
        7: "topic-3",
        8: "system-design",
        9: "candidate-specific",
        10: "final"
    }

    return stages.get(
        question_number,
        "final"
    )


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

    if next_index < len(completed_topics):
        return completed_topics[next_index]

    return None


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
        # Get COMPLETE candidate profile
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
        # Get completed curriculum topics
        # =================================================

        completed_topics = get_completed_topics(
            full_candidate
        )

        if not completed_topics:

            return {
                "reply": (
                    "No completed curriculum topics "
                    "found for this candidate."
                ),
                "done": True
            }

        # =================================================
        # First topic
        # =================================================

        current_topic = completed_topics[0]

        # =================================================
        # Generate warm-up question
        # =================================================

        first_question = generate_response(

            candidate_name=candidate_name,

            role=role,

            topic=current_topic,

            question_type="warmup",

            asked_questions=[]
        )

        # =================================================
        # Create session
        # =================================================

        sessions[session_id] = {

            "sessionId": session_id,

            "candidate": full_candidate,

            "candidate_name": candidate_name,

            "role": role,

            "completed_topics": completed_topics,

            "current_topic": current_topic,

            "topic_index": 0,

            "current_question": first_question,

            "turns": [],

            "evaluations": [],

            "asked_topics": [],

            "asked_questions": [],

            "question_number": 1,

            "turn_count": 0
        }

        return {

            "reply": first_question,

            "done": False,

            "questionNumber": 1,

            "stage": "warm-up"
        }

    # =====================================================
    # EXISTING SESSION
    # =====================================================

    session = sessions[session_id]

    # =====================================================
    # If no message, return current question
    # =====================================================

    if not request.message:

        return {

            "reply": session["current_question"],

            "done": False,

            "questionNumber": session["question_number"],

            "stage": get_interview_stage(
                session["question_number"]
            )
        }

    # =====================================================
    # Current Question
    # =====================================================

    current_question = session[
        "current_question"
    ]

    candidate_answer = request.message

    # =====================================================
    # Evaluate Answer
    # =====================================================

    evaluation = evaluate_answer(

        current_question,

        candidate_answer
    )

    # =====================================================
    # Save Asked Question
    # =====================================================

    session["asked_questions"].append(
        current_question
    )

    # =====================================================
    # Save Current Topic
    # =====================================================

    current_topic = session.get(
        "current_topic"
    )

    if current_topic:

        if current_topic not in session["asked_topics"]:

            session["asked_topics"].append(
                current_topic
            )

    # =====================================================
    # Save Turn
    # =====================================================

    session["turns"].append({

        "question": current_question,

        "answer": candidate_answer,

        "evaluation": evaluation,

        "topic": current_topic
    })

    session["evaluations"].append(
        evaluation
    )

    session["turn_count"] += 1

    # =====================================================
    # Maximum Questions
    # =====================================================

    MAX_QUESTIONS = 10

    if session["turn_count"] >= MAX_QUESTIONS:

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
            "topic": session.get("current_topic")
        }

    # =====================================================
    # Next Question Number
    # =====================================================

    next_question_number = (
        session["question_number"] + 1
    )

    session["question_number"] = (
        next_question_number
    )

    # =====================================================
    # Determine Stage
    # =====================================================

    stage = get_interview_stage(
        next_question_number
    )

    # =====================================================
    # Decide whether to move to next topic
    # =====================================================

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

    next_topic = None
    

    # -----------------------------------------------------
    # If candidate is strong and this is a new-topic stage,
    # move to next curriculum topic.
    # -----------------------------------------------------
    
    
    # -----------------------------------------------------
    # Also move to next topic at new-topic stage when
    # there is no important weakness.
    # -----------------------------------------------------

    if ( stage in ["new-topic", "scenario", "system-design", "candidate-specific"] and understanding_level in ["good", "strong"] and not should_follow_up ):
        next_topic = get_next_topic(
            session
        )

    # =====================================================
    # If moving to next topic
    # =====================================================

    if next_topic:

        session["topic_index"] += 1

        session["current_topic"] = (
            next_topic
        )

        current_topic = next_topic

    # =====================================================
    # Generate Adaptive Question
    # =====================================================

    next_question = generate_adaptive_question(

        candidate_name=session[
            "candidate_name"
        ],

        role=session[
            "role"
        ],

        previous_question=current_question,

        previous_answer=candidate_answer,

        evaluation=evaluation,

        current_topic=session[
            "current_topic"
        ],

        stage=stage,

        asked_topics=session[
            "asked_topics"
        ],

        next_topic=next_topic
    )
    
    
    # ===================================================== # CLEAN AI RESPONSE # ===================================================== 
    if not next_question: 
        next_question = ( 
                         "Can you explain the main concept "
                         "of this topic in your own words?" 
                         ) 
    # Remove accidental prefixes 
    next_question = next_question.strip()
    if next_question.startswith("Question:"): 
        next_question = next_question[
            len("Question:"): ].strip() 
        
    if next_question.startswith( 
                                "Follow-up question:"
                                ): 
        next_question = next_question[
            len("Follow-up question:"): ].strip() 
    next_question = next_question.replace( "**",
                "" ).strip()

    # =====================================================
    # Save New Question
    # =====================================================

    session["current_question"] = (
        next_question
    )

    # =====================================================
    # Response
    # =====================================================

    return {

        "reply": next_question,

        "done": False,

        "questionNumber": next_question_number,

        "stage": stage,

        "topic": session[
            "current_topic"
        ]
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
        # Strength
        # =================================================

        score = evaluation.get(
            "score",
            0
        )

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

        for item in improvements:

            if item not in next_steps:

                next_steps.append(item)

    # =====================================================
    # Default Strength
    # =====================================================

    if not strengths:

        strengths.append(
            "Demonstrated willingness to explain "
            "technical concepts."
        )

    # =====================================================
    # Default Gaps
    # =====================================================

    if not gaps:

        gaps.append(
            "More depth can be added to technical "
            "explanations."
        )

    # =====================================================
    # Default Next Steps
    # =====================================================

    if not next_steps:

        next_steps.append(
            "Practice explaining technical concepts "
            "with practical examples."
        )

    # =====================================================
    # Average Score
    # =====================================================

    scores = [

        e.get("score", 0)

        for e in evaluations

        if isinstance(e, dict)

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
