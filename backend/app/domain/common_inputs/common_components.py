COMMON_COMPONENTS = [
    {
        "id": "api_error_envelope",
        "name": "API Error Envelope",
        "appliesTo": ["api", "screen"],
        "contract": {
            "shape": {"data": None, "meta": {}, "error": {"code": "string", "message": "string"}},
            "requiredCodes": ["VALIDATION_ERROR", "NOT_FOUND", "CONFLICT", "SERVER_ERROR"],
        },
        "ddUsage": "Use in API Contract and UI API Integration sections for consistent error handling.",
    },
    {
        "id": "pagination",
        "name": "Pagination",
        "appliesTo": ["api", "screen"],
        "contract": {
            "query": ["page", "limit"],
            "meta": ["total", "page", "limit", "last_page"],
            "limitMax": 100,
        },
        "ddUsage": "Use for list endpoints and screen tables where result count can grow.",
    },
    {
        "id": "audit_log",
        "name": "Audit Log",
        "appliesTo": ["api", "batch"],
        "contract": {
            "fields": ["actor_id", "action", "target_type", "target_id", "timestamp", "metadata"],
            "piiPolicy": "Do not store raw secrets or sensitive payloads.",
        },
        "ddUsage": "Use in Business Logic and Data Access sections for state-changing operations.",
    },
    {
        "id": "file_upload",
        "name": "File Upload",
        "appliesTo": ["screen", "api"],
        "contract": {
            "acceptedTypes": ["text/markdown", "text/plain"],
            "maxSizeMb": 5,
            "failureModes": ["unsupported_type", "too_large", "empty_file"],
        },
        "ddUsage": "Use when DD includes upload or ingest screens/APIs.",
    },
    {
        "id": "form_validation",
        "name": "Form Validation",
        "appliesTo": ["screen", "api"],
        "contract": {
            "levels": ["client_required_fields", "server_schema_validation", "business_rule_validation"],
            "errorDisplay": "field-level when possible, form-level for workflow errors",
        },
        "ddUsage": "Use in UI Design, Business Logic, and API Contract sections.",
    },
    {
        "id": "job_status",
        "name": "Async Job Status",
        "appliesTo": ["screen", "api", "batch"],
        "contract": {
            "states": [
                "uploaded",
                "analyzing",
                "retrieving_samples",
                "generating_analysis",
                "generating_dd",
                "validating",
                "needs_manual_review",
                "completed",
                "failed",
            ],
            "requiredFields": ["jobId", "status", "updatedAt"],
        },
        "ddUsage": "Use in generation APIs, background processing, and result screens.",
    },
    {
        "id": "state_management",
        "name": "Screen State Management",
        "appliesTo": ["screen"],
        "contract": {
            "states": ["idle", "uploading", "generating", "reviewing", "export_ready", "failed"],
            "requiredData": ["projectId", "jobId", "inputs", "pipeline", "review", "artifacts"],
        },
        "ddUsage": "Use in State Management sections for result and review screens.",
    },
]

