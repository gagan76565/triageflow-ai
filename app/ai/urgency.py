CRITICAL_KEYWORDS = [
    "critical",
    "production down",
    "server down",
    "cannot login",
    "system down",
    "urgent"
]

HIGH_KEYWORDS = [
    "failed",
    "error",
    "asap",
    "immediately",
    "not working"
]

MEDIUM_KEYWORDS = [
    "slow",
    "issue",
    "problem"
]

def detect_urgency(text):

    text = text.lower()

    # Critical
    for keyword in CRITICAL_KEYWORDS:

        if keyword in text:
            return "Critical"

    # High
    for keyword in HIGH_KEYWORDS:

        if keyword in text:
            return "High"

    # Medium
    for keyword in MEDIUM_KEYWORDS:

        if keyword in text:
            return "Medium"

    return "Low"