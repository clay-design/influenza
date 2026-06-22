from dotenv import load_dotenv
load_dotenv()

import os
import logging
from flask import Flask, session, request
from config import Config
from models import init_db
import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    init_db(app)

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

app = create_app()

@app.route('/init-db')
def init_db_route():
    try:
        init_db(app)
        return "✅ Database initialized successfully! Tables created."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])