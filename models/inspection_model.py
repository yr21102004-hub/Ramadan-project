"""
Inspection Request Model - handles inspection requests
"""
from tinydb import Query
from datetime import datetime, timedelta
from .database import Database
import math


class InspectionRequestModel:
    """Inspection Request Model - handles inspection request operations"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.table('inspection_requests')
        self.query = Query()
    
    
    def create_request(self, user_id, user_location, service_type, description='', images=None):
        """Create a new inspection request"""
        request_data = {
            'user_id': user_id,
            'user_latitude': user_location['latitude'],
            'user_longitude': user_location['longitude'],
            'governorate': user_location.get('governorate', ''),
            'city': user_location.get('city', ''),
            'user_address': user_location.get('address', ''),
            'service_type': service_type,
            'description': description,
            'images': images or [],
            'status': 'new_request',  # new_request, assigned_to_worker, admin_visit, inspection_done, admin_inspection_done, approved_for_user, completed, cancelled
            'assigned_worker': None,
            'inspection_by': None, # 'worker' or 'admin'
            'inspection_report': None,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'response_deadline': (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        doc_id = self.table.insert(request_data)
        return {'success': True, 'request_id': doc_id, 'data': request_data}
    
    def get_request_by_id(self, request_id):
        """Get request by ID"""
        return self.table.get(doc_id=request_id)
    
    def update_status(self, request_id, status, extra_data=None):
        """Update request status and optional extra data"""
        data = {'status': status}
        if extra_data:
            data.update(extra_data)
        self.table.update(data, doc_ids=[request_id])
    
    def assign_worker(self, request_id, worker_id):
        """Assign a worker to a request"""
        self.table.update({
            'assigned_worker': worker_id,
            'status': 'assigned_to_worker',
            'inspection_by': 'worker',
            'assigned_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, doc_ids=[request_id])

    def assign_admin_visit(self, request_id):
        """Assign admin for visit"""
        self.table.update({
            'status': 'admin_visit',
            'inspection_by': 'admin',
            'assigned_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, doc_ids=[request_id])
    
    def accept_request(self, request_id, worker_id):
        """Worker accepts the request"""
        self.table.update({
            'status': 'accepted',
            'assigned_worker': worker_id,
            'accepted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, doc_ids=[request_id])
        return {'success': True, 'message': 'تم قبول طلب المعاينة'}
    
    def reject_request(self, request_id, worker_id, reason=''):
        """Worker rejects the request"""
        # Get current request
        request = self.get_request_by_id(request_id)
        if not request:
            return {'success': False, 'message': 'الطلب غير موجود'}
        
        # Add to rejected workers list
        rejected_workers = request.get('rejected_workers', [])
        rejected_workers.append({
            'worker_id': worker_id,
            'reason': reason,
            'rejected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        self.table.update({
            'rejected_workers': rejected_workers
        }, doc_ids=[request_id])
        
        return {'success': True, 'message': 'تم رفض الطلب'}
    
    def complete_request(self, request_id):
        """Mark request as completed"""
        self.table.update({
            'status': 'completed',
            'completed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, doc_ids=[request_id])
    
    def cancel_request(self, request_id):
        """Cancel a request"""
        self.table.update({
            'status': 'cancelled',
            'cancelled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, doc_ids=[request_id])

    def submit_report(self, request_id, report_data):
        """Submit inspection report"""
        self.table.update({
            'status': 'inspection_done',
            'inspection_report': {
                'photos': report_data.get('photos', []),
                'voice_note_url': report_data.get('voice_note_url'),
                'job_type': report_data.get('job_type'),
                'place_status': report_data.get('place_status'),
                'job_size': report_data.get('job_size'),
                'submitted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }, doc_ids=[request_id])
        return {'success': True, 'message': 'تم حفظ تقرير المعاينة'}

    def approve_report(self, request_id):
        """Admin approves the report and reveals worker"""
        self.table.update({
            'status': 'approved_for_user',
            'approved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, doc_ids=[request_id])
    
    def get_user_requests(self, user_id):
        """Get all requests for a user"""
        return self.table.search(self.query.user_id == user_id)
    
    def get_worker_requests(self, worker_id):
        """Get all requests assigned to a worker"""
        return self.table.search(self.query.assigned_worker == worker_id)
    
    def get_pending_requests(self):
        """Get all pending requests"""
        return self.table.search(self.query.status == 'pending')
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        # Radius of Earth in kilometers
        R = 6371
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return round(distance, 2)  # Return distance in km
    
    def find_nearest_workers(self, user_lat, user_lon, service_type, max_distance=50, limit=3):
        """Find nearest available workers"""
        from .database import UserModel
        user_model = UserModel()
        
        # Get all workers
        all_users = user_model.get_all()
        workers = [u for u in all_users if u.get('role') == 'worker']
        
        # Filter workers
        available_workers = []
        for worker in workers:
            # Check if worker has GPS enabled and location data
            if not worker.get('gps_active', False):
                continue
            
            if not worker.get('latitude') or not worker.get('longitude'):
                continue
            
            # Check if worker is available
            if not worker.get('available_for_inspection', True):
                continue
            
            # Check service type match (if specified)
            if service_type and worker.get('specialization') != service_type:
                continue
            
            # Calculate distance
            distance = self.calculate_distance(
                user_lat, user_lon,
                float(worker['latitude']), float(worker['longitude'])
            )
            
            # Check max distance preference
            worker_max_distance = worker.get('max_inspection_distance', 50)
            if distance > worker_max_distance or distance > max_distance:
                continue
            
            available_workers.append({
                'worker': worker,
                'distance': distance
            })
        
        # Sort by distance
        available_workers.sort(key=lambda x: x['distance'])
        
        # Return top N workers
        return available_workers[:limit]
    
    def get_all(self):
        """Get all requests"""
        return self.table.all()
