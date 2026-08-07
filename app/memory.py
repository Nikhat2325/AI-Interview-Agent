class InterviewMemory:

    def __init__(self):
        self.sessions = {}

    def create_session(self, candidate):
        self.sessions[candidate] = {
            "candidate": candidate,
            "questions": [],
            "scores": [],
            "feedback": []
        }

    def add_result(self, candidate, question, answer, evaluation):

        if candidate not in self.sessions:
            self.create_session(candidate)

        self.sessions[candidate]["questions"].append({
            "question": question,
            "answer": answer,
            "evaluation": evaluation
        })

        if isinstance(evaluation, dict):
            if "score" in evaluation:
                self.sessions[candidate]["scores"].append(
                    evaluation["score"]
                )

    def get_session(self, candidate):
        return self.sessions.get(candidate)