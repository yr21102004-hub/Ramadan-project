

@admin_bp.route('/admin/inspections')
@login_required
def admin_inspections():
    """View and manage inspections"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    # Get all requests
    all_requests = inspection_model.get_all()
    all_requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Statistics
    stats = {
        'new': len([r for r in all_requests if r['status'] == 'new_request']),
        'assigned': len([r for r in all_requests if r['status'] == 'assigned_to_worker']),
        'admin_visit': len([r for r in all_requests if r['status'] == 'admin_visit']),
        'completed': len([r for r in all_requests if r['status'] == 'completed']),
        'total': len(all_requests)
    }
    
    return render_template('admin_inspections.html', requests=all_requests, stats=stats)


@admin_bp.route('/admin/inspection/<request_id>/assign', methods=['POST'])
@login_required
def assign_inspection(request_id):
    """Assign worker or admin to inspection"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    assignment_type = request.form.get('assignment_type') # 'worker' or 'admin'
    
    if assignment_type == 'admin':
        inspection_model.assign_admin_visit(request_id)
        flash('تم تعيين المعاينة للإدارة', 'success')
    else:
        worker_username = request.form.get('worker_username')
        if worker_username:
            inspection_model.assign_worker(request_id, worker_username)
            flash(f'تم تعيين المعاينة للصنايعي {worker_username}', 'success')
        else:
            flash('الرجاء اختيار صنايعي', 'error')
            
    return redirect(url_for('admin.admin_inspections'))


@admin_bp.route('/admin/inspection/<request_id>/details')
@login_required
def inspection_details(request_id):
    """Get inspection details and nearby workers via AJAX"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    req = inspection_model.get_request_by_id(request_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404
        
    # Find nearest workers
    nearby_workers = inspection_model.find_nearest_workers(
        user_lat=req['user_latitude'],
        user_lon=req['user_longitude'],
        service_type=req['service_type'],
        max_distance=100, # Search wider range for admin
        limit=10
    )
    
    return jsonify({
        'request': req,
        'nearby_workers': nearby_workers
    })
