import os
import uuid
from functools import wraps
from flask import session, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_media_file(file_storage, media_type='image'):
    """
    Saves an uploaded file to the designated folder.
    media_type: 'image' or 'video'
    Returns relative path like 'uploads/images/abc_item.jpg' or None
    """
    if not file_storage or file_storage.filename == '':
        return None

    allowed_exts = Config.ALLOWED_IMAGE_EXTENSIONS if media_type == 'image' else Config.ALLOWED_VIDEO_EXTENSIONS
    target_dir = Config.IMAGE_UPLOAD_FOLDER if media_type == 'image' else Config.VIDEO_UPLOAD_FOLDER
    
    os.makedirs(target_dir, exist_ok=True)
    
    if not allowed_file(file_storage.filename, allowed_exts):
        raise ValueError(f"Invalid {media_type} file format. Allowed: {', '.join(allowed_exts)}")
    
    original_name = secure_filename(file_storage.filename)
    unique_prefix = uuid.uuid4().hex[:10]
    final_filename = f"{unique_prefix}_{original_name}"
    full_path = os.path.join(target_dir, final_filename)
    
    file_storage.save(full_path)
    return f"uploads/{'images' if media_type == 'image' else 'videos'}/{final_filename}"

def delete_media_file(relative_path):
    """
    Safely removes a media file from disk when an item is deleted.
    """
    if not relative_path:
        return
    full_path = os.path.join(Config.BASE_DIR, 'static', relative_path.replace('/', os.sep))
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this feature.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in as an administrator.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('user_role') != 'admin':
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
