"""
Rating Model - handles worker ratings
"""
from tinydb import Query
from datetime import datetime
from .database import Database


class RatingModel:
    """Rating Model - handles rating operations"""
    
    def __init__(self):
        self.db = Database()
        self.table = self.db.ratings
        self.query = Query()
    
    def add_rating(self, user_id, worker_id, quality_rating, behavior_rating, comment=""):
        """Add a new rating"""
        # Check if user already rated this worker
        existing = self.table.search(
            (self.query.user_id == user_id) & 
            (self.query.worker_id == worker_id)
        )
        
        if existing:
            return {'success': False, 'message': 'لقد قمت بتقييم هذا الصنايعي من قبل'}
        
        rating_data = {
            'user_id': user_id,
            'worker_id': worker_id,
            'quality_rating': quality_rating,  # 1-5
            'behavior_rating': behavior_rating,  # 1-5
            'comment': comment,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.table.insert(rating_data)
        return {'success': True, 'message': 'تم إضافة التقييم بنجاح'}
    
    def get_worker_ratings(self, worker_id):
        """Get all ratings for a specific worker"""
        return self.table.search(self.query.worker_id == worker_id)
    
    def get_worker_stats(self, worker_id):
        """Get rating statistics for a worker"""
        ratings = self.get_worker_ratings(worker_id)
        
        if not ratings:
            return {
                'avg_quality': 0,
                'avg_behavior': 0,
                'total_ratings': 0
            }
        
        total_quality = sum([r['quality_rating'] for r in ratings])
        total_behavior = sum([r['behavior_rating'] for r in ratings])
        count = len(ratings)
        
        return {
            'avg_quality': round(total_quality / count, 1),
            'avg_behavior': round(total_behavior / count, 1),
            'total_ratings': count
        }
    
    def user_has_rated(self, user_id, worker_id):
        """Check if user has already rated this worker"""
        result = self.table.search(
            (self.query.user_id == user_id) & 
            (self.query.worker_id == worker_id)
        )
        return len(result) > 0
    
    def get_user_project_rating(self, user_id):
        """Get project rating by a specific user"""
        result = self.table.search(
            (self.query.user_id == user_id) & 
            (self.query.worker_id == 'PROJECT')
        )
        return result[0] if result else None

    def add_project_rating(self, user_id, rating, comment=""):
        """Add a rating for the project itself"""
        # Check if already rated
        if self.get_user_project_rating(user_id):
            return {'success': False, 'message': 'لقد قمت بتقييم المشروع بالفعل'}
            
        rating_data = {
            'user_id': user_id,
            'worker_id': 'PROJECT',
            'quality_rating': rating,
            'behavior_rating': 0, # Not applicable
            'comment': comment,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.table.insert(rating_data)
        return {'success': True, 'message': 'تم إضافة تقييمك للمشروع بنجاح'}
    
    def get_all(self):
        """Get all ratings"""
        return self.table.all()
