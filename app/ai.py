from app.prompts import interview_prompt


def generate_response(candidate,role):

    prompt = interview_prompt(
        candidate,
        role
    )

    # abhi testing ke liye
    return f"Generate interview question for {role} based on {candidate}"