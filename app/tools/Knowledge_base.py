# tools/knowledge_base.py
KNOWLEDGE_BASE = {
    "password reset": {
        "keywords": ["password", "reset", "forgot password", "change password"],
        "response": "To reset your password:\n1. Go to Settings > Security\n2. Click 'Reset Password'\n3. Check your email for the reset link\n4. Follow the instructions in the email"
    },
    "otp issues": {
        "keywords": ["otp", "verification code", "2fa", "two factor"],
        "response": "If you're not receiving OTP:\n1. Check your spam/junk folder\n2. Wait 2-3 minutes for delivery\n3. Ensure your phone number is correct\n\nStill not working? I can create a support ticket for you."
    },
    "billing": {
        "keywords": ["billing", "invoice", "payment", "charge"],
        "response": "For billing inquiries, please contact our billing team at billing@intercloud.com or call 1-800-BILLING"
    }
}

def search_knowledge_base(query):
    """Search knowledge base before using other tools"""
    query_lower = query.lower()
    
    for topic, data in KNOWLEDGE_BASE.items():
        for keyword in data["keywords"]:
            if keyword in query_lower:
                return {"found": True, "response": data["response"]}
    
    return {"found": False, "response": None}