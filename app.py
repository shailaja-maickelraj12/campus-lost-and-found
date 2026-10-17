import os
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from db import init_db, get_db, is_mock_db
from helpers import save_media_file, delete_media_file, login_required, admin_required

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folders exist
os.makedirs(Config.IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.VIDEO_UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db = init_db()

CATEGORIES = [
    "Electronics & Gadgets",
    "College ID & Cards",
    "Wallets & Purses",
    "Bags & Backpacks",
    "Keys & Keychains",
    "Books & Lab Records",
    "Water Bottles",
    "Eyewear & Watches",
    "Clothing & Accessories",
    "Sports Equipment",
    "Others"
]

CAMPUS_LOCATIONS = [
    "Computer Science Block (Lab 1 / Lab 2)",
    "Main Central Library",
    "Auditorium & Open Air Theatre",
    "Canteen & Food Court",
    "Mechanical & Civil Workshop",
    "Sports Complex / Ground",
    "Student Activity Center (SAC)",
    "Admin Block & Exam Cell",
    "Parking Area (North / South)",
    "Campus Gate 1 / Gate 2",
    "Classroom Blocks"
]

@app.context_processor
def inject_globals():
    user_info = None
    if 'user_id' in session:
        user_info = {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'email': session.get('user_email'),
            'role': session.get('user_role')
        }
    return {
        'current_user': user_info,
        'categories': CATEGORIES,
        'locations': CAMPUS_LOCATIONS,
        'is_mock_db': is_mock_db()
    }

@app.template_filter('datetime_format')
def datetime_format(val, fmt='%b %d, %Y'):
    if not val:
        return 'N/A'
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val)
        except Exception:
            return val
    return val.strftime(fmt)

# -------------------------------------------------------------
# Home & Feed Routes (Read)
# -------------------------------------------------------------
@app.route('/')
def index():
    database = get_db()
    
    # Recent items
    recent_lost = list(database.items.find({"type": "Lost"}).sort("created_at", -1).limit(4))
    recent_found = list(database.items.find({"type": "Found"}).sort("created_at", -1).limit(4))
    
    # Quick statistics
    total_items = database.items.count_documents({})
    total_lost = database.items.count_documents({"type": "Lost"})
    total_found = database.items.count_documents({"type": "Found"})
    total_returned = database.items.count_documents({"status": "Returned"})
    
    return render_template(
        'home.html',
        recent_lost=recent_lost,
        recent_found=recent_found,
        stats={
            'total': total_items,
            'lost': total_lost,
            'found': total_found,
            'returned': total_returned
        }
    )

# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        
        # Basic validation
        if not username or not email or not password:
            flash("All required fields must be filled.", "danger")
            return render_template('register.html')
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')
            
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template('register.html')
            
        database = get_db()
        existing_user = database.users.find_one({"$or": [{"email": email}, {"username": username}]})
        if existing_user:
            flash("A user with this email or username already exists.", "warning")
            return render_template('register.html')
            
        hashed_password = generate_password_hash(password)
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "role": role,
            "phone": phone,
            "department": department,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = database.users.insert_one(user_doc)
        
        # Log the user in directly
        session['user_id'] = str(result.inserted_id)
        session['username'] = username
        session['user_email'] = email
        session['user_role'] = role
        
        flash(f"Welcome to Campus Lost & Found, {username}!", "success")
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')
        next_page = request.args.get('next') or url_for('index')
        
        if not login_id or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('login.html')
            
        database = get_db()
        # Find by either email or username
        user = database.users.find_one({
            "$or": [
                {"email": login_id.lower()},
                {"username": login_id}
            ]
        })
        
        if not user or not check_password_hash(user.get('password_hash', ''), password):
            flash("Invalid credentials. Please check your username/email and password.", "danger")
            return render_template('login.html')
            
        # Store in session
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        session['user_email'] = user['email']
        session['user_role'] = user.get('role', 'student')
        
        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(next_page)
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('index'))

# -------------------------------------------------------------
# Add Lost / Found Item (Create with Media Upload)
# -------------------------------------------------------------
@app.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        item_type = request.form.get('type', 'Found').strip().capitalize()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        date_observed = request.form.get('date_observed', '')
        contact_info = request.form.get('contact_info', '').strip()
        
        # Specific dynamic attributes
        brand = request.form.get('brand', '').strip()
        color = request.form.get('color', '').strip()
        id_number = request.form.get('id_number', '').strip()
        key_type = request.form.get('key_type', '').strip()
        
        if not title or not category or not location:
            flash("Title, category, and location are required.", "danger")
            return render_template('add_item.html')
            
        # Handle media uploads
        image_file = request.files.get('image')
        video_file = request.files.get('video')
        
        image_path = None
        video_path = None
        
        try:
            if image_file and image_file.filename:
                image_path = save_media_file(image_file, media_type='image')
            if video_file and video_file.filename:
                video_path = save_media_file(video_file, media_type='video')
        except ValueError as val_err:
            flash(str(val_err), "danger")
            return render_template('add_item.html')
        except Exception as e:
            flash(f"File upload error: {str(e)}", "danger")
            return render_template('add_item.html')
            
        custom_fields = {}
        if brand: custom_fields['brand'] = brand
        if color: custom_fields['color'] = color
        if id_number: custom_fields['id_number'] = id_number
        if key_type: custom_fields['key_type'] = key_type
        
        item_doc = {
            "title": title,
            "type": item_type if item_type in ['Lost', 'Found'] else 'Found',
            "category": category,
            "description": description,
            "location": location,
            "date_observed": date_observed or datetime.now().strftime("%Y-%m-%d"),
            "status": "Available",
            "uploaded_by": ObjectId(session['user_id']),
            "uploader_name": session.get('username'),
            "uploader_email": session.get('user_email'),
            "uploader_role": session.get('user_role'),
            "contact_info": contact_info or session.get('user_email'),
            "image_path": image_path,
            "video_path": video_path,
            "custom_fields": custom_fields,
            "created_at": datetime.now(timezone.utc)
        }
        
        database = get_db()
        result = database.items.insert_one(item_doc)
        flash(f"Successfully posted {item_type} item: '{title}'!", "success")
        return redirect(url_for('item_detail', item_id=str(result.inserted_id)))
        
    return render_template('add_item.html')

# -------------------------------------------------------------
# Browse & Search Items (Read)
# -------------------------------------------------------------
@app.route('/items')
def items():
    database = get_db()
    
    # Query parameters
    search_q = request.args.get('q', '').strip()
    item_type = request.args.get('type', 'all').strip()
    category = request.args.get('category', 'all').strip()
    location = request.args.get('location', 'all').strip()
    status = request.args.get('status', 'all').strip()
    sort_by = request.args.get('sort', 'newest').strip()
    
    query = {}
    
    if search_q:
        query['$or'] = [
            {'title': {'$regex': search_q, '$options': 'i'}},
            {'description': {'$regex': search_q, '$options': 'i'}},
            {'location': {'$regex': search_q, '$options': 'i'}},
            {'category': {'$regex': search_q, '$options': 'i'}},
            {'custom_fields.brand': {'$regex': search_q, '$options': 'i'}},
            {'custom_fields.id_number': {'$regex': search_q, '$options': 'i'}}
        ]
        
    if item_type != 'all' and item_type in ['Lost', 'Found']:
        query['type'] = item_type
        
    if category != 'all' and category:
        query['category'] = category
        
    if location != 'all' and location:
        query['location'] = location
        
    if status != 'all' and status:
        query['status'] = status
        
    sort_spec = ("created_at", -1) if sort_by == 'newest' else ("created_at", 1)
    
    item_list = list(database.items.find(query).sort([sort_spec]))
    total_found_count = len(item_list)
    
    return render_template(
        'items.html',
        items=item_list,
        total_count=total_found_count,
        search_q=search_q,
        current_type=item_type,
        current_category=category,
        current_location=location,
        current_status=status,
        current_sort=sort_by
    )

# -------------------------------------------------------------
# Item Details View (Read with Media Display)
# -------------------------------------------------------------
@app.route('/item/<item_id>')
def item_detail(item_id):
    try:
        obj_id = ObjectId(item_id)
    except (InvalidId, TypeError):
        abort(404)
        
    database = get_db()
    item = database.items.find_one({"_id": obj_id})
    if not item:
        abort(404)
        
    # Check ownership
    is_owner = False
    if 'user_id' in session and str(item.get('uploaded_by')) == session['user_id']:
        is_owner = True
    elif session.get('user_role') == 'admin':
        is_owner = True
        
    # Related items in same category
    related_items = list(database.items.find({
        "category": item.get('category'),
        "_id": {"$ne": obj_id}
    }).limit(3))
    
    # Claims submitted on this item (visible to owner or admin)
    claims = []
    user_claim = None
    if 'user_id' in session:
        user_id_obj = ObjectId(session['user_id'])
        if is_owner:
            claims = list(database.claims.find({"item_id": obj_id}).sort("created_at", -1))
        else:
            # Has this user already claimed this item?
            user_claim = database.claims.find_one({"item_id": obj_id, "claimant_id": user_id_obj})
        
    return render_template(
        'item_detail.html',
        item=item,
        is_owner=is_owner,
        related_items=related_items,
        claims=claims,
        user_claim=user_claim
    )

# -------------------------------------------------------------
# SECOND HALF: Edit Item Post (Update - PyMongo update_one)
# -------------------------------------------------------------
@app.route('/edit-item/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    try:
        obj_id = ObjectId(item_id)
    except (InvalidId, TypeError):
        abort(404)
        
    database = get_db()
    item = database.items.find_one({"_id": obj_id})
    if not item:
        abort(404)
        
    # Access check: Only owner or admin
    is_owner = str(item.get('uploaded_by')) == session['user_id']
    is_admin = session.get('user_role') == 'admin'
    if not (is_owner or is_admin):
        flash("You do not have permission to edit this post.", "danger")
        return redirect(url_for('item_detail', item_id=item_id))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        item_type = request.form.get('type', item.get('type', 'Found')).strip().capitalize()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        date_observed = request.form.get('date_observed', '')
        contact_info = request.form.get('contact_info', '').strip()
        status = request.form.get('status', item.get('status', 'Available'))
        
        brand = request.form.get('brand', '').strip()
        color = request.form.get('color', '').strip()
        id_number = request.form.get('id_number', '').strip()
        key_type = request.form.get('key_type', '').strip()
        
        if not title or not category or not location:
            flash("Title, category, and location are required.", "danger")
            return render_template('edit_item.html', item=item)
            
        image_path = item.get('image_path')
        video_path = item.get('video_path')
        
        # Check if user wants to remove existing files
        if request.form.get('remove_image') == 'yes':
            delete_media_file(image_path)
            image_path = None
        if request.form.get('remove_video') == 'yes':
            delete_media_file(video_path)
            video_path = None
            
        # Handle replacement media uploads
        new_image = request.files.get('image')
        new_video = request.files.get('video')
        
        try:
            if new_image and new_image.filename:
                delete_media_file(image_path)
                image_path = save_media_file(new_image, media_type='image')
            if new_video and new_video.filename:
                delete_media_file(video_path)
                video_path = save_media_file(new_video, media_type='video')
        except ValueError as err:
            flash(str(err), "danger")
            return render_template('edit_item.html', item=item)
            
        custom_fields = {}
        if brand: custom_fields['brand'] = brand
        if color: custom_fields['color'] = color
        if id_number: custom_fields['id_number'] = id_number
        if key_type: custom_fields['key_type'] = key_type
        
        update_data = {
            "title": title,
            "type": item_type if item_type in ['Lost', 'Found'] else 'Found',
            "category": category,
            "description": description,
            "location": location,
            "date_observed": date_observed,
            "status": status,
            "contact_info": contact_info,
            "image_path": image_path,
            "video_path": video_path,
            "custom_fields": custom_fields,
            "updated_at": datetime.now(timezone.utc)
        }
        
        database.items.update_one({"_id": obj_id}, {"$set": update_data})
        flash(f"Item '{title}' updated successfully!", "success")
        return redirect(url_for('item_detail', item_id=item_id))
        
    return render_template('edit_item.html', item=item)

# -------------------------------------------------------------
# SECOND HALF: Delete Item Post (Delete - PyMongo delete_one)
# -------------------------------------------------------------
@app.route('/delete-item/<item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    try:
        obj_id = ObjectId(item_id)
    except (InvalidId, TypeError):
        abort(404)
        
    database = get_db()
    item = database.items.find_one({"_id": obj_id})
    if not item:
        abort(404)
        
    # Access check: Owner or Admin
    is_owner = str(item.get('uploaded_by')) == session['user_id']
    is_admin = session.get('user_role') == 'admin'
    if not (is_owner or is_admin):
        flash("You do not have permission to delete this post.", "danger")
        return redirect(url_for('item_detail', item_id=item_id))
        
    # Delete media files from disk
    delete_media_file(item.get('image_path'))
    delete_media_file(item.get('video_path'))
    
    # Delete any associated claims
    database.claims.delete_many({"item_id": obj_id})
    
    # Delete item document
    database.items.delete_one({"_id": obj_id})
    
    flash(f"Post '{item.get('title')}' and its media were deleted successfully.", "info")
    return redirect(url_for('my_posts'))

# -------------------------------------------------------------
# SECOND HALF: Mark as Returned / Toggle Status (update_one)
# -------------------------------------------------------------
@app.route('/item/<item_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(item_id):
    try:
        obj_id = ObjectId(item_id)
    except (InvalidId, TypeError):
        abort(404)
        
    database = get_db()
    item = database.items.find_one({"_id": obj_id})
    if not item:
        abort(404)
        
    is_owner = str(item.get('uploaded_by')) == session['user_id']
    is_admin = session.get('user_role') == 'admin'
    if not (is_owner or is_admin):
        flash("Permission denied.", "danger")
        return redirect(url_for('item_detail', item_id=item_id))
        
    new_status = request.form.get('status')
    if not new_status:
        new_status = 'Returned' if item.get('status') == 'Available' else 'Available'
        
    database.items.update_one({"_id": obj_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}})
    flash(f"Item status updated to '{new_status}'!", "success")
    return redirect(request.referrer or url_for('item_detail', item_id=item_id))

# -------------------------------------------------------------
# SECOND HALF: My Posts Dashboard
# -------------------------------------------------------------
@app.route('/my-posts')
@login_required
def my_posts():
    database = get_db()
    user_id_obj = ObjectId(session['user_id'])
    
    my_items = list(database.items.find({"uploaded_by": user_id_obj}).sort("created_at", -1))
    
    # Add claims count to each item
    for item in my_items:
        item['claims_count'] = database.claims.count_documents({"item_id": item['_id']})
        item['pending_claims_count'] = database.claims.count_documents({"item_id": item['_id'], "status": "Pending"})
        
    return render_template('my_posts.html', items=my_items)

# -------------------------------------------------------------
# SECOND HALF: Claims Workflow (Create & View Claims)
# -------------------------------------------------------------
@app.route('/item/<item_id>/claim', methods=['POST'])
@login_required
def submit_claim(item_id):
    try:
        obj_id = ObjectId(item_id)
    except (InvalidId, TypeError):
        abort(404)
        
    database = get_db()
    item = database.items.find_one({"_id": obj_id})
    if not item:
        abort(404)
        
    # Cannot claim own item
    if str(item.get('uploaded_by')) == session['user_id']:
        flash("You cannot submit a claim on your own post.", "warning")
        return redirect(url_for('item_detail', item_id=item_id))
        
    user_id_obj = ObjectId(session['user_id'])
    
    # Check if already claimed
    existing_claim = database.claims.find_one({"item_id": obj_id, "claimant_id": user_id_obj})
    if existing_claim:
        flash("You have already submitted a claim for this item.", "info")
        return redirect(url_for('item_detail', item_id=item_id))
        
    proof_description = request.form.get('proof_description', '').strip()
    claimant_phone = request.form.get('claimant_phone', '').strip()
    
    if not proof_description:
        flash("Please provide detailed proof of ownership.", "danger")
        return redirect(url_for('item_detail', item_id=item_id))
        
    claim_doc = {
        "item_id": obj_id,
        "item_title": item.get('title'),
        "item_type": item.get('type'),
        "item_image_path": item.get('image_path'),
        "item_category": item.get('category'),
        "uploader_id": item.get('uploaded_by'),
        "uploader_name": item.get('uploader_name'),
        "claimant_id": user_id_obj,
        "claimant_name": session.get('username'),
        "claimant_email": session.get('user_email'),
        "claimant_phone": claimant_phone,
        "proof_description": proof_description,
        "status": "Pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    database.claims.insert_one(claim_doc)
    flash("Your claim request has been submitted to the finder/poster for verification!", "success")
    return redirect(url_for('my_claims'))

@app.route('/my-claims')
@login_required
def my_claims():
    database = get_db()
    user_id_obj = ObjectId(session['user_id'])
    
    # Claims made by me
    claims_by_me = list(database.claims.find({"claimant_id": user_id_obj}).sort("created_at", -1))
    
    # Claims received on my items
    claims_on_my_items = list(database.claims.find({"uploader_id": user_id_obj}).sort("created_at", -1))
    
    return render_template(
        'my_claims.html',
        claims_by_me=claims_by_me,
        claims_on_my_items=claims_on_my_items
    )

@app.route('/claim/<claim_id>/action', methods=['POST'])
@login_required
def claim_action(claim_id):
    try:
        obj_id = ObjectId(claim_id)
    except (InvalidId, TypeError):
        abort(404)
        
    database = get_db()
    claim = database.claims.find_one({"_id": obj_id})
    if not claim:
        abort(404)
        
    # Check permissions: must be post owner or admin
    is_uploader = str(claim.get('uploader_id')) == session['user_id']
    is_admin = session.get('user_role') == 'admin'
    if not (is_uploader or is_admin):
        flash("You do not have permission to act on this claim.", "danger")
        return redirect(url_for('my_claims'))
        
    action = request.form.get('action') # 'Approved' or 'Rejected'
    if action not in ['Approved', 'Rejected']:
        flash("Invalid action.", "danger")
        return redirect(url_for('my_claims'))
        
    database.claims.update_one(
        {"_id": obj_id},
        {"$set": {"status": action, "decided_at": datetime.now(timezone.utc)}}
    )
    
    # If approved, automatically update item status to "Returned"
    if action == 'Approved':
        database.items.update_one(
            {"_id": claim['item_id']},
            {"$set": {"status": "Returned", "updated_at": datetime.now(timezone.utc)}}
        )
        flash(f"Claim from '{claim.get('claimant_name')}' approved! Item marked as Returned.", "success")
    else:
        flash(f"Claim from '{claim.get('claimant_name')}' has been rejected.", "info")
        
    return redirect(request.referrer or url_for('my_claims'))

# -------------------------------------------------------------
# SECOND HALF: Admin Dashboard (PyMongo Aggregation Pipelines)
# -------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    database = get_db()
    
    # Overall counts
    total_users = database.users.count_documents({})
    total_items = database.items.count_documents({})
    total_lost = database.items.count_documents({"type": "Lost"})
    total_found = database.items.count_documents({"type": "Found"})
    total_returned = database.items.count_documents({"status": "Returned"})
    total_claims = database.claims.count_documents({})
    pending_claims = database.claims.count_documents({"status": "Pending"})
    
    # Aggregation 1: Group items by category ($group, $sort)
    cat_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    category_breakdown = list(database.items.aggregate(cat_pipeline))
    
    # Aggregation 2: Group items by campus location ($group, $sort, $limit)
    loc_pipeline = [
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 6}
    ]
    location_breakdown = list(database.items.aggregate(loc_pipeline))
    
    # Aggregation 3: User count by role ($group)
    role_pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    role_breakdown = list(database.users.aggregate(role_pipeline))
    
    # Fetch lists for admin moderation
    all_users = list(database.users.find({}).sort("created_at", -1))
    all_items = list(database.items.find({}).sort("created_at", -1))
    all_claims = list(database.claims.find({}).sort("created_at", -1))
    
    return render_template(
        'admin_dashboard.html',
        stats={
            'total_users': total_users,
            'total_items': total_items,
            'total_lost': total_lost,
            'total_found': total_found,
            'total_returned': total_returned,
            'total_claims': total_claims,
            'pending_claims': pending_claims
        },
        category_breakdown=category_breakdown,
        location_breakdown=location_breakdown,
        role_breakdown=role_breakdown,
        all_users=all_users,
        all_items=all_items,
        all_claims=all_claims
    )

@app.route('/admin/user/<user_id>/role', methods=['POST'])
@admin_required
def admin_change_role(user_id):
    try:
        obj_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        abort(404)
        
    new_role = request.form.get('role')
    if new_role not in ['student', 'staff', 'security', 'admin']:
        flash("Invalid role.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    database = get_db()
    database.users.update_one({"_id": obj_id}, {"$set": {"role": new_role}})
    flash("User role updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[Starting] Campus Lost-and-Found Media Portal on http://0.0.0.0:{port} ...")
    app.run(debug=True, host='0.0.0.0', port=port)

