def search_docs(query):
    documents = [
        {"title": "password reset", "content": "To reset your password, go to the settings page..."},
        {"title": "Billing", "content": "For billing inquiries, please contact support."},
        {"title": "Account Deletion", "content": "contact support to delete your account."}
    ]
    results = []
    for doc in documents:
        if query.lower() in doc["title"].lower():
            results.append(doc)
    return results