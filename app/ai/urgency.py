HIGH_PRIORITY_KEYWORDS = [
    "urgent",
    "asap",
    "immediately",
    "critical",
    "down",
    "cannot",
    "can't",
    "failed",
    "error"
]

def detect_urgency(text):

    text = text.lower()

    score = 0

    for keyword in HIGH_PRIORITY_KEYWORDS:

        if keyword in text:
            score += 1

    if score >= 4:
        return "Critical"

    elif score >= 2:
        return "High"

    elif score >= 1:
        return "Medium"

    return "Low"