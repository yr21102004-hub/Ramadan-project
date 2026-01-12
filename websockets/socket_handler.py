"""
WebSocket Handler for Real-time Updates
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps

socketio = None

def init_socketio(app):
    """Initialize SocketIO"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    register_events()
    return socketio


def authenticated_only(f):
    """Decorator to require authentication for socket events"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Add authentication check here if needed
        return f(*args, **kwargs)
    return wrapped


def register_events():
    """Register all WebSocket events"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print('Client connected')
        emit('connection_response', {'status': 'connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected')
    
    @socketio.on('join_admin')
    @authenticated_only
    def handle_join_admin(data):
        """Admin joins admin room for real-time updates"""
        join_room('admin_room')
        emit('joined_admin', {'status': 'success'})
    
    @socketio.on('leave_admin')
    def handle_leave_admin():
        """Admin leaves admin room"""
        leave_room('admin_room')
    
    @socketio.on('update_project_percentage')
    @authenticated_only
    def handle_update_percentage(data):
        """Handle project percentage update"""
        username = data.get('username')
        percentage = data.get('percentage')
        
        # Broadcast to all admins
        socketio.emit('percentage_updated', {
            'username': username,
            'percentage': percentage
        }, room='admin_room')
    
    @socketio.on('new_message')
    def handle_new_message(data):
        """Handle new chat message"""
        # Broadcast to admin room
        socketio.emit('admin_notification', {
            'type': 'new_message',
            'data': data
        }, room='admin_room')
    
    @socketio.on('new_payment')
    def handle_new_payment(data):
        """Handle new payment notification"""
        # Broadcast to admin room
        socketio.emit('admin_notification', {
            'type': 'new_payment',
            'data': data
        }, room='admin_room')


def notify_admins(event_type, data):
    """Send notification to all admins"""
    if socketio:
        socketio.emit('admin_notification', {
            'type': event_type,
            'data': data
        }, room='admin_room')


def broadcast_percentage_update(username, percentage):
    """Broadcast percentage update to all connected clients"""
    if socketio:
        socketio.emit('percentage_updated', {
            'username': username,
            'percentage': percentage
        }, broadcast=True)
