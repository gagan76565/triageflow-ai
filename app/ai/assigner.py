TEAM_MAPPING = {
    "Billing": "Finance Team",
    "Bug Report": "Engineering Team",
    "Account Access": "Support Team",
    "Feature Request": "Product Team",
    "How-To Question": "Customer Success",
    "General Inquiry": "Support Team"
}

def assign_team(category):

    return TEAM_MAPPING.get(
        category,
        "Support Team"
    )