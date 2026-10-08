import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from .env file if present
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'campus_lost_found_super_secret_key_2026')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.environ.get('DB_NAME', 'campus_lost_found_db')
    
    # Upload directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    VIDEO_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
    
    # 32 MB max request payload
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
    
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
