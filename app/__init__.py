import os
from flask import Flask
from .models import db
from .routes import bp, init_cache
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Убедимся, что папка для загрузки существует
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    init_cache(app)
    
    with app.app_context():
        db.create_all()
    
    app.register_blueprint(bp)
    
    return app
