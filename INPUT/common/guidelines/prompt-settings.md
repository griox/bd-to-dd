# Prompt Settings

Default prompt configuration for DD generation.

## System Prompt Structure
```
[Role] You are a Detailed Design document generator.
[Context] Given Basic Design input + UI information + patterns from knowledge base.
[Task] Generate a {dd_type} document following the template structure.
[Format] Output in Markdown following the template exactly.
[Language] Use Japanese technical terms as specified.
```

## Temperature Settings
| DD Type | Temperature | Reason |
|---------|------------|--------|
| Screen設計 | 0.2 | Highly structured, low creativity |
| ViewModel設計 | 0.2 | Deterministic mapping |
| UseCase設計 | 0.3 | Some logic inference needed |
| Service設計 | 0.3 | API design needs some flexibility |
| Repository設計 | 0.2 | Data access is formulaic |
| Composable設計 | 0.3 | Pattern recognition |
| Bridge設計 | 0.3 | Cross-cutting logic |
| Resource設計 | 0.2 | Constants/enums are fixed |
