import os
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from dotenv import load_dotenv

load_dotenv()

from models import db, bcrypt, User, Todo

# ============================================================
# App initialization
# ============================================================
app = Flask(__name__)
CORS(app)

# ============================================================
# Configuration (single source of truth)
# ============================================================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-12345')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-12345')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration (supports postgres:// from Render)
database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

# ============================================================
# Initialize extensions
# ============================================================
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

CATEGORY_COLORS = {
    'work': '#3b82f6',
    'personal': '#10b981',
    'shopping': '#f59e0b',
    'health': '#ef4444',
    'learning': '#8b5cf6',
    'urgent': '#dc2626',
    'other': '#6b7280',
}


# ============================================================
# Routes
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running',
        'environment': os.getenv('FLASK_ENV', 'development'),
    })


# ---------- Auth ----------
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'error': 'Missing required fields'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 400

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Missing email or password'}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict(),
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- Todos ----------
@app.route('/api/todos', methods=['GET'])
@jwt_required()
def get_todos():
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass

        todos = Todo.query.filter_by(user_id=user_id).all()
        return jsonify({'todos': [t.to_dict() for t in todos]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/todos', methods=['POST'])
@jwt_required()
def create_todo():
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass

        data = request.get_json() or {}
        todo = Todo(
            title=data.get('title'),
            description=data.get('description', ''),
            category=data.get('category', 'other'),
            priority=data.get('priority', 'medium'),
            user_id=user_id,
        )

        if data.get('due_date'):
            todo.due_date = datetime.fromisoformat(
                data['due_date'].replace('Z', '+00:00')
            )

        db.session.add(todo)
        db.session.commit()

        return jsonify({
            'message': 'Todo created successfully',
            'todo': todo.to_dict(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass

        todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404

        data = request.get_json() or {}
        if 'title' in data:
            todo.title = data['title']
        if 'description' in data:
            todo.description = data['description']
        if 'category' in data:
            todo.category = data['category']
        if 'priority' in data:
            todo.priority = data['priority']
        if 'completed' in data:
            todo.update_completion(data['completed'])
        if 'due_date' in data:
            if data['due_date']:
                todo.due_date = datetime.fromisoformat(
                    data['due_date'].replace('Z', '+00:00')
                )
            else:
                todo.due_date = None

        db.session.commit()
        return jsonify({
            'message': 'Todo updated successfully',
            'todo': todo.to_dict(),
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass

        todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404

        db.session.delete(todo)
        db.session.commit()
        return jsonify({'message': 'Todo deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ---------- Statistics ----------
@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass

        todos = Todo.query.filter_by(user_id=user_id).all()
        total = len(todos)
        completed = sum(1 for t in todos if t.completed)
        pending = total - completed

        category_stats = {c: sum(1 for t in todos if t.category == c) for c in Todo.CATEGORIES}
        priority_stats = {p: sum(1 for t in todos if t.priority == p) for p in Todo.PRIORITIES}

        return jsonify({
            'total': total,
            'completed': completed,
            'pending': pending,
            'completion_rate': round((completed / total * 100), 2) if total > 0 else 0,
            'category_stats': category_stats,
            'priority_stats': priority_stats,
            'category_colors': CATEGORY_COLORS,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# Database init & startup
# ============================================================
with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully!")
    print("🌐 Environment:", os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))

    print("🚀 Starting Professional Todo App...")
    print(f"🌐 Web Interface: http://0.0.0.0:{port}")
    print(f"🔧 Debug Mode: {debug_mode}")

    app.run(debug=debug_mode, host='0.0.0.0', port=port)