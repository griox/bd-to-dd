# Coding Guidelines

General coding guidelines that apply across all DD types.

## Naming Conventions
- Class names: PascalCase
- Method names: camelCase
- Variable names: camelCase
- Constants: UPPER_SNAKE_CASE
- File names: kebab-case

## Architecture Layers
1. Screen → ViewModel → UseCase → Service → Repository
2. Each layer communicates only with adjacent layers
3. Bridge handles cross-cutting concerns

## Error Handling
- All API calls must have try-catch
- Show user-friendly error messages
- Log technical details for debugging
