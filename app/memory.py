INTERVIEW_FLOW = [
    {
        "stage": "warmup",
        "type": "warmup",
        "count": 1
    },
    {
        "stage": "topic_basic",
        "type": "basic",
        "count": 1
    },
    {
        "stage": "topic_followup",
        "type": "followup",
        "count": 1
    },
    {
        "stage": "topic_deeper",
        "type": "deeper",
        "count": 1
    },
    {
        "stage": "topic_2",
        "type": "topic",
        "count": 1
    },
    {
        "stage": "scenario",
        "type": "scenario",
        "count": 1
    },
    {
        "stage": "topic_3",
        "type": "topic",
        "count": 1
    },
    {
        "stage": "system_design",
        "type": "system_design",
        "count": 1
    },
    {
        "stage": "candidate_specific",
        "type": "candidate_specific",
        "count": 1
    },
    {
        "stage": "final",
        "type": "final",
        "count": 1
    }
]


class InterviewMemory:

    def __init__(self):
        self.sessions = {}

    # =====================================================
    # CREATE SESSION
    # =====================================================

    def create_session(self, session_id, candidate):

        self.sessions[session_id] = {
            "sessionId": session_id,
            "candidate": candidate,

            "questions": [],
            "scores": [],

            # Topics that have already been used
            "asked_topics": [],

            # Interview flow
            "stage": "warmup",
            "topic_index": 0,
            "current_topic": None,
            "question_count": 0,

            # Current question
            "current_question": None
        }

    # =====================================================
    # ADD RESULT
    # =====================================================

    def add_result(
        self,
        session_id,
        question,
        answer,
        evaluation,
        topic=None
    ):

        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        session["questions"].append({
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "topic": topic
        })

        session["question_count"] += 1

        if isinstance(evaluation, dict):

            score = evaluation.get("score")

            if score is not None:
                session["scores"].append(score)

        # Add topic only once
        if topic and topic not in session["asked_topics"]:
            session["asked_topics"].append(topic)

    # =====================================================
    # GET SESSION
    # =====================================================

    def get_session(self, session_id):

        return self.sessions.get(session_id)

    # =====================================================
    # GET ASKED TOPICS
    # =====================================================

    def get_asked_topics(self, session_id):

        session = self.sessions.get(session_id)

        if not session:
            return []

        return session.get("asked_topics", [])

    # =====================================================
    # SESSION EXISTS
    # =====================================================

    def session_exists(self, session_id):

        return session_id in self.sessions

    # =====================================================
    # CURRENT STAGE
    # =====================================================

    def get_current_stage(self, session_id):

        session = self.sessions.get(session_id)

        if not session:
            return None

        return session.get("stage")

    # =====================================================
    # CURRENT TOPIC
    # =====================================================

    def get_current_topic(self, session_id):

        session = self.sessions.get(session_id)

        if not session:
            return None

        return session.get("current_topic")

    # =====================================================
    # SET CURRENT QUESTION
    # =====================================================

    def set_current_question(
        self,
        session_id,
        question,
        topic=None,
        stage=None
    ):

        session = self.sessions.get(session_id)

        if not session:
            return

        session["current_question"] = question

        if topic:
            session["current_topic"] = topic

        if stage:
            session["stage"] = stage

    # =====================================================
    # GET CURRENT QUESTION
    # =====================================================

    def get_current_question(self, session_id):

        session = self.sessions.get(session_id)

        if not session:
            return None

        return session.get("current_question")

    # =====================================================
    # MOVE TO NEXT FLOW STAGE
    # =====================================================

    def move_next_stage(self, session_id):

        session = self.sessions.get(session_id)

        if not session:
            return None

        current_stage = session.get("stage")

        current_index = 0

        for index, flow in enumerate(INTERVIEW_FLOW):

            if flow["stage"] == current_stage:
                current_index = index
                break

        next_index = current_index + 1

        if next_index >= len(INTERVIEW_FLOW):

            session["stage"] = "completed"

            return "completed"

        next_stage = INTERVIEW_FLOW[next_index]["stage"]

        session["stage"] = next_stage

        return next_stage

    # =====================================================
    # GET FLOW CONFIG
    # =====================================================

    def get_flow_config(self, session_id):

        session = self.sessions.get(session_id)

        if not session:
            return None

        stage = session.get("stage")

        for flow in INTERVIEW_FLOW:

            if flow["stage"] == stage:
                return flow

        return None