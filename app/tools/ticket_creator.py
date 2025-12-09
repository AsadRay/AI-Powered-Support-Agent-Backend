import random

TICKET_CREATION_LINK = "https://app-support.brilliant.com.bd/create-ticket"

def create_ticket(issue):
    ticket_id = f"TICKET-{random.randint(1000, 9999)}"
    return {
        "ticket_id": ticket_id,
        "issue": issue,
        "status": "Created",
        "ticket_link": TICKET_CREATION_LINK
    }