TEMPLATES = {
    "basic_design": {
        "id": "basic-design",
        "artifact": "basic-design",
        "purpose": "Normalize user-provided BD into screen, API, and batch design inputs.",
        "modules": {
            "01_Screen": {
                "artifact": "basic-design",
                "description": "Screen/page level scope, actors, UI flow, and UI-driven data needs.",
                "requiredSections": [
                    "Screen purpose",
                    "Actors",
                    "Screen flow",
                    "Input/output data",
                    "Validation and error behavior",
                ],
                "schemaPath": "basicDesign.screen",
            },
            "02_API": {
                "artifact": "basic-design",
                "description": "API level scope, external interfaces, and business capabilities.",
                "requiredSections": [
                    "API purpose",
                    "Endpoint candidates",
                    "Request/response overview",
                    "Auth and error policy",
                    "Related entities",
                ],
                "schemaPath": "basicDesign.api",
            },
            "03_Batch": {
                "artifact": "basic-design",
                "description": "Batch or background processing scope and operational constraints.",
                "requiredSections": [
                    "Job purpose",
                    "Trigger and schedule",
                    "Input/output data",
                    "Retry and failure policy",
                    "Affected entities",
                ],
                "schemaPath": "basicDesign.batch",
            },
        },
    },
    "detail_design": {
        "id": "detail-design",
        "artifact": "detail-design",
        "purpose": "Generate implementation-ready DD artifacts for screen, API, and batch modules.",
        "modules": {
            "01_Screen": {
                "artifact": "detail-design",
                "schemaPath": "detailDesign.screen",
                "reviewChecklistIds": [
                    "DD-SCREEN-UI",
                    "DD-SCREEN-COMPONENTS",
                    "DD-SCREEN-DATA",
                    "DD-SCREEN-API",
                    "DD-SCREEN-LOGIC",
                    "DD-SCREEN-STATE",
                ],
                "sections": [
                    {
                        "id": "01_UI_Design",
                        "title": "UI Design",
                        "required": True,
                        "description": "Screen layout, user actions, navigation, and UI assumptions.",
                        "expectedContent": ["screen states", "actions", "validation display"],
                    },
                    {
                        "id": "02_Components",
                        "title": "Components",
                        "required": True,
                        "description": "Reusable UI and domain components used by the screen.",
                        "expectedContent": ["component list", "props/data", "events"],
                    },
                    {
                        "id": "03_Data_Models",
                        "title": "Data Models",
                        "required": True,
                        "description": "Entities, fields, and client-side view models required by the screen.",
                        "expectedContent": ["entities", "fields", "validation constraints"],
                    },
                    {
                        "id": "04_API_Integration",
                        "title": "API Integration",
                        "required": True,
                        "description": "Backend APIs, request data, response data, and error handling.",
                        "expectedContent": ["endpoints", "request/response", "error mapping"],
                    },
                    {
                        "id": "05_Business_Logic",
                        "title": "Business Logic",
                        "required": True,
                        "description": "User-facing rules, branching, and workflow logic.",
                        "expectedContent": ["rules", "conditions", "edge cases"],
                    },
                    {
                        "id": "06_State_Management",
                        "title": "State Management",
                        "required": True,
                        "description": "UI state, loading/error state, and data refresh behavior.",
                        "expectedContent": ["state fields", "transitions", "reset behavior"],
                    },
                ],
            },
            "02_API": {
                "artifact": "detail-design",
                "schemaPath": "detailDesign.api",
                "reviewChecklistIds": [
                    "DD-API-CONTRACT",
                    "DD-API-LOGIC",
                    "DD-API-DATA",
                ],
                "sections": [
                    {
                        "id": "01_Contract",
                        "title": "Contract",
                        "required": True,
                        "description": "Method, path, headers, query/body schema, responses, and errors.",
                        "expectedContent": ["method/path", "request schema", "response schema", "error codes"],
                    },
                    {
                        "id": "02_Business_Logic",
                        "title": "Business Logic",
                        "required": True,
                        "description": "Service-level rules, branch conditions, idempotency, and state changes.",
                        "expectedContent": ["processing steps", "conditions", "side effects"],
                    },
                    {
                        "id": "03_Data_Access",
                        "title": "Data Access",
                        "required": True,
                        "description": "Tables, query patterns, indexes, and transaction boundaries.",
                        "expectedContent": ["tables", "queries", "indexes", "transaction notes"],
                    },
                ],
            },
            "03_Batch": {
                "artifact": "detail-design",
                "schemaPath": "detailDesign.batch",
                "reviewChecklistIds": [
                    "DD-BATCH-JOB",
                    "DD-BATCH-LOGIC",
                    "DD-BATCH-DATA",
                ],
                "sections": [
                    {
                        "id": "01_Job_Definition",
                        "title": "Job Definition",
                        "required": True,
                        "description": "Job trigger, schedule, owner, timeout, and retry policy.",
                        "expectedContent": ["trigger", "schedule", "timeout", "retry"],
                    },
                    {
                        "id": "02_Processing_Logic",
                        "title": "Processing Logic",
                        "required": True,
                        "description": "Step-by-step processing, branching, failure behavior, and observability.",
                        "expectedContent": ["steps", "failure handling", "logs/metrics"],
                    },
                    {
                        "id": "03_Data_Access",
                        "title": "Data Access",
                        "required": True,
                        "description": "Read/write datasets, checkpoints, and idempotency keys.",
                        "expectedContent": ["source data", "target data", "checkpoint/idempotency"],
                    },
                ],
            },
        },
    },
}

