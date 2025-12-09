import uuid

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.agents.main_agent import orchestrate_response
from app.models.chat import ChatMessage, User
from app.auth.jwt_auth import (
    generate_access_token,
    verify_token,
    token_required,
    get_token_from_header
)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 400

    conversation_id = str(uuid.uuid4())
    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        default_conversation_id=conversation_id,
    )
    db.session.add(user)
    db.session.commit()

    # Generate access token
    access_token = generate_access_token(user.id, user.email)

    return jsonify(
        {
            "message": "registered",
            "conversation_id": conversation_id,
            "user_id": user.id,
            "access_token": access_token,
        }
    ), 201


@chat_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    conversation_id = user.default_conversation_id or str(uuid.uuid4())
    if user.default_conversation_id is None:
        user.default_conversation_id = conversation_id
        db.session.commit()

    # Generate access token
    access_token = generate_access_token(user.id, user.email)

    return jsonify(
        {
            "message": "logged in",
            "conversation_id": conversation_id,
            "user_id": user.id,
            "access_token": access_token,
        }
    ), 200


@chat_bp.route('/messages', methods=['POST'])
def get_messages():
    data = request.get_json() or {}
    user_message = data.get('message')
    conversation_id = data.get('conversation_id')
    user_id = data.get("user_id")

    # Try to get user_id from JWT token if not provided in body
    if not user_id:
        token = get_token_from_header()
        if token:
            payload, error = verify_token(token, token_type='access')
            if not error:
                user_id = payload.get('user_id')

    # If a user_id is provided (from body or token), prefer their default conversation id
    if user_id and not conversation_id:
        user = User.query.get(user_id)
        if user and user.default_conversation_id:
            conversation_id = user.default_conversation_id

    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # Fetch prior context for this conversation
    previous_messages = (
        ChatMessage.query.filter_by(conversation_id=conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    # InterCloud company context
    intercloud_context = """
InterCloud (https://intercloud.com.bd/) is a leading IT-enabled technology brand of Bangladesh, part of Brilliant Group. 

Our Products & Services:
1. Ants Shop - Online shopping hub bringing major national brands into a single platform with best prices, easy ordering, 7-day return policy, quick delivery, and cash on delivery.

2. Brilliant Cloud - First public cloud service provider in Bangladesh offering:
   - IaaS/VM Instance, BaaS, STaaS, S3, LaaS, MaaS
   - Cost savings, no power headaches, no physical servers
   - Fast disaster recovery, redundancy, scalability

3. Brilliant Telephony - Nationwide IP Telephony Service Provider (IPTSP) with:
   - App-based PBX, Hosted PBX, Business Telephony
   - Audio Conference, Toll Free Service, Shortcode

4. Brilliant PBX - First app-based PBX solution in Bangladesh with:
   - Personal IVR Setup, Custom Portal to Manage
   - 0 Upfront Cost, Roam Anywhere
   - Free App to App Calls, 24/7 Customer Support, Easy Configuration

5. SMS Solutions - Commercial enterprise SMS with:
   - Call Back Option, Push Pull Service
   - Masking, Non-masking, Return SMS, QoS Ensured

6. Internet & Data - Global telecommunications leadership:
   - Business Internet, Domestic Data Connectivity
   - Multi Protocol Label Switching (MPLS)
   - Direct Internet Access, Internet Private Leased Circuit (IPLC)

7. Brilliant Connect - Communication app for friends and family:
   - App to App Calling, Video Calling, Text Messaging
   - Photo and Video Sharing, Location Sharing
   - Security by Encryption

Sister Companies: NovoTel, NovoCom, Novoair, Tusuka
"""

    history = [
        {
            "role": "system",
            "content": (
                f"You are a smart AI support agent for InterCloud company (https://intercloud.com.bd/).\n\n"
                f"{intercloud_context}\n\n"
                "IMPORTANT RULES:\n"
                "1. Always maintain awareness of InterCloud's products and services in every conversation.\n"
                "2. When users greet you or express they need help, ask what issue they're experiencing.\n"
                "3. Once you understand their issue clearly, use the appropriate tool:\n\n"
                "- To search documentation: respond ONLY with '__Search__: <query>'\n"
                "- To summarize text: respond ONLY with '__SUMMARY__: <text>'\n"
                "- To create a support ticket: respond ONLY with '__CREATE_TICKET__: <issue_description>'\n\n"
                "4. Always gather enough information before creating a ticket. The issue description should be clear and specific.\n"
                "5. After responding to the user, ALWAYS end your message with a relevant question about InterCloud's services or products that could help them further. "
                "This question should be natural and related to the conversation context, even if the conversation went off-topic.\n"
                "6. When creating tickets, always provide the direct ticket creation link: https://app-support.brilliant.com.bd/create-ticket"
                "7. If they ask for Ants Shop website, provide this link: https://ants.brilliant.com.bd/"
            ),
        }
    ]

    history.extend(
        {"role": msg.role, "content": msg.content} for msg in previous_messages
    )
    history.append({"role": "user", "content": user_message})

    reply = orchestrate_response(history)

    # Persist the new turn for future context
    db.session.add(
        ChatMessage(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )
    )
    db.session.add(
        ChatMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=reply,
        )
    )
    db.session.commit()

    return jsonify({"reply": reply, "conversation_id": conversation_id})
