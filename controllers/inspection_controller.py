"""
Inspection Controller
Handles inspection requests and location operations
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import InspectionRequestModel, UserModel
from utils.egypt_locations import get_all_governorates, get_cities_by_governorate
import json

inspection_bp = Blueprint('inspection', __name__)

# Initialize models
inspection_model = InspectionRequestModel()
user_model = UserModel()

@inspection_bp.route('/inspection/request', methods=['GET', 'POST'])
@login_required
def request_inspection():
    """User: Request an inspection"""
    if current_user.role != 'user':
        flash('فقط العملاء يمكنهم طلب معاينة', 'error')
        return redirect(url_for('web.home'))
    
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        governorate = request.form.get('governorate')
        city = request.form.get('city')
        address = request.form.get('address')
        
        if not latitude or not longitude:
            flash('يجب تحديد موقعك على الخريطة', 'error')
            return render_template('request_inspection.html')
            
        user_location = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'governorate': governorate,
            'city': city,
            'address': address
        }
        
        # Handle images
        uploaded_images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    from werkzeug.utils import secure_filename
                    from datetime import datetime
                    import os
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join('static/uploads/inspections', filename)
                    os.makedirs('static/uploads/inspections', exist_ok=True)
                    file.save(filepath)
                    uploaded_images.append(f"uploads/inspections/{filename}")

        # Create request
        result = inspection_model.create_request(
            user_id=current_user.username,
            user_location=user_location,
            service_type=service_type,
            description=description,
            images=uploaded_images
        )
        
        flash('تم إرسال طلبك بنجاح. سنقوم بمراجعته وتعيين الصنايعي المناسب.', 'success')
            
        return redirect(url_for('inspection.my_requests'))

    return render_template('request_inspection.html')

@inspection_bp.route('/inspection/my-requests')
@login_required
def my_requests():
    """User: View my requests"""
    if current_user.role != 'user':
        return redirect(url_for('web.home'))
        
    requests = inspection_model.get_user_requests(current_user.username)
    # Sort by newest
    requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('my_inspections.html', requests=requests)

@inspection_bp.route('/worker/inspections')
@login_required
def worker_inspections():
    """Worker: View assigned inspections"""
    if current_user.role != 'worker':
        return redirect(url_for('web.home'))
        
    requests = inspection_model.get_worker_requests(current_user.username)
    # Filter pending requests
    pending = [r for r in requests if r.get('status') == 'assigned_to_worker']
    # Filter other requests
    others = [r for r in requests if r.get('status') != 'assigned_to_worker']
    
    # Sort by newest
    pending.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    others.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('worker_inspections.html', pending=pending, others=others)

@inspection_bp.route('/inspection/<request_id>/respond', methods=['POST'])
@login_required
def respond_inspection(request_id):
    """Worker: Accept/Reject inspection"""
    if current_user.role != 'worker':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    action = request.form.get('action') # accept or reject
    
    if action == 'accept':
        result = inspection_model.accept_request(request_id, current_user.username)
        if result['success']:
            flash('تم قبول المعاينة، يمكنك الآن التواصل مع العميل', 'success')
            
    elif action == 'reject':
        reason = request.form.get('reason', '')
        # Just update status to rejected (or maybe back to 'new_request' for admin to reassign?)
        # For now, let's keep it rejected and admin can see rejected workers log
        inspection_model.reject_request(request_id, current_user.username, reason)
        flash('تم رفض الطلب', 'info')

    return redirect(url_for('inspection.worker_inspections'))

@inspection_bp.route('/inspection/<request_id>/report', methods=['GET', 'POST'])
@login_required
def submit_report(request_id):
    """Worker: Submit inspection report"""
    if current_user.role != 'worker':
        return redirect(url_for('web.home'))
        
    req = inspection_model.get_request_by_id(request_id)
    if not req or req['assigned_worker'] != current_user.username:
        return "Unauthorized", 403
        
    if request.method == 'POST':
        try:
            from werkzeug.utils import secure_filename
            import os
            
            # 1. Save Photos
            photo_paths = []
            if 'photos' in request.files:
                files = request.files.getlist('photos')
                for file in files:
                    if file and file.filename:
                        filename = secure_filename(f"{request_id}_{file.filename}")
                        filepath = os.path.join('static/uploads/reports', filename)
                        os.makedirs('static/uploads/reports', exist_ok=True)
                        file.save(filepath)
                        photo_paths.append(f"uploads/reports/{filename}")
            
            # 2. Save Voice Note
            voice_url = None
            if 'voice_note' in request.files:
                voice_file = request.files['voice_note']
                if voice_file:
                    filename = f"voice_{request_id}_{secure_filename(voice_file.filename)}"
                    filepath = os.path.join('static/uploads/reports', filename)
                    os.makedirs('static/uploads/reports', exist_ok=True)
                    voice_file.save(filepath)
                    voice_url = f"uploads/reports/{filename}"

            # 3. Data
            report_data = {
                'photos': photo_paths,
                'voice_note_url': voice_url,
                'job_type': request.form.get('job_type'),
                'place_status': request.form.get('place_status'),
                'job_size': request.form.get('job_size')
            }
            
            inspection_model.submit_report(request_id, report_data)
            return jsonify({'success': True})
            
        except Exception as e:
            print(e)
            return jsonify({'success': False, 'message': str(e)})

    return render_template('submit_report.html', request=req)

@inspection_bp.route('/api/governorates')
def get_governorates():
    """API: Get all governorates"""
    return jsonify(get_all_governorates())

@inspection_bp.route('/api/cities/<governorate>')
def get_cities(governorate):
    """API: Get cities for governorate"""
    return jsonify(get_cities_by_governorate(governorate))

@inspection_bp.route('/worker/settings/location', methods=['POST'])
@login_required
def update_location_settings():
    """Worker: Update location settings"""
    if current_user.role != 'worker':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    
    update_data = {
        'governorate': data.get('governorate'),
        'city': data.get('city'),
        'latitude': data.get('latitude'),
        'longitude': data.get('longitude'),
        'gps_active': data.get('gps_active'),
        'available_for_inspection': data.get('available'),
        'max_inspection_distance': int(data.get('max_distance', 50))
    }
    
    user_model.update(current_user.username, update_data)
    return jsonify({'success': True, 'message': 'تم تحديث إعدادات الموقع'})
