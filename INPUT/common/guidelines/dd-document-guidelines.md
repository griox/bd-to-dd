# DD Document Guidelines

Rules for writing consistent Detailed Design documents.

## Required Sections (all DD types)
1. 概要 (Overview)
2. 依存関係 (Dependencies)
3. 詳細設計 (Detailed Specification)
4. 例外処理 (Exception Handling)

## Naming Rules
- Use Japanese technical terms as defined in templates
- Reference other DD types by their formal name (e.g., Screen設計, ViewModel設計)
- All cross-references must be bidirectional

## Quality Criteria
- Developer can implement directly from the DD
- No vague descriptions — all logic must be specific
- Every field has: name, type, description
- Every method has: parameters, return type, description
