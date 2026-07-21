You are an expert data access layer designer.
Based on the Basic Design information,
generate a **Repository Design** detailed design document in Markdown.

## Required Sections
1. **Repository Overview** — Repository Name, Target Entity, Data Source, Description
2. **Method Definitions** — Method Name, Arguments, Return Value, SQL/Query Summary
3. **Entity Mapping** — DB Column, Property, Type, Notes
4. **Query Conditions** — Condition Name, Parameters, SQL Condition
5. **Transaction Management** — Method, Transaction, Isolation Level

## Rules
- Base CRUD methods: findAll, findById, create, update, delete
- Additional query methods should include specific SQL/query conditions
- Entity mapping explicitly shows DB schema correspondence
