from ai.question_engine.models import Question, InputType, Option

def get_cough_pathway():
    return [
        Question(
            id="cough_duration",
            text="How long have you had this cough?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="duration",
            options=[
                Option(id="few_days", label="A few days"),
                Option(id="weeks", label="A few weeks"),
                Option(id="months", label="More than a month")
            ]
        )
    ]
