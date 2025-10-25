import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import db, bcrypt, User, Todo

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-12345')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-12345')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Database configuration for production
database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

# Color schemes for frontend
CATEGORY_COLORS = {
    'work': {'color': '#3B82F6', 'icon': '💼', 'bg': 'bg-blue-100', 'text': 'text-blue-800'},
    'personal': {'color': '#10B981', 'icon': '🏠', 'bg': 'bg-green-100', 'text': 'text-green-800'},
    'shopping': {'color': '#F59E0B', 'icon': '🛒', 'bg': 'bg-yellow-100', 'text': 'text-yellow-800'},
    'health': {'color': '#EF4444', 'icon': '🏥', 'bg': 'bg-red-100', 'text': 'text-red-800'},
    'learning': {'color': '#8B5CF6', 'icon': '📚', 'bg': 'bg-purple-100', 'text': 'text-purple-800'},
    'urgent': {'color': '#DC2626', 'icon': '🚨', 'bg': 'bg-red-100', 'text': 'text-red-800'},
    'other': {'color': '#6B7280', 'icon': '📌', 'bg': 'bg-gray-100', 'text': 'text-gray-800'}
}

PRIORITY_COLORS = {
    'high': {'color': '#DC2626', 'icon': '🔴', 'bg': 'bg-red-100', 'text': 'text-red-800'},
    'medium': {'color': '#F59E0B', 'icon': '🟡', 'bg': 'bg-yellow-100', 'text': 'text-yellow-800'},
    'low': {'color': '#10B981', 'icon': '🟢', 'bg': 'bg-green-100', 'text': 'text-green-800'}
}

# JWT configuration to handle tokens properly
@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Authorization required',
        'message': 'Missing access token'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid token',
        'message': 'Token signature is invalid'
    }), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token expired',
        'message': 'Token has expired'
    }), 401

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'Server is running',
        'environment': os.getenv('FLASK_ENV', 'development')
    })

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token with user ID
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token with user ID as string
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Todo Routes
@app.route('/api/todos', methods=['GET'])
@jwt_required()
def get_todos():
    try:
        user_id = get_jwt_identity()
        
        # Convert to integer if needed
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user ID in token'}), 422
        
        todos = Todo.query.filter_by(user_id=user_id_int).order_by(Todo.created_at.desc()).all()
        
        return jsonify({
            'todos': [todo.to_dict() for todo in todos],
            'category_colors': CATEGORY_COLORS,
            'priority_colors': PRIORITY_COLORS
        })
        
    except Exception as e:
        print(f"❌ Error in get_todos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos', methods=['POST'])
@jwt_required()
def create_todo():
    try:
        user_id = get_jwt_identity()
        
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Convert user_id to integer
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user ID in token'}), 422
        
        # Validate category and priority
        category = data.get('category', 'other')
        if category not in Todo.CATEGORIES:
            category = 'other'
            
        priority = data.get('priority', 'medium')
        if priority not in Todo.PRIORITIES:
            priority = 'medium'
        
        # Parse due date
        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                pass
        
        todo = Todo(
            title=data['title'],
            description=data.get('description', ''),
            category=category,
            priority=priority,
            due_date=due_date,
            user_id=user_id_int
        )
        
        db.session.add(todo)
        db.session.commit()
        
        return jsonify({
            'message': 'Todo created successfully',
            'todo': todo.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in create_todo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    try:
        user_id = get_jwt_identity()
        
        # Convert user_id to integer
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user ID in token'}), 422
        
        todo = Todo.query.filter_by(id=todo_id, user_id=user_id_int).first()
        
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            todo.title = data['title']
        if 'description' in data:
            todo.description = data['description']
        if 'category' in data and data['category'] in Todo.CATEGORIES:
            todo.category = data['category']
        if 'priority' in data and data['priority'] in Todo.PRIORITIES:
            todo.priority = data['priority']
        if 'due_date' in data:
            if data['due_date']:
                try:
                    todo.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except ValueError:
                    todo.due_date = None
            else:
                todo.due_date = None
        if 'completed' in data:
            todo.update_completion(data['completed'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Todo updated successfully',
            'todo': todo.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in update_todo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    try:
        user_id = get_jwt_identity()
        
        # Convert user_id to integer
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user ID in token'}), 422
        
        todo = Todo.query.filter_by(id=todo_id, user_id=user_id_int).first()
        
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        
        db.session.delete(todo)
        db.session.commit()
        
        return jsonify({'message': 'Todo deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in delete_todo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    try:
        user_id = get_jwt_identity()
        
        # Convert user_id to integer
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user ID in token'}), 422
        
        todos = Todo.query.filter_by(user_id=user_id_int).all()
        
        total = len(todos)
        completed = len([t for t in todos if t.completed])
        pending = total - completed
        
        category_stats = {}
        priority_stats = {}
        
        for todo in todos:
            category_stats[todo.category] = category_stats.get(todo.category, 0) + 1
            priority_stats[todo.priority] = priority_stats.get(todo.priority, 0) + 1
        
        return jsonify({
            'total': total,
            'completed': completed,
            'pending': pending,
            'completion_rate': round((completed / total * 100), 2) if total > 0 else 0,
            'category_stats': category_stats,
            'priority_stats': priority_stats,
            'category_colors': CATEGORY_COLORS,
            'priority_colors': PRIORITY_COLORS
        })
        
    except Exception as e:
        print(f"❌ Error in get_statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Initialize database
with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully!")
    print("🌐 Environment:", os.getenv('FLASK_ENV', 'development'))
    print("🗄️ Database URL:", os.getenv('DATABASE_URL', 'sqlite:///app.db'))

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    print("🚀 Starting Professional Todo App...")
    print(f"🌐 Web Interface: http://0.0.0.0:{port}")
    print(f"🔧 Debug Mode: {debug_mode}")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)