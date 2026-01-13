

@admin_bp.route('/admin/complaints')
@login_required
def admin_complaints():
    """View and manage complaints"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    # Get all complaints
    all_complaints = complaint_model.get_all()
    
    # Sort by date (newest first)
    all_complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Get statistics
    pending = len([c for c in all_complaints if c['status'] == 'قيد المراجعة'])
    resolved = len([c for c in all_complaints if c['status'] == 'تم الحل'])
    rejected = len([c for c in all_complaints if c['status'] == 'مرفوضة'])
    
    stats = {
        'total': len(all_complaints),
        'pending': pending,
        'resolved': resolved,
        'rejected': rejected
    }
    
    return render_template('admin_complaints.html', complaints=all_complaints, stats=stats)


@admin_bp.route('/admin/complaint/<int:complaint_id>/update', methods=['POST'])
@login_required
def update_complaint_status(complaint_id):
    """Update complaint status"""
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    complaint_model.update_status(complaint_id, status, admin_notes)
    
    flash('تم تحديث حالة الشكوى بنجاح', 'success')
    return redirect(url_for('admin.admin_complaints'))
