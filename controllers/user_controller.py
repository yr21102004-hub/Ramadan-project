from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import UserModel
from websockets import notify_admins, broadcast_percentage_update

user_bp = Blueprint('user', __name__)
bcrypt = Bcrypt()
user_model = UserModel()

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        email = request.form.get('email', '')
        project_description = request.form.get('project_description', 'لا يوجد وصف للمشروع')
        
        # Handle profile image upload
        profile_image_path = None
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                unique_filename = f"{username}_{timestamp}.{file_extension}"
                
                upload_folder = os.path.join('static', 'user_images')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                profile_image_path = f"user_images/{unique_filename}"
        
        # Check if user exists
        if user_model.get_by_username(username):
            flash('اسم المستخدم مسجل بالفعل')
            return redirect(url_for('user.register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # First user is admin
        all_users = user_model.get_all()
        role = 'admin' if len(all_users) == 0 else 'user'
            
        # Create user
        user_model.create({
            'username': username,
            'password': hashed_password,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'role': role,
            'profile_image': profile_image_path,
            'project_location': 'غير محدد',
            'project_description': project_description,
            'project_percentage': 0
        })
        
        # Notify admins
        notify_admins('new_user', {
            'username': username,
            'full_name': full_name
        })
        
        return redirect(url_for('login')) # Login is likely global
        
    return render_template('register.html')


@user_bp.route('/user/<username>')
def profile(username):
    """Get user profile"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.role != 'admin' and current_user.username != username:
        return "Access Denied", 403
        
    user_data = user_model.get_by_username(username)
    if not user_data:
        return "User not found", 404
        
    user_obj = {
        'full_name': user_data.get('full_name'),
        'username': user_data.get('username'),
        'email': user_data.get('email', 'لا يوجد'),
        'phone': user_data.get('phone'),
        'profile_image': user_data.get('profile_image'),
        'project_location': user_data.get('project_location', 'غير محدد'),
        'project_description': user_data.get('project_description', 'لا يوجد وصف'),
        'project_percentage': user_data.get('project_percentage', 0),
        'created_at': user_data.get('created_at')
    }
    return render_template('user_dashboard.html', user=user_obj)


@user_bp.route('/admin/update_project_percentage', methods=['POST'])
def update_percentage():
    """Update user project percentage"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access Denied", 403
        
    username = request.form.get('username')
    percentage = request.form.get('percentage')
    
    try:
        percentage = int(percentage)
        if percentage < 0: percentage = 0
        if percentage > 100: percentage = 100
    except:
        percentage = 0
        
    user_model.update(username, {'project_percentage': percentage})
    
    # Broadcast update via WebSocket
    broadcast_percentage_update(username, percentage)
    
    flash(f"تم تحديث نسبة الإنجاز للعميل {username} بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))


@user_bp.route('/admin/delete_user/<username>', methods=['POST'])
def delete(username):
    """Delete user"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return "Access Denied", 403

    user_model.delete(username)
    flash(f"تم حذف المستخدم {username} بنجاح.")
    return redirect(url_for('admin.admin_dashboard'))
