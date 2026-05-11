from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.metrics.pairwise import cosine_similarity


def find_similar_tickets(
    new_ticket,
    existing_tickets
):

    if not existing_tickets:
        return []

    texts = [new_ticket] + existing_tickets

    vectorizer = TfidfVectorizer()

    vectors = vectorizer.fit_transform(texts)

    similarities = cosine_similarity(
        vectors[0:1],
        vectors[1:]
    )[0]

    results = []

    for i, score in enumerate(similarities):

        if score > 0.3:

            results.append({
                "ticket": existing_tickets[i],
                "similarity": round(score * 100, 2)
            })

    return results