import os
from flask import Flask
from .models import db
from .routes import bp
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Убедимся, что папка для загрузки существует
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    app.register_blueprint(bp)
    
    return app
