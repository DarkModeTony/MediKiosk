from ai.question_engine.models import Question, InputType, Option

def get_vomiting_pathway():
    return [
        Question(
            id="vomiting_frequency",
            text="How many times have you vomited?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="frequency",
            options=[
                Option(id="once_twice", label="1-2 times"),
                Option(id="several", label="3-5 times"),
                Option(id="many", label="More than 5 times")
            ]
        )
    ]
