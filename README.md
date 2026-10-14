# 🎓 Campus Lost-and-Found Media Portal

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-lightgrey.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-green.svg?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205.3-purple.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)

A modern, role-based web portal designed for college campuses to report, track, and recover lost and found belongings. Built with **Flask** and **MongoDB Atlas**, it combines multimedia verification (photographs and short video footage), flexible NoSQL embedded document structures, a verified claim recovery workflow, and an administrative analytics dashboard.

---

## 📌 Table of Contents
- [Problem Statement & Overview](#-problem-statement--overview)
- [Key Features](#-key-features)
- [Technical Architecture](#-technical-architecture)
- [NoSQL Database Design & Schema](#-nosql-database-design--schema)
- [Media Storage Strategy](#-media-storage-strategy)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Local Setup](#-installation--local-setup)
- [Default Login Credentials](#-default-login-credentials)
- [Application Routes](#-application-routes)
- [Viva & Technical Defense Highlights](#-viva--technical-defense-highlights)

---

## 📖 Problem Statement & Overview
On college campuses, lost-and-found items are typically reported across unorganized WhatsApp groups, unofficial social media channels, or physical notice boards. This leads to:
- High difficulty in searching for past reports.
- Lack of authentic photo/video proof.
- No secure way to verify true ownership before handing over valuable belongings.

**Campus Lost-and-Found Media Portal** solves this by centralizing campus recovery operations into a unified platform with role-based access, instant keyword search, dynamic category fields, and proof-of-ownership claim verification.

---

## ✨ Key Features

1. **Full CRUD Operations**:
   - **Create**: Report Lost or Found items with title, location, category, description, and proof files.
   - **Read**: Browse all items with multi-faceted search (keyword, item type, category).
   - **Update**: Edit post details, replace media, or toggle status (`Available` ↔ `Returned`).
   - **Delete**: Remove posts and automatically clean associated media files and claim records.

2. **Multimedia Upload & Native Streaming**:
   - Upload high-resolution photos and short video clips (`.mp4`, `.webm`).
   - In-browser HTML5 video player for visual verification.
   - Unique UUID prefixing and Werkzeug sanitization to prevent filename collisions and security vulnerabilities.

3. **NoSQL Polymorphic Embedded Documents**:
   - Leverages MongoDB's schema flexibility using embedded sub-documents (`custom_fields`).
   - Different categories store unique attributes without table migrations (e.g., ID cards store `student_name` and `department`, while calculators store `brand` and `serial_number`).

4. **Claim & Ownership Verification Workflow**:
   - Claimants submit proof of ownership (answers to security questions, identification numbers, purchase details).
   - Original uploaders can review, approve, or reject claims with instant status feedback.

5. **Admin Analytics Dashboard**:
   - Real-time statistics powered by **MongoDB Aggregation Pipelines** (`$group`, `$sort`).
   - Visual KPI cards for Total Reports, Lost vs. Found counts, and Resolution rates.
   - Comprehensive administrative control over all campus listings and claims.

6. **Authentication & Role-Based Authorization**:
   - Secure account registration and login.
   - Passwords hashed with salted PBKDF2:SHA-256 via `werkzeug.security`.
   - Custom decorators (`@login_required`, `@admin_required`) protecting privileged actions.

---

## 🛠️ Technical Architecture

The application implements the **Model-View-Template (MVT)** architectural pattern:

* **Model Layer (`db.py`)**: MongoDB Atlas cloud database managed via `pymongo`. Features an automatic in-memory `mongomock` fallback for offline resilience.
* **Controller / Application Logic (`app.py`, `helpers.py`)**: Flask WSGI application handling routing, session cookies, file validation, and business rules.
* **View / Presentation Layer (`templates/`, `static/`)**: Jinja2 templates extending a shared `base.html` layout, styled with Bootstrap 5.3 and Bootstrap Icons.

```
+-------------------------------------------------------------+
|                     Client Browser                          |
+------------------------------+------------------------------+
                               | HTTP GET / POST
                               v
+-------------------------------------------------------------+
|                      Flask Application                      |
|  - Routing (@app.route)          - Custom Decorators        |
|  - Session Authentication         - Werkzeug File & Hashing  |
|  - Jinja2 Template Engine        - Input Validation         |
+------------------------------+------------------------------+
                               | PyMongo Driver
                               v
+-------------------------------------------------------------+
|                   MongoDB Atlas (Cloud)                     |
|  - users collection              - items collection         |
|  - claims collection             - Aggregation Pipelines    |
+-------------------------------------------------------------+
```

---

## 🗄️ NoSQL Database Design & Schema

The database `campus_lost_found_db` consists of 3 primary collections:

### 1. `items` Collection (Showcases Embedded Documents)
```json
{
  "_id": ObjectId("66ff8a1b2c3d4e5f6a7b8c9d"),
  "title": "Casio fx-991EX Scientific Calculator",
  "type": "Found",
  "category": "Electronics & Gadgets",
  "description": "Found on the second bench in Seminar Hall B.",
  "location": "Seminar Hall B, Block 2",
  "date_observed": "2026-10-07",
  "status": "Available",
  "uploaded_by": ObjectId("66ff7c..."),
  "uploader_name": "student_user",
  "image_path": "uploads/images/sample_calculator.svg",
  "video_path": "uploads/videos/fab60d0cef_video.mp4",
  "custom_fields": {
    "brand": "Casio",
    "model": "fx-991EX ClassWiz",
    "color": "Black",
    "serial_number": "EX991-8841",
    "has_protective_cover": "Yes"
  },
  "created_at": ISODate("2026-10-07T12:30:00Z")
}
```

### 2. `users` Collection
```json
{
  "_id": ObjectId("66ff7c1b2c3d4e5f6a7b8c01"),
  "username": "campus_admin",
  "email": "admin@campus.edu",
  "password_hash": "scrypt:32768:8:1$...",
  "role": "admin",
  "department": "Campus Security & Admin",
  "phone": "+91 99999 00000",
  "created_at": ISODate("2026-10-03T16:00:00Z")
}
```

### 3. `claims` Collection
```json
{
  "_id": ObjectId("66ff9d1b2c3d4e5f6a7b8c22"),
  "item_id": ObjectId("66ff8a1b2c3d4e5f6a7b8c9d"),
  "claimant_id": ObjectId("66ff7d..."),
  "claimant_name": "Kiruthika",
  "claimant_email": "kiruthika@campus.edu",
  "proof_description": "My calculator has my initials 'KM' scratched lightly on the battery cover.",
  "status": "Pending",
  "created_at": ISODate("2026-10-08T09:15:00Z")
}
```

---

## 📷 Media Storage Strategy

This project employs the **Hybrid Storage Architecture Pattern**:
1. **Physical Files on Server**:
   - Uploaded photos are stored under `static/uploads/images/`.
   - Uploaded video footage is stored under `static/uploads/videos/`.
2. **Metadata & Paths in MongoDB**:
   - Only the clean relative path (`uploads/images/...`) is stored in the database document.
3. **Benefits**:
   - Avoids the strict 16 MB MongoDB BSON document limit.
   - Eliminates database memory bloat and keeps queries instantaneous.
   - Enables native browser caching for images and hardware-accelerated HTTP byte-range streaming for HTML5 video.

---

## 📁 Project Directory Structure

```text
PROJECT_WNI/
├── .env                       # Environment configuration (MongoDB URI, secret keys)
├── .env.example               # Template for environment configuration
├── .gitignore                 # Excludes .env, pycache, and temporary uploads
├── README.md                  # Comprehensive project documentation
├── requirements.txt           # Python library dependencies
├── config.py                  # Central configuration loader
├── db.py                      # MongoDB connection manager & admin account seeder
├── helpers.py                 # Media handling routines & route decorators
├── app.py                     # Main Flask application & route controllers
├── seed_data.py               # Standalone database population script
│
├── templates/                 # Jinja2 HTML presentation templates
│   ├── base.html              # Core layout (Navbar, flash alerts, Footer)
│   ├── home.html              # Homepage with KPI metrics & recent listings
│   ├── items.html             # Item catalog with live search & category filters
│   ├── item_detail.html       # Single item view, embedded details, claim workflow
│   ├── add_item.html          # New item reporting form with media upload
│   ├── edit_item.html         # Item modification form
│   ├── my_posts.html          # User's uploaded posts management
│   ├── my_claims.html         # Claims submitted and received
│   ├── login.html             # Login portal (includes Quick-Fill Admin button)
│   ├── register.html          # User registration portal
│   └── admin_dashboard.html   # Analytical control center for administrators
│
└── static/                    # Static web assets
    ├── css/
    │   └── style.css          # Custom styling and animations
    ├── js/
    │   └── main.js            # Client-side dynamic interactions
    └── uploads/               # Upload destination for photos and video evidence
        ├── images/
        └── videos/
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- **Git** installed.
- An active internet connection (to connect to MongoDB Atlas cloud cluster).

### 2. Clone the Repository
```bash
git clone https://github.com/shailaja-maickelraj12/campus-lost-and-found.git
cd campus-lost-and-found
```

### 3. Create & Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory (or copy from `.env.example`):
```env
SECRET_KEY=your_secure_flask_secret_key_2026
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.t0hhm2n.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=campus_lost_found_db
```

### 6. Run the Application
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default Login Credentials

A pre-configured administrator account is automatically initialized upon database connection:

| Role | Username / Email | Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin@campus.edu` | `admin123` | Full access to Admin Dashboard, all posts, and all claims |
| **Student** | *(Register via UI)* | *(User defined)* | Post items, claim items, manage personal reports |

*(Note: The login page includes a one-click **"Fill Admin Credentials"** button for quick demonstration).*

---

## 🚦 Application Routes

| Method | URL Endpoint | Description | Access Control |
|---|---|---|---|
| `GET` | `/` | Home page with metrics and recent items | Public |
| `GET` | `/items` | Search and filter catalog of lost/found items | Public |
| `GET` | `/items/<item_id>` | Detailed view of item, media, and claim form | Public |
| `GET, POST` | `/add-item` | Submit a new lost/found report with photos/video | `@login_required` |
| `GET, POST` | `/edit-item/<item_id>` | Edit an existing item post | Post Owner / Admin |
| `POST` | `/delete-item/<item_id>` | Permanently delete post and clean media files | Post Owner / Admin |
| `POST` | `/item/<item_id>/toggle-status` | Toggle between `Available` and `Returned` | Post Owner / Admin |
| `POST` | `/item/<item_id>/claim` | Submit proof of ownership claim | Logged-in User |
| `GET` | `/my-posts` | Manage items reported by current user | `@login_required` |
| `GET` | `/my-claims` | Track claims made and claims received on posts | `@login_required` |
| `POST` | `/claim/<claim_id>/action` | Approve or reject a claim on user's post | Post Owner / Admin |
| `GET` | `/admin/dashboard` | Administrative analytics & system management | `@admin_required` |
| `GET, POST` | `/login` | User and administrator sign-in | Public |
| `GET, POST` | `/register` | New student account registration | Public |
| `GET` | `/logout` | Terminate session and clear cookies | `@login_required` |

---

## 🎯 Viva & Technical Defense Highlights

### For Python Web Frameworks Examiner:
- **Why Flask?** Flask is an unopinionated, lightweight WSGI micro-framework that does not constrain developers to a relational ORM (like Django ORM). This makes Flask the premier choice for pairing with non-relational document stores like MongoDB.
- **Session Security**: Uses cryptographically signed client cookies via Flask `session` with a server `SECRET_KEY`.
- **Upload Safety**: Werkzeug `secure_filename()` eliminates path traversal attacks; `uuid4` prefixes prevent file collisions.
- **Modular Decorators**: Custom Python wrappers (`@login_required` and `@admin_required`) enforce declarative access control.

### For NoSQL Database Examiner:
- **Why MongoDB?** Lost and found items have heterogeneous, polymorphic attributes. Relational tables require numerous `NULL` columns or costly join tables. MongoDB stores dynamic category fields (`brand`, `serial_number`, `id_number`, `key_type`) naturally within embedded sub-documents (`custom_fields`).
- **Complete CRUD Demonstrated**:
  - `insert_one()`: Storing items, user profiles, and claim tickets.
  - `find()` & `find_one()`: Keyword regex queries (`$options: 'i'`) and primary key lookups.
  - `update_one()`: Atomic updates with `$set` for post editing and claim status updates.
  - `delete_one()` & `delete_many()`: Cascade post deletion and associated claims cleanup.
- **Aggregation Pipelines**: Real-time KPI metrics on the Admin Dashboard compute group-level metrics using `$match`, `$group`, and `$sort` directly inside the MongoDB query engine.

---

## 👩‍💻 Author
- **Developer**: Shailaja Maickelraj
- **GitHub**: [@shailaja-maickelraj12](https://github.com/shailaja-maickelraj12)
- **Repository**: [campus-lost-and-found](https://github.com/shailaja-maickelraj12/campus-lost-and-found)
