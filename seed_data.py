import os
import shutil
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash
from db import init_db
from config import Config

# Simple SVG generator to create realistic sample images
def create_sample_svg(filename, title, color_bg, icon_text):
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
  <rect width="600" height="400" fill="{color_bg}"/>
  <circle cx="300" cy="170" r="80" fill="rgba(255,255,255,0.2)"/>
  <text x="300" y="195" font-family="Arial, sans-serif" font-size="70" font-weight="bold" fill="#ffffff" text-anchor="middle">{icon_text}</text>
  <text x="300" y="300" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="#ffffff" text-anchor="middle">{title}</text>
  <text x="300" y="340" font-family="Arial, sans-serif" font-size="16" fill="rgba(255,255,255,0.8)" text-anchor="middle">Campus Lost &amp; Found Media Portal</text>
</svg>'''
    filepath = os.path.join(Config.IMAGE_UPLOAD_FOLDER, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    return f"uploads/images/{filename}"

def seed():
    os.makedirs(Config.IMAGE_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.VIDEO_UPLOAD_FOLDER, exist_ok=True)
    
    db = init_db()
    
    # Check if data already exists
    if db.users.count_documents({}) > 0 and db.items.count_documents({}) > 0:
        print("[Seed] Database already contains records. Skipping seed.")
        return

    print("[Seed] Seeding sample campus users and items...")
    
    # 1. Create Default Users
    admin_pw = generate_password_hash("admin123")
    student_pw = generate_password_hash("student123")
    
    user1 = {
        "username": "rahul_sharma",
        "email": "rahul@campus.edu",
        "password_hash": student_pw,
        "role": "student",
        "phone": "+91 98765 43210",
        "department": "Computer Science (3rd Yr)",
        "created_at": datetime.now(timezone.utc)
    }
    user2 = {
        "username": "priya_patel",
        "email": "priya@campus.edu",
        "password_hash": student_pw,
        "role": "student",
        "phone": "+91 98220 12345",
        "department": "Electronics & Comm (2nd Yr)",
        "created_at": datetime.now(timezone.utc)
    }
    admin_user = {
        "username": "campus_admin",
        "email": "admin@campus.edu",
        "password_hash": admin_pw,
        "role": "admin",
        "phone": "+91 94444 00000",
        "department": "Security & Student Affairs",
        "created_at": datetime.now(timezone.utc)
    }
    
    u1_id = db.users.insert_one(user1).inserted_id
    u2_id = db.users.insert_one(user2).inserted_id
    adm_id = db.users.insert_one(admin_user).inserted_id
    
    # 2. Create Sample Media Files
    img_calc = create_sample_svg("sample_calculator.svg", "Casio Scientific Calculator", "#1e3a8a", "CALC")
    img_id = create_sample_svg("sample_id_card.svg", "Student ID Card", "#b91c1c", "ID")
    img_keys = create_sample_svg("sample_keys.svg", "Honda Bike Key", "#047857", "KEY")
    img_bottle = create_sample_svg("sample_bottle.svg", "Milton Water Bottle", "#0284c7", "AQUA")
    img_bag = create_sample_svg("sample_backpack.svg", "Wildcraft Navy Backpack", "#475569", "BAG")
    
    # 3. Create Sample Items
    now = datetime.now(timezone.utc)
    sample_items = [
        {
            "title": "Casio fx-991EX Scientific Calculator",
            "type": "Found",
            "category": "Electronics & Gadgets",
            "description": "Found on Desk #14 near the whiteboard in Computer Lab 2 after the Afternoon Data Structures practical session. Clean condition with cover.",
            "location": "Computer Science Block (Lab 1 / Lab 2)",
            "date_observed": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "status": "Available",
            "uploaded_by": u1_id,
            "uploader_name": "rahul_sharma",
            "uploader_email": "rahul@campus.edu",
            "uploader_role": "student",
            "contact_info": "Handed to Lab Assistant Mr. Ramesh or call rahul@campus.edu",
            "image_path": img_calc,
            "video_path": None,
            "custom_fields": {
                "brand": "Casio",
                "color": "Black & White"
            },
            "created_at": now - timedelta(hours=8)
        },
        {
            "title": "College Student ID Card (Roll: 22BCSE104)",
            "type": "Found",
            "category": "College ID & Cards",
            "description": "Found near the Central Library water cooler on 1st floor. Name on card is 'Aakash Verma'. Deposited with the main circulation desk.",
            "location": "Main Central Library",
            "date_observed": now.strftime("%Y-%m-%d"),
            "status": "Available",
            "uploaded_by": u2_id,
            "uploader_name": "priya_patel",
            "uploader_email": "priya@campus.edu",
            "uploader_role": "student",
            "contact_info": "Deposited at Library Front Desk",
            "image_path": img_id,
            "video_path": None,
            "custom_fields": {
                "id_number": "22BCSE104",
                "color": "Blue Lanyard"
            },
            "created_at": now - timedelta(hours=3)
        },
        {
            "title": "Honda Activa Bike Key with Red Tag",
            "type": "Lost",
            "category": "Keys & Keychains",
            "description": "Lost my vehicle key somewhere between the North Two-Wheeler Parking and the Canteen. Has a red woven lanyard tag with 'RIDE'. Very urgent as my vehicle is locked.",
            "location": "Parking Area (North / South)",
            "date_observed": now.strftime("%Y-%m-%d"),
            "status": "Available",
            "uploaded_by": u1_id,
            "uploader_name": "rahul_sharma",
            "uploader_email": "rahul@campus.edu",
            "uploader_role": "student",
            "contact_info": "+91 98765 43210 (Call immediately)",
            "image_path": img_keys,
            "video_path": None,
            "custom_fields": {
                "key_type": "Honda Scooter Key with red lanyard"
            },
            "created_at": now - timedelta(hours=1)
        },
        {
            "title": "Insulated Stainless Steel Water Bottle 1L",
            "type": "Found",
            "category": "Water Bottles",
            "description": "Metallic matte cyan water bottle left behind in Classroom 302 after the 11 AM Mathematics lecture.",
            "location": "Classroom Blocks",
            "date_observed": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "status": "Available",
            "uploaded_by": adm_id,
            "uploader_name": "campus_admin",
            "uploader_email": "admin@campus.edu",
            "uploader_role": "admin",
            "contact_info": "Available at Security Gate 1 Lost & Found Desk",
            "image_path": img_bottle,
            "video_path": None,
            "custom_fields": {
                "brand": "Milton Thermosteel",
                "color": "Cyan Blue"
            },
            "created_at": now - timedelta(days=2)
        },
        {
            "title": "Navy Blue Wildcraft Laptop Backpack",
            "type": "Lost",
            "category": "Bags & Backpacks",
            "description": "Left on the wooden bench outside the Canteen during lunch break. Contains notebook and pencil pouch. No electronic laptop was inside.",
            "location": "Canteen & Food Court",
            "date_observed": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "status": "Returned",
            "uploaded_by": u2_id,
            "uploader_name": "priya_patel",
            "uploader_email": "priya@campus.edu",
            "uploader_role": "student",
            "contact_info": "priya@campus.edu",
            "image_path": img_bag,
            "video_path": None,
            "custom_fields": {
                "brand": "Wildcraft",
                "color": "Navy Blue"
            },
            "created_at": now - timedelta(days=3)
        }
    ]
    
    db.items.insert_many(sample_items)
    print(f"[Seed] Successfully populated {len(sample_items)} items and 3 users!")

if __name__ == '__main__':
    seed()
