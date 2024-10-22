from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import abort
from flaskr.db import get_db

bp = Blueprint('todo', __name__)

# View todos (GET all todos for the logged-in user)
@bp.route('/todos', methods=['GET'])
@jwt_required()
def get_todos():
    user_id = get_jwt_identity()
    db = get_db()
    todos = db.execute(
        'SELECT id, title, body, created FROM todo WHERE author_id = ? ORDER BY created DESC',
        (user_id,)
    ).fetchall()
    
    todo_list = []
    for todo in todos:
        todo_list.append({
            'id': todo['id'],
            'title': todo['title'],
            'body': todo['body'],
            'created': todo['created']
        })
    
    return jsonify(todo_list), 200

# Create a new todo (POST)
@bp.route('/todos', methods=['POST'])
@jwt_required()
def create_todo():
    user_id = get_jwt_identity()
    data = request.get_json()
    title = data.get('title')
    body = data.get('body', '')  # Optional field
    error = None

    if not title:
        error = 'Title is required.'
        return jsonify({'error': error}), 400

    db = get_db()
    cursor = db.execute(
        'INSERT INTO todo (title, body, author_id) VALUES (?, ?, ?)',
        (title, body, user_id)
    )
    db.commit()
    
    # Get the last inserted todo's ID
    todo_id = cursor.lastrowid

    # Return the new todo with its id
    return jsonify({'id': todo_id, 'title': title, 'body': body}), 201

# Helper function to get a todo by ID
def get_todo(id, check_author=True):
    todo = get_db().execute(
        'SELECT id, title, body, created, author_id FROM todo WHERE id = ?',
        (id,)
    ).fetchone()

    if todo is None:
        abort(404, f"Todo id {id} doesn't exist.")

    if check_author:
        user_id = get_jwt_identity()
        if todo['author_id'] != user_id:
            abort(403, "You are not authorized to modify this todo.")

    return todo

# Update a todo (PUT)
@bp.route('/todos/<int:id>', methods=['PUT'])
@jwt_required()
def update_todo(id):
    todo = get_todo(id)

    data = request.get_json()
    title = data.get('title')
    body = data.get('body', '')

    if not title:
        return jsonify({'error': 'Title is required.'}), 400

    db = get_db()
    db.execute(
        'UPDATE todo SET title = ?, body = ? WHERE id = ?',
        (title, body, id)
    )
    db.commit()

    return jsonify({'message': 'Todo updated successfully'}), 200

# Delete a todo (DELETE)
@bp.route('/todos/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_todo(id):
    get_todo(id)  # Ensure the todo exists and the user is authorized

    db = get_db()
    db.execute('DELETE FROM todo WHERE id = ?', (id,))
    db.commit()

    return jsonify({'message': 'Todo deleted successfully'}), 200
