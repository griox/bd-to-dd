import re


def clean_markdown_text(text: str) -> str:
    """Clean and compress markdown text to reduce unnecessary token usage.
    
    1. Removes HTML comments <!-- ... -->
    2. Strips trailing spaces on lines
    3. Normalizes 3+ consecutive newlines to 2 newlines
    """
    if not text:
        return ""
    # Strip HTML comments
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Strip trailing spaces per line
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    # Reduce 3+ consecutive newlines to 2 newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
