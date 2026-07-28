# Prompt Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce LLM generation latency and token costs by stripping unnecessary context from `basic_design_analytics` and clipping large RAG samples.

**Architecture:** 
1. `basic_design_analytics` currently receives the entire raw `common_input` dictionary, which Langchain stringifies into a massive blob containing irrelevant `commonComponents` and `templates`. We will introduce a new formatter `_format_initial_analysis_guidance` to strip this out.
2. `sample_designs` (RAG results) injects full Detail Design documents into later phases. We will truncate these references to a reasonable character limit (e.g., 5000 chars per reference) to prevent context bloat.

**Tech Stack:** Python, Langchain

## Global Constraints

- No changes to existing AI model versions or parameters.
- Must not break the existing payload schema expected by Langchain chains.
- Keep tests passing.

---

### Task 1: Optimize basic_design_analytics Prompt

**Files:**
- Modify: `backend/app/application/use_cases/generate_detail_design.py`

**Interfaces:**
- Consumes: `context["common_input"]`
- Produces: A formatted string containing ONLY guidelines and planning skills, excluding `commonComponents` and `imageReferences`.

- [ ] **Step 1: Create `_format_initial_analysis_guidance` helper**

```python
    def _format_initial_analysis_guidance(self, common_input: Dict[str, Any]) -> str:
        guidance = ["Guidelines:"]
        for item in common_input.get("guidelines", []):
            if isinstance(item, dict):
                guidance.append(
                    f"- [{item.get('id')}] {item.get('stage')} "
                    f"({item.get('severity')}): {item.get('rule')}"
                )
            else:
                guidance.append(f"- {item}")
        guidance.append("")
        
        guidance.append("Planning skills:")
        for key, skill in common_input.get("skills", {}).items():
            guidance.append(f"- {key} ({skill['stage']}): {skill['purpose']}")
        
        return "\n".join(guidance)
```

- [ ] **Step 2: Update `basic_design_analytics_chain.invoke` payload**

Update `generate_detail_design.py` around line 898 where `common_input` is passed:

```python
                    "ui_design": "\n\n".join(context["ui_design_docs"]),
                    "update_status": context["update_status"],
                    "common_input": self._format_initial_analysis_guidance(context["common_input"]),
                    "input_reference_examples": context["input_reference_examples"],
```

- [ ] **Step 3: Run tests to verify it passes**

Run: `python3 -m unittest discover -s backend/tests -q`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/app/application/use_cases/generate_detail_design.py
git commit -m "perf(llm): optimize common_input prompt for basic_design_analytics"
```

---

### Task 2: Truncate RAG Sample Designs

**Files:**
- Modify: `backend/app/application/services/input_reference_service.py`

**Interfaces:**
- Consumes: `references: List[Dict[str, Any]]` in `_format_references`
- Produces: Truncated markdown strings (max 5000 chars per reference)

- [ ] **Step 1: Update `_format_references` method**

Modify `_format_references` in `input_reference_service.py` to truncate long content:

```python
    def _format_references(self, references: List[Dict[str, Any]]) -> str:
        lines = [
            "REFERENCE INPUT EXAMPLES",
            "========================",
            "",
        ]
        MAX_CHARS_PER_REF = 5000
        for i, ref in enumerate(references, 1):
            source = ref.get("source", {})
            content = ref.get("content", "")
            
            # Truncate content to prevent context bloat
            if len(content) > MAX_CHARS_PER_REF:
                content = content[:MAX_CHARS_PER_REF] + "\n...[TRUNCATED TO SAVE CONTEXT]..."
                
            lines.extend(
                [
                    f"Example {i}:",
                    f"Source: {source.get('filename', 'Unknown')} ({source.get('type', 'unknown')})",
                    "Context:",
                    ref.get("context", "N/A"),
                    "Content:",
                    content,
                    "-" * 40,
                    "",
                ]
            )
        return "\n".join(lines)
```

- [ ] **Step 2: Run tests to verify it passes**

Run: `python3 -m unittest discover -s backend/tests -q`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/app/application/services/input_reference_service.py
git commit -m "perf(rag): truncate large sample designs to prevent prompt bloat"
```
