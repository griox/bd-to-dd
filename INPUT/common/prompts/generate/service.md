You are an expert backend architect.
Based on the Basic Design information,
generate a **Service Design** detailed design document in Markdown.

## Required Sections
1. **Service Overview** — Service Name, Target Domain, Description
2. **Method Definitions** — Method Name, Arguments, Return Value, Processing Summary
3. **Dependent Services** — Service Name, Purpose
4. **API Integration** — Endpoint, Method, Request, Response
5. **Error Handling** — Error Type, Condition, Retry, Fallback
6. **Cache Strategy** — Target, TTL, Invalidation Condition

## Rules
- Service is a unit of business logic execution
- External API calls go through Bridge
- Error handling includes fallback strategies
