import os
from flask import Blueprint, jsonify, request, render_template, current_app, url_for
from werkzeug.utils import secure_filename
from .models import db, Parent, Child
import uuid

bp = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/onboarding/<unique_id>')
def onboarding(unique_id):
    parent = Parent.query.filter_by(unique_id=unique_id).first_or_404()
    return render_template('onboarding.html', parent=parent)

@bp.route('/api/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    if not data or 'parent_first_name' not in data or 'parent_last_name' not in data or 'child_first_name' not in data:
        return jsonify({'error': 'Неполные данные'}), 400

    parent = Parent(
        first_name=data['parent_first_name'],
        last_name=data['parent_last_name']
    )
    child = Child(
        first_name=data['child_first_name'],
        parent=parent
    )
    
    db.session.add(parent)
    db.session.add(child)
    db.session.commit()

    onboarding_url = url_for('main.onboarding', unique_id=parent.unique_id, _external=True)
    return jsonify({
        'success': True,
        'onboarding_url': onboarding_url
    })

@bp.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'Нет файла фотографии'}), 400
    
    photo = request.files['photo']
    parent_id = request.form.get('parent_id')
    
    if not photo or not parent_id:
        return jsonify({'error': 'Неверные данные'}), 400

    parent = Parent.query.get_or_404(parent_id)
    
    if photo and allowed_file(photo.filename):
        filename = secure_filename(f"{parent.unique_id}_{photo.filename}")
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        
        parent.photo_path = filename
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Фото успешно загружено'
        })
    
    return jsonify({'error': 'Недопустимый формат файла'}), 400
