def interview_prompt(candidate, role):

    return f"""
You are an expert AI interviewer.

Candidate Profile:
{candidate}

Interview Role:
{role}


Generate a personalized technical interview question.
Difficulty should match candidate skills.
"""