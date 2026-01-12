from flask import Blueprint, request, jsonify
from flask_login import current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from services.ai_service import AIService
from models import SecurityLogModel

chat_bp = Blueprint('chat', __name__)
ai_service = AIService()
security_model = SecurityLogModel()

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        # Determine unique user_id
        if current_user.is_authenticated:
            user_id = current_user.username
            user_name = current_user.full_name if current_user.full_name else current_user.username
        else:
            user_id = data.get('user_id', 'anonymous')
            user_name = "Guest"
        
        # Recognize Contact Request logging (Side effect, maybe belongs in service?)
        # Putting it here or service. It's security logging, so controller is fine or service.
        # Let's keep specific logging in controller for now or move to service if it grows.
        is_contact_req = any(kw in message.lower() for kw in ["تواصل", "أكلم حد", "رقم", "اتصل", "contact", "call", "phone"])
        if is_contact_req:
            security_model.create("Contact Info Requested", f"User {user_name} ({user_id}) requested contact details. Message: {message}", severity="low")

        response_text = ai_service.process_message(user_id, user_name, message)
        
        return jsonify({'response': response_text})
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500
