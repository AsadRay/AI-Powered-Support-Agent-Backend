def summarize_text(text):
    if len(text) <= 120:
        return text
    return text[:120] + '...'
