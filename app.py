from dotenv import load_dotenv
load_dotenv()

import os
import logging
from flask import Flask, session, request, g
from config import Config
from models import init_db, get_db
import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Explicitly initialize the database on startup (just in case)
    init_db(app)

    # -------------------- Auto‑init on first request --------------------
    @app.before_request
    def ensure_db():
        # Skip static files and the init‑db route itself to avoid recursion
        if request.endpoint in ('static', 'init_db_route'):
            return
        try:
            db = get_db()
            cursor = db.cursor()
            # Try a simple query to check if the users table exists
            if Config.DB_TYPE == 'postgresql':
                cursor.execute("SELECT 1 FROM users LIMIT 1")
            else:
                cursor.execute("SELECT 1 FROM users LIMIT 1")
        except Exception:
            # Table does not exist – initialize the database
            app.logger.info("Database tables missing – initializing...")
            init_db(app)
            app.logger.info("Database initialized successfully!")

    # ---------------------------------------------------------------------

    @app.before_request
    def refresh_session():
        if 'user' in session:
            session.permanent = True
            session.modified = True

    from routes.auth import auth_bp
    from routes.views import views_bp
    from routes.forms import forms_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(forms_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')

    return app

# Create the Flask app instance
app = create_app()

# -------------------- Fallback initialisation route --------------------
@app.route('/init-db')
def init_db_route():
    try:
        init_db(app)
        return "✅ Database initialized successfully! Tables created."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])