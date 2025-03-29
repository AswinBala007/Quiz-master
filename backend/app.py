import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import db, bcrypt, jwt, migrate, cache
from jobs.celery_factory import celery_init_app
# from flask_caching import Cache

# Load environment variables from .env file
load_dotenv()

def create_app(config=None):
    """Application factory function to create and configure the Flask app"""
    app = Flask(__name__)
    CORS(app)

    # Configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your_secret_key")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "your_jwt_secret_key")
    
    # Cache configuration
    app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE")
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 30))
    app.config["CACHE_REDIS_HOST"] = os.getenv("CACHE_REDIS_HOST")
    app.config["CACHE_REDIS_PORT"] = int(os.getenv("CACHE_REDIS_PORT", 6379))
    
    # Celery configuration
    app.config["CELERY"] = {
        "broker_url": os.getenv("CELERY_BROKER_URL"),
        "result_backend": os.getenv("CELERY_RESULT_BACKEND"),
        "timezone": os.getenv("TIMEZONE", "UTC"),
    }
    
    # Apply custom configuration if provided
    if config:
        app.config.update(config)

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    app.cache = cache

    # Register Blueprints
    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.user import user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    # Create admin if not exists
    with app.app_context():
        try:
            db.create_all()
            from models import create_admin
            create_admin()
        except Exception as e:
            print(f"Warning: Database initialization error - {str(e)}")
            print("Run 'python setup_db.py' to set up the database correctly")

    @app.route("/")
    def home():
        return {"message": "Welcome to Quiz Master API"}

    return app

# Create the Flask app
app = create_app()
celery_app = celery_init_app(app)

if __name__ == "__main__":
    app.run()  # Run the app in debug mode
