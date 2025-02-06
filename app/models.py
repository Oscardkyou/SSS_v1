from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    unique_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    children = db.relationship('Child', backref='parent', lazy=True)

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
