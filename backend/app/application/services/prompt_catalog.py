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
            "You are a senior developer. Return JSON where each key represents a logical file (e.g., '01_Screen設計', '02_ViewModel設計'). "
            "The value for each key must be an object with a single key 'content'. "
            "The value of 'content' must be the ENTIRE detailed design as a single Markdown string for that specific file. "
            "The Markdown MUST exactly match the structure, tables, and headings of the provided Templates. "
            "Do NOT split the document into generic JSON keys. "
            "Respect provided guidelines, references, and review feedback."
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
    "detail_design_ui_generation": {
        "system": (
            "You are a senior UI/UX developer. Return JSON where key is '01_Screen設計'. "
            "The value must be an object with a single key 'content'. "
            "The value of 'content' must be the detailed UI Design as a Markdown string covering layout, composable components, and user interaction events. "
            "Respect provided templates, guidelines, and review feedback."
        ),
        "user": (
            "Generate the Screen UI Detailed Design (01_Screen設計).\n"
            "Design Analysis:\n{design_analysis}\n\n"
            "Templates:\n{templates}\n\n"
            "Guidelines:\n{guidelines}\n\n"
            "Sample References:\n{sample_designs}\n\n"
            "Review Feedback:\n{review_feedback}"
        ),
    },
    "detail_design_logic_generation": {
        "system": (
            "You are a senior backend/logic developer. Return JSON where key is '02_ViewModel設計'. "
            "The value must be an object with a single key 'content'. "
            "The value of 'content' must be the detailed ViewModel/Logic Design as a Markdown string covering State Management, API Integration, and Business Logic rules. "
            "Respect provided templates, guidelines, and review feedback."
        ),
        "user": (
            "Generate the ViewModel & Logic Detailed Design (02_ViewModel設計).\n"
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
