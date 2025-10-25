// Global variables
let currentUser = null;
let authToken = null;
let allTodos = [];
let currentFilter = 'all';

// API Base URL
const API_BASE = '/api';

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

// Authentication Functions
function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('currentUser');
    
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        showTodoDashboard();
        loadTodos();
        loadStatistics();
    } else {
        showAuthSection();
    }
}

function showAuthSection() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('todoDashboard').style.display = 'none';
}

function showTodoDashboard() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('todoDashboard').style.display = 'block';
    document.getElementById('usernameDisplay').textContent = currentUser.username;
}

async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        alert('Please enter both email and password');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            currentUser = data.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showTodoDashboard();
            loadTodos();
            loadStatistics();
            
            // Clear form
            document.getElementById('loginEmail').value = '';
            document.getElementById('loginPassword').value = '';
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        alert('Login error: ' + error.message);
    }
}

async function register() {
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    if (!username || !email || !password) {
        alert('Please fill all fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            currentUser = data.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showTodoDashboard();
            loadTodos();
            loadStatistics();
            
            // Clear form and show login
            document.getElementById('registerUsername').value = '';
            document.getElementById('registerEmail').value = '';
            document.getElementById('registerPassword').value = '';
            showLogin();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        alert('Registration error: ' + error.message);
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    showAuthSection();
}

function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

// Todo Functions
async function loadTodos() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/todos`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            allTodos = data.todos;
            renderTodos();
        } else {
            console.error('Error loading todos:', data.error);
        }
    } catch (error) {
        console.error('Error loading todos:', error);
    }
}

function renderTodos() {
    const todoList = document.getElementById('todoList');
    const filteredTodos = filterTodosByStatus(allTodos);
    
    if (filteredTodos.length === 0) {
        todoList.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-check-circle fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No tasks found</h5>
                <p class="text-muted">Add your first task to get started!</p>
                <button class="btn btn-primary" onclick="showTodoForm()">
                    <i class="fas fa-plus me-2"></i>Add Your First Task
                </button>
            </div>
        `;
        return;
    }
    
    todoList.innerHTML = filteredTodos.map(todo => `
        <div class="todo-item ${todo.category} card mb-3 ${todo.completed ? 'completed' : ''}" data-todo-id="${todo.id}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-2">
                            <span class="priority-dot priority-${todo.priority}"></span>
                            <h6 class="card-title mb-0 me-2 ${todo.completed ? 'text-decoration-line-through' : ''}">
                                ${todo.title}
                            </h6>
                            <span class="badge ${getCategoryClass(todo.category)} category-badge">
                                ${getCategoryIcon(todo.category)} ${todo.category}
                            </span>
                        </div>
                        ${todo.description ? `<p class="card-text text-muted small">${todo.description}</p>` : ''}
                        <div class="d-flex justify-content-between align-items-center mt-2">
                            <small class="text-muted">
                                <i class="fas fa-calendar me-1"></i>
                                Created: ${new Date(todo.created_at).toLocaleDateString()}
                                ${todo.due_date ? ` | Due: ${new Date(todo.due_date).toLocaleDateString()}` : ''}
                            </small>
                            <div>
                                <button class="btn btn-sm ${todo.completed ? 'btn-warning' : 'btn-success'}" onclick="toggleTodo(${todo.id})">
                                    <i class="fas ${todo.completed ? 'fa-undo' : 'fa-check'} me-1"></i>
                                    ${todo.completed ? 'Reopen' : 'Complete'}
                                </button>
                                <button class="btn btn-sm btn-outline-primary" onclick="editTodo(${todo.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteTodo(${todo.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function filterTodosByStatus(todos) {
    switch (currentFilter) {
        case 'active':
            return todos.filter(todo => !todo.completed);
        case 'completed':
            return todos.filter(todo => todo.completed);
        default:
            return todos;
    }
}

function filterTodos(filter) {
    currentFilter = filter;
    renderTodos();
}

function searchTodos() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filteredTodos = allTodos.filter(todo => 
        todo.title.toLowerCase().includes(searchTerm) || 
        (todo.description && todo.description.toLowerCase().includes(searchTerm))
    );
    
    const todoList = document.getElementById('todoList');
    todoList.innerHTML = filteredTodos.map(todo => `
        <!-- Same todo item structure as above -->
    `).join('');
}

// Todo Modal Functions
function showTodoForm(todo = null) {
    const modal = new bootstrap.Modal(document.getElementById('todoModal'));
    const form = document.getElementById('todoForm');
    
    if (todo) {
        document.getElementById('modalTitle').textContent = 'Edit Task';
        document.getElementById('todoId').value = todo.id;
        document.getElementById('todoTitle').value = todo.title;
        document.getElementById('todoDescription').value = todo.description || '';
        document.getElementById('todoCategory').value = todo.category;
        document.getElementById('todoPriority').value = todo.priority;
        document.getElementById('todoDueDate').value = todo.due_date ? todo.due_date.slice(0, 16) : '';
    } else {
        document.getElementById('modalTitle').textContent = 'Add New Task';
        form.reset();
        document.getElementById('todoId').value = '';
    }
    
    modal.show();
}

async function saveTodo() {
    const form = document.getElementById('todoForm');
    const todoId = document.getElementById('todoId').value;
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const todoData = {
        title: document.getElementById('todoTitle').value,
        description: document.getElementById('todoDescription').value,
        category: document.getElementById('todoCategory').value,
        priority: document.getElementById('todoPriority').value,
        due_date: document.getElementById('todoDueDate').value || null
    };
    
    try {
        const url = todoId ? `${API_BASE}/todos/${todoId}` : `${API_BASE}/todos`;
        const method = todoId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(todoData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('todoModal'));
            modal.hide();
            loadTodos();
            loadStatistics();
        } else {
            alert(data.error || 'Error saving todo');
        }
    } catch (error) {
        alert('Error saving todo: ' + error.message);
    }
}

async function toggleTodo(todoId) {
    try {
        const todo = allTodos.find(t => t.id === todoId);
        const response = await fetch(`${API_BASE}/todos/${todoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ completed: !todo.completed })
        });
        
        if (response.ok) {
            loadTodos();
            loadStatistics();
        } else {
            const data = await response.json();
            alert(data.error || 'Error updating todo');
        }
    } catch (error) {
        alert('Error updating todo: ' + error.message);
    }
}

function editTodo(todoId) {
    const todo = allTodos.find(t => t.id === todoId);
    showTodoForm(todo);
}

async function deleteTodo(todoId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/todos/${todoId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            loadTodos();
            loadStatistics();
        } else {
            const data = await response.json();
            alert(data.error || 'Error deleting todo');
        }
    } catch (error) {
        alert('Error deleting todo: ' + error.message);
    }
}

// Statistics Functions
async function loadStatistics() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/statistics`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            renderStatistics(data);
        } else {
            console.error('Error loading statistics:', data.error);
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

function renderStatistics(stats) {
    const statsContent = document.getElementById('statisticsContent');
    const completionRate = stats.completion_rate || 0;
    
    statsContent.innerHTML = `
        <div class="text-center mb-4">
            <div class="display-6 fw-bold text-primary">${completionRate.toFixed(1)}%</div>
            <div class="text-muted">Completion Rate</div>
        </div>
        
        <div class="progress-bar bg-light mb-3">
            <div class="progress-bar bg-success" style="width: ${completionRate}%"></div>
        </div>
        
        <div class="row text-center mb-3">
            <div class="col-4">
                <div class="fw-bold">${stats.total || 0}</div>
                <small class="text-muted">Total</small>
            </div>
            <div class="col-4">
                <div class="fw-bold text-success">${stats.completed || 0}</div>
                <small class="text-muted">Done</small>
            </div>
            <div class="col-4">
                <div class="fw-bold text-warning">${stats.pending || 0}</div>
                <small class="text-muted">Pending</small>
            </div>
        </div>
        
        <div class="mt-3">
            <h6 class="fw-bold mb-2">By Category</h6>
            ${Object.entries(stats.category_stats || {}).map(([category, count]) => `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge ${getCategoryClass(category)} category-badge">
                        ${getCategoryIcon(category)} ${category}
                    </span>
                    <small class="text-muted">${count}</small>
                </div>
            `).join('')}
        </div>
    `;
}

// Helper Functions
function getCategoryClass(category) {
    const classes = {
        'work': 'bg-blue-100 text-blue-800',
        'personal': 'bg-green-100 text-green-800',
        'shopping': 'bg-yellow-100 text-yellow-800',
        'health': 'bg-red-100 text-red-800',
        'learning': 'bg-purple-100 text-purple-800',
        'urgent': 'bg-red-100 text-red-800',
        'other': 'bg-gray-100 text-gray-800'
    };
    return classes[category] || classes['other'];
}

function getCategoryIcon(category) {
    const icons = {
        'work': '💼',
        'personal': '🏠',
        'shopping': '🛒',
        'health': '🏥',
        'learning': '📚',
        'urgent': '🚨',
        'other': '📌'
    };
    return icons[category] || icons['other'];
}

// Service Worker for PWA (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}