from groq import Groq
import os
from dotenv import load_dotenv

from app.tools.summarizer import summarize_text
from app.tools.ticket_creator import create_ticket, TICKET_CREATION_LINK
from app.tools.doc_search import search_docs
from app.tools.Knowledge_base import search_knowledge_base
load_dotenv()

client = Groq(api_key=os.getenv('Groq_API_Key'))

# InterCloud services for generating relevant questions
INTERCLOUD_SERVICES = [
    "Ants Shop online shopping",
    "Brilliant Cloud services",
    "Telephony and PBX solutions",
    "SMS services",
    "Business Internet and Data connectivity",
    "Brilliant Connect app"
]


def _is_otp_issue(message: str) -> bool:
    """
    Lightweight check to determine if the user is reporting an OTP-related issue.
    """
    normalized = message.lower()
    keywords = [
        "otp",
        "one time password",
        "one-time password",
        "verification code",
        "auth code",
        "login code",
    ]
    return any(keyword in normalized for keyword in keywords)


def _truncate_history(history, max_messages=15):
    """
    Truncate conversation history to keep within token limits.
    Always keeps system message and the most recent messages.
    Groq limit is 6000 tokens, so we keep last 15 messages to be safe.
    """
    if len(history) <= max_messages:
        return history
    
    # Always keep the system message (first message)
    system_message = history[0]
    
    # Keep the most recent messages (excluding system message)
    # This ensures we keep the latest context while staying within token limits
    recent_messages = history[-(max_messages - 1):]
    
    # Combine system message with recent messages
    return [system_message] + recent_messages


def generate_response(messages):
    # Truncate history to prevent token limit errors
    messages = _truncate_history(messages, max_messages=20)
    
    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return chat.choices[0].message.content

def _add_intercloud_question(response: str) -> str:
    """
    Ensures the response ends with a relevant InterCloud question.
    If it already ends with a question, returns as is. Otherwise adds one.
    """
    response = response.strip()
    
    # Check if response already ends with a question mark
    if response.endswith('?'):
        # Check if it's about InterCloud services
        response_lower = response.lower()
        intercloud_keywords = [
            "intercloud", "ants shop", "cloud", "telephony", "pbx", 
            "sms", "internet", "data", "connect", "brilliant"
        ]
        if any(keyword in response_lower for keyword in intercloud_keywords):
            return response
    
    # Add a relevant InterCloud question
    question_prompt = (
        f"Based on this conversation, generate a single, natural question about InterCloud's services "
        f"(Ants Shop, Cloud, Telephony, PBX, SMS, Internet/Data, or Connect app) that could help the user. "
        f"Make it conversational and relevant. Return ONLY the question, nothing else."
    )
    
    question_messages = [
        {"role": "system", "content": "You are a helpful assistant that generates relevant questions about InterCloud services."},
        {"role": "user", "content": f"Conversation context: {response}\n\n{question_prompt}"}
    ]
    
    try:
        question = generate_response(question_messages).strip()
        if question and not question.endswith('?'):
            question += "?"
        return f"{response}\n\n{question}"
    except:
        # Fallback question if generation fails
        return f"{response}\n\nWould you like to learn more about any of InterCloud's services, such as our Cloud solutions, Telephony, or Ants Shop?"

def orchestrate_response(history):
    user_message = history[-1]["content"]

    # Auto-handle OTP issues: create a ticket using the first prompt and ask for the phone number.
    if _is_otp_issue(user_message):
        ticket = create_ticket(user_message)
        response = (
            f"I've opened ticket {ticket['ticket_id']} for your OTP issue based on your first message. "
            f"Please share the phone number linked to your account so I can add it to the ticket.\n\n"
            f"You can also create or manage tickets directly at: {TICKET_CREATION_LINK}"
        )
        return _add_intercloud_question(response)

    # First, check knowledge base
    kb_result = search_knowledge_base(user_message)
    
    if kb_result["found"]:
        # Return direct answer from knowledge base
        return _add_intercloud_question(kb_result["response"])
    
    # If not in KB, proceed with normal LLM flow
    response = generate_response(history)
    
    if "__Search__:" in response:
        query = response.replace("__Search__:", "").strip()
        tool_results = search_docs(query)
        history.append({"role": "assistant", "content": str(tool_results)})
        response = generate_response(history)
        return _add_intercloud_question(response)
    
    if "__SUMMARY__:" in response:
        text = response.replace("__SUMMARY__:", "").strip()
        tool_results = summarize_text(text)
        history.append({"role": "assistant", "content": tool_results})
        response = generate_response(history)
        return _add_intercloud_question(response)
    
    if "__CREATE_TICKET__:" in response:
        issue = response.replace("__CREATE_TICKET__:", "").strip()
        tool_results = create_ticket(issue)
        ticket_info = f"Ticket {tool_results['ticket_id']} has been created. You can create or manage tickets at: {TICKET_CREATION_LINK}"
        history.append({"role": "assistant", "content": f"{tool_results}\n{ticket_info}"})
        response = generate_response(history)
        # Ensure ticket link is included in final response
        if TICKET_CREATION_LINK not in response:
            response += f"\n\nCreate or manage tickets at: {TICKET_CREATION_LINK}"
        return _add_intercloud_question(response)
    
    return _add_intercloud_question(response)