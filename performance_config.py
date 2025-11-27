# performance_config.py - Performance optimization config
import os
from functools import wraps
from flask import request, g
from app import app
from datetime import datetime, timedelta

# Cache config
CACHE_ENABLED = True
CACHE_TIMEOUT = 300  # 5 minutes

# Query optimization
def cache_result(timeout=CACHE_TIMEOUT):
    """Decorator for caching function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not CACHE_ENABLED:
                return f(*args, **kwargs)
            
            cache_key = f"cache:{f.__name__}:{str(args)}:{str(kwargs)}"
            if not hasattr(g, '_cache'):
                g._cache = {}
            
            if cache_key in g._cache:
                return g._cache[cache_key]
            
            result = f(*args, **kwargs)
            g._cache[cache_key] = result
            return result
        return decorated_function
    return decorator

# Optimized query helpers
class QueryOptimizer:
    @staticmethod
    def get_employees_optimized(department_id=None, status='active'):
        """Get employees with eager loading to avoid N+1"""
        from models import Employee
        from sqlalchemy.orm import joinedload
        
        query = Employee.query.options(
            joinedload(Employee.departments),
            joinedload(Employee.documents)
        ).filter(Employee.status == status)
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        return query.all()
    
    @staticmethod
    def get_departments_optimized():
        """Get departments with employee count"""
        from models import Department
        from sqlalchemy.orm import joinedload
        
        return Department.query.options(
            joinedload(Department.employees)
        ).all()
    
    @staticmethod
    def get_salary_data_optimized(month, year, department_id=None):
        """Get salary data efficiently"""
        from models import Salary, Employee
        from sqlalchemy.orm import joinedload
        
        query = Salary.query.options(
            joinedload(Salary.employee)
        ).filter(
            Salary.month == month,
            Salary.year == year
        )
        
        if department_id:
            query = query.join(Employee).filter(
                Employee.department_id == department_id
            )
        
        return query.all()

# Image optimization
class ImageOptimizer:
    @staticmethod
    def should_optimize_image(file_path):
        """Check if image needs optimization"""
        import os
        if not os.path.exists(file_path):
            return False
        
        size = os.path.getsize(file_path)
        return size > 500 * 1024  # > 500KB
    
    @staticmethod
    def optimize_image(file_path, max_size=(1920, 1920), quality=85):
        """Optimize image size and quality"""
        try:
            from PIL import Image
            import os
            
            if not os.path.exists(file_path):
                return False
            
            img = Image.open(file_path)
            
            # Resize if necessary
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB if JPEG
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                if img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    rgb_img.save(file_path, 'JPEG', quality=quality, optimize=True)
                else:
                    img.save(file_path, 'JPEG', quality=quality, optimize=True)
            else:
                img.save(file_path, quality=quality, optimize=True)
            
            return True
        except Exception as e:
            app.logger.error(f"Image optimization failed: {e}")
            return False

# Response optimization
@app.before_request
def before_request():
    """Pre-request optimizations"""
    g._start_time = datetime.utcnow()
    g._cache = {}

@app.after_request
def after_request(response):
    """Post-request optimizations"""
    if hasattr(g, '_start_time'):
        elapsed = (datetime.utcnow() - g._start_time).total_seconds()
        if elapsed > 1:
            app.logger.warning(f"Slow request: {request.path} took {elapsed:.2f}s")
    
    # Add caching headers
    if response.content_type and response.content_type.startswith('text/html'):
        response.cache_control.max_age = 60
    elif response.content_type and (
        response.content_type.startswith('image/') or 
        response.content_type.startswith('application/javascript') or
        response.content_type.startswith('text/css')
    ):
        response.cache_control.max_age = 86400  # 1 day
    
    return response

print("✅ Performance optimization module loaded")
