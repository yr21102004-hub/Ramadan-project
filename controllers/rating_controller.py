"""
Rating and Complaint Controller
Handles rating and complaint operations
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import RatingModel, ComplaintModel, UserModel
from werkzeug.utils import secure_filename
import os
from datetime import datetime

rating_bp = Blueprint('rating', __name__)

# Initialize models
rating_model = RatingModel()
complaint_model = ComplaintModel()
user_model = UserModel()

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/complaints'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@rating_bp.route('/worker/<username>')
def worker_profile(username):
    """Display worker profile with ratings"""
    worker = user_model.get_by_username(username)
    
    if not worker or worker.get('role') != 'worker':
        flash('الصنايعي غير موجود', 'error')
        return redirect(url_for('web.home'))
    
    # Get rating statistics
    rating_stats = rating_model.get_worker_stats(username)
    
    # Get all ratings
    ratings = rating_model.get_worker_ratings(username)
    
    # Get complaint count
    complaint_count = complaint_model.get_worker_complaint_count(username)
    
    # Check if current user has rated this worker
    user_has_rated = False
    if current_user.is_authenticated:
        user_has_rated = rating_model.user_has_rated(current_user.username, username)
    
    return render_template('worker_profile.html',
                         worker=worker,
                         rating_stats=rating_stats,
                         ratings=ratings,
                         complaint_count=complaint_count,
                         user_has_rated=user_has_rated)


@rating_bp.route('/rate/<worker_username>', methods=['POST'])
@login_required
def rate_worker(worker_username):
    """Submit a rating for a worker"""
    if current_user.role != 'user':
        flash('فقط العملاء يمكنهم تقييم الصنايعية', 'error')
        return redirect(url_for('rating.worker_profile', username=worker_username))
    
    quality_rating = int(request.form.get('quality_rating', 0))
    behavior_rating = int(request.form.get('behavior_rating', 0))
    comment = request.form.get('comment', '').strip()
    
    # Validate ratings
    if not (1 <= quality_rating <= 5) or not (1 <= behavior_rating <= 5):
        flash('التقييم يجب أن يكون من 1 إلى 5 نجوم', 'error')
        return redirect(url_for('rating.worker_profile', username=worker_username))
    
    # Add rating
    result = rating_model.add_rating(
        user_id=current_user.username,
        worker_id=worker_username,
        quality_rating=quality_rating,
        behavior_rating=behavior_rating,
        comment=comment
    )
    
    flash(result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('rating.worker_profile', username=worker_username))


@rating_bp.route('/complain/<worker_username>', methods=['POST'])
@login_required
def submit_complaint(worker_username):
    """Submit a complaint against a worker"""
    if current_user.role != 'user':
        flash('فقط العملاء يمكنهم تقديم شكاوى', 'error')
        return redirect(url_for('rating.worker_profile', username=worker_username))
    
    reason = request.form.get('reason', '')
    description = request.form.get('description', '').strip()
    
    if not description:
        flash('يجب كتابة وصف للمشكلة', 'error')
        return redirect(url_for('rating.worker_profile', username=worker_username))
    
    # Handle image uploads
    uploaded_images = []
    if 'images' in request.files:
        files = request.files.getlist('images')
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                uploaded_images.append(f"uploads/complaints/{filename}")
    
    # Add complaint
    result = complaint_model.add_complaint(
        user_id=current_user.username,
        worker_id=worker_username,
        reason=reason,
        description=description,
        images=uploaded_images
    )
    
    flash(result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('rating.worker_profile', username=worker_username))


@rating_bp.route('/api/worker/<username>/stats')
def get_worker_stats_api(username):
    """API endpoint to get worker rating stats"""
    stats = rating_model.get_worker_stats(username)
    complaint_count = complaint_model.get_worker_complaint_count(username)
    
    return jsonify({
        'rating_stats': stats,
        'complaint_count': complaint_count
    })
