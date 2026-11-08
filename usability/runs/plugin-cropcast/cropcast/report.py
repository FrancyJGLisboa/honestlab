def markdown_table(rows, headers):
    """Render rows (list of lists) as a markdown table for the weekly note."""
    line = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join([line, sep] + body)
# minor
