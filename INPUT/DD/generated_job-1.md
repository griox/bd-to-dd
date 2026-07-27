# Detail Design Artifact

## Analysis Summary
Summary

## Business Flows
- Flow A

## Detail Design
### screen
- **01_UI_Design**: Subtotal confirmation layout with fixed header and action footer.
- **02_Components**: [{'componentName': 'NpBaseScreen', 'type': 'DS', 'role': 'Screen base component', 'notes': '-'}, {'componentName': 'NpHalfModal', 'type': 'DS', 'role': 'Workflow adjustment modal', 'notes': 'Shown when subtotal count > 0'}]
- **04_API_Integration**: [{'endpoint': '/api/subtotal', 'method': 'GET', 'timing': 'On screen load', 'responseHandling': 'Populate loading type and subtotal count'}]
- **06_State_Management**: [{'stateName': 'subtotalCount', 'type': 'String', 'initialValue': '0', 'updateTiming': 'Updated after subtotal API returns'}]

## Review
- Status: PASS