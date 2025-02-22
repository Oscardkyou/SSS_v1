import os
from flask import Blueprint, jsonify, request, render_template, current_app, url_for
from werkzeug.utils import secure_filename
from .models import db, Parent, Child
import uuid
from PIL import Image
from flask_caching import Cache
from functools import wraps
import io
import time
import logging
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cache = Cache()

def init_cache(app):
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def optimize_image(image_file):
    """Optimize image for faster loading"""
    img = Image.open(image_file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize if too large
    max_size = 1024
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.LANCZOS)

    # Save with optimization
    output = io.BytesIO()
    img.save(output, format='JPEG', optimize=True, quality=85)
    output.seek(0)
    return output

def api_documentation(f):
    """Decorator for API documentation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    # Add API documentation
    if not hasattr(f, 'api_doc'):
        f.api_doc = {
            'endpoint': f.__name__,
            'methods': getattr(f, 'methods', ['GET']),
            'description': f.__doc__,
            'parameters': getattr(f, 'parameters', {}),
            'responses': getattr(f, 'responses', {})
        }
    return decorated_function

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/onboarding/<unique_id>')
def onboarding(unique_id):
    parent = Parent.query.filter_by(unique_id=unique_id).first_or_404()
    return render_template('onboarding.html', parent=parent)

@bp.route('/register')
def register():
    return render_template('onboarding.html')

@bp.route('/register/<registration_id>')
def register_with_id(registration_id):
    return render_template('onboarding.html', registration_id=registration_id)

@bp.route('/api/generate_link', methods=['POST'])
@api_documentation
def generate_link():
    """
    Generate onboarding link for parent and child.

    Parameters:
        - parent_first_name (str): First name of parent
        - parent_last_name (str): Last name of parent
        - child_first_name (str): First name of child

    Returns:
        - success (bool): Operation status
        - onboarding_url (str): Generated onboarding URL
    """
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

    onboarding_url = url_for('main.onboarding', unique_id=parent.unique_id, _external=True, _scheme='https')
    return jsonify({
        'success': True,
        'onboarding_url': onboarding_url
    })

@bp.route('/api/upload_photo', methods=['POST'])
@api_documentation
def upload_photo():
    """
    Upload and process photo for parent.

    Parameters:
        - photo (file): Photo file (jpg, png, jpeg)
        - parent_id (str): Parent identifier

    Returns:
        - success (bool): Operation status
        - message (str): Status message
    """
    logger.info("Received upload request")
    logger.info("Files:", request.files)
    logger.info("Form data:", request.form)

    if 'photo' not in request.files:
        return jsonify({'error': 'Нет файла фотографии'}), 400

    photo = request.files['photo']
    parent_id = request.form.get('parent_id')

    logger.info(f"Photo filename: {photo.filename}")
    logger.info(f"Parent ID: {parent_id}")

    if not photo or not parent_id:
        return jsonify({'error': 'Неверные данные'}), 400

    try:
        parent = Parent.query.get_or_404(parent_id)

        if photo and allowed_file(photo.filename):
            # Create upload folder if it doesn't exist
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Optimize image
            optimized_photo = optimize_image(photo)

            filename = secure_filename(f"{parent.unique_id}_{photo.filename}")
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            logger.info(f"Saving to path: {photo_path}")

            # Save optimized image
            with open(photo_path, 'wb') as f:
                f.write(optimized_photo.getvalue())

            parent.photo_path = filename
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Фото успешно загружено'
            })

        return jsonify({'error': 'Недопустимый формат файла'}), 400

    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        return jsonify({'error': f'Ошибка при загрузке: {str(e)}'}), 500
