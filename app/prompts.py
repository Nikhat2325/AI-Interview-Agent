def interview_prompt(candidate, role):

    prompt = f"""
You are an AI Interview Agent.

Candidate Name:
{candidate}

Job Role:
{role}

Generate a technical interview question.
Question should match candidate skills and role.
"""

    return prompt