"""
Complaint Model - handles worker complaints
"""
from tinydb import Query
from datetime import datetime
from .database import Database


class ComplaintModel:
    """Complaint Model - handles complaint operations"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.complaints
        self.query = Query()
    
    def add_complaint(self, user_id, worker_id, reason, description, images=None):
        """Add a new complaint"""
        complaint_data = {
            'user_id': user_id,
            'worker_id': worker_id,
            'reason': reason,  # تأخير، سوء تعامل، شغل غير مطابق، سبب آخر
            'description': description,
            'images': images or [],  # قائمة بمسارات الصور
            'status': 'قيد المراجعة',  # قيد المراجعة، تم الحل، مرفوضة
            'admin_notes': '',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'resolved_at': None
        }
        
        doc_id = self.table.insert(complaint_data)
        return {'success': True, 'message': 'تم تقديم الشكوى بنجاح', 'complaint_id': doc_id}
    
    def get_worker_complaints(self, worker_id):
        """Get all complaints for a specific worker"""
        return self.table.search(self.query.worker_id == worker_id)
    
    def get_pending_complaints(self):
        """Get all pending complaints"""
        return self.table.search(self.query.status == 'قيد المراجعة')
    
    def get_complaint_by_id(self, complaint_id):
        """Get complaint by ID"""
        return self.table.get(doc_id=complaint_id)
    
    def update_status(self, complaint_id, status, admin_notes=''):
        """Update complaint status"""
        update_data = {
            'status': status,
            'admin_notes': admin_notes
        }
        
        if status in ['تم الحل', 'مرفوضة']:
            update_data['resolved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.table.update(update_data, doc_ids=[complaint_id])
        return {'success': True, 'message': 'تم تحديث حالة الشكوى'}
    
    def get_worker_complaint_count(self, worker_id):
        """Get number of complaints for a worker"""
        complaints = self.get_worker_complaints(worker_id)
        return {
            'total': len(complaints),
            'pending': len([c for c in complaints if c['status'] == 'قيد المراجعة']),
            'resolved': len([c for c in complaints if c['status'] == 'تم الحل']),
            'rejected': len([c for c in complaints if c['status'] == 'مرفوضة'])
        }
    
    def get_all(self):
        """Get all complaints"""
        return self.table.all()
