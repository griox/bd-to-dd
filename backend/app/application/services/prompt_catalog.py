from app.domain.common_inputs.common_components import COMMON_COMPONENTS
from app.domain.common_inputs.planning_skills import (
    PLANNING_SKILLS,
)

STAGE_NAMES = [
    "Basic Design Analytics",
    "Get Sample Design",
    "Design Analysis Generation",
    "Detail Design Generation",
    "Detail Design Review",
]

SKILLS = PLANNING_SKILLS

DEFAULT_PROMPTS = {
    "basic_design_analytics": {
        "system": (
            "You are a senior BA. Return JSON with keys summary, modules, screens, "
            "entities, businessFlows, apiCandidates, externalInterfaces, uiSignals, assumptions."
        ),
        "user": (
            "Analyze the provided Basic Design and optional UI Design.\n"
            "Basic Design:\n{basic_design}\n\n"
            "UI Design:\n{ui_design}\n\n"
            "Similar Input References:\n{input_reference_examples}\n\n"
            "Common Input:\n{common_input}"
        ),
    },
    "design_analysis_generation": {
        "system": (
            "You are a senior solution architect. Return JSON with keys summary, scope, "
            "entities, businessFlows, apiCandidates, uiSignals, risks, assumptions."
        ),
        "user": (
            "Create a design analysis from the basic design analytics and sample references.\n"
            "Basic Design Analytics:\n{basic_design_analytics}\n\n"
            "Sample References:\n{sample_designs}\n\n"
            "Guidelines:\n{guidelines}"
        ),
    },
    "detail_design_generation": {
        "system": (
            "You are a senior developer. Return JSON with keys screen, api, batch. "
            "Each key must be an object whose values are section strings. "
            "Do not return a whole module as a single Markdown string. "
            "Respect provided templates, guidelines, references, and review feedback."
        ),
        "user": (
            "Generate a detailed design from the design analysis.\n"
            "Design Analysis:\n{design_analysis}\n\n"
            "Templates:\n{templates}\n\n"
            "Guidelines:\n{guidelines}\n\n"
            "Sample References:\n{sample_designs}\n\n"
            "Review Feedback:\n{review_feedback}"
        ),
    },
    "detail_design_review": {
        "system": (
            "You are a detail design reviewer. Return JSON with keys status, findings, strengths, nextActions. "
            "Status must be PASS or NG."
        ),
        "user": (
            "Review the generated detail design against the checklist.\n"
            "Design Analysis:\n{design_analysis}\n\n"
            "Detail Design:\n{detail_design}\n\n"
            "Checklist:\n{checklist}"
        ),
    },
}

PROMPTS = DEFAULT_PROMPTS
