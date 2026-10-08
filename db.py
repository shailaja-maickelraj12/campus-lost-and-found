import os
import logging
from datetime import datetime, timezone
import dns.resolver
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from werkzeug.security import generate_password_hash
import mongomock
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LostFoundDB")

# Configure public DNS resolvers (Google & Cloudflare) to ensure MongoDB Atlas SRV records resolve seamlessly
try:
    custom_resolver = dns.resolver.Resolver()
    custom_resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
    dns.resolver.default_resolver = custom_resolver
except Exception as dns_err:
    logger.debug("DNS configuration notice: %s", dns_err)

_db_instance = None
_is_mock = False

def init_db():
    global _db_instance, _is_mock
    if _db_instance is not None:
        return _db_instance

    try:
        masked_uri = Config.MONGO_URI.split('@')[-1] if '@' in Config.MONGO_URI else Config.MONGO_URI
        logger.info("[Database] Connecting to MongoDB instance (%s)...", masked_uri)
        real_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=8000)
        real_client.admin.command('ping')
        _db_instance = real_client[Config.DB_NAME]
        _is_mock = False
        logger.info("[Database] Connected successfully to MongoDB Atlas (%s)", Config.DB_NAME)
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as err:
        logger.warning("[Database] Could not connect to MongoDB Atlas (%s). Falling back to mongomock for development/demo.", err)
        mock_client = mongomock.MongoClient()
        _db_instance = mock_client[Config.DB_NAME]
        _is_mock = True
        logger.info("[Database] Running with mongomock (PyMongo compatible in-memory engine).")

    # Initialize collections and indexes
    try:
        _db_instance.users.create_index([("email", ASCENDING)], unique=True)
        _db_instance.users.create_index([("username", ASCENDING)], unique=True)
        _db_instance.items.create_index([("title", TEXT), ("description", TEXT), ("location", TEXT)])
        _db_instance.items.create_index([("category", ASCENDING)])
        _db_instance.items.create_index([("status", ASCENDING)])
        _db_instance.items.create_index([("created_at", ASCENDING)])
    except Exception as e:
        logger.debug("Index creation notice: %s", e)

    # Ensure default admin account always exists
    try:
        admin_email = "admin@campus.edu"
        if not _db_instance.users.find_one({"email": admin_email}):
            _db_instance.users.insert_one({
                "username": "campus_admin",
                "email": admin_email,
                "password_hash": generate_password_hash("admin123"),
                "role": "admin",
                "phone": "+91 99999 00000",
                "department": "Campus Security & Admin",
                "created_at": datetime.now(timezone.utc)
            })
            logger.info("[Database] Default admin account ensured: admin@campus.edu / admin123")
    except Exception as e:
        logger.warning("Default admin creation notice: %s", e)

    return _db_instance

def get_db():
    global _db_instance
    if _db_instance is None:
        return init_db()
    return _db_instance

def is_mock_db():
    return _is_mock
