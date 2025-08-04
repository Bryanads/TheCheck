from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from dotenv import load_dotenv


# NOVO: Importação específica das funções de queries
from src.db.queries import (
    get_user_by_email,
    create_user,
    get_user_by_id,
    update_user_last_login,
    update_user_profile
)

"""
Exemplo de Requisição para /register

Método: POST
URL: http://127.0.0.1:5000/register
Headers:
    Content-Type: application/json

Corpo da Requisição (JSON):
{
    "name": "Maria Onda",
    "email": "maria.onda@example.com",
    "password": "umaSenhaSegura!",
    "surf_level": "Maroleiro",
    "goofy_regular_stance": "goofy",
    "preferred_wave_direction": "left",
    "bio": "Adoro surfar ondas pequenas e aprender sempre mais.",
    "profile_picture_url": "https://example.com/maria_onda.jpg"
}

-----------------------------------------------------------------------------------------------------

Exemplo de Requisição para /login

Método: POST
URL: http://127.0.0.1:5000/login
Headers:
    Content-Type: application/json

Corpo da Requisição (JSON):
{
    "email": "joao.surfista@example.com",
    "password": "umaSenhaSegura123!"
}

-----------------------------------------------------------------------------------------------------

Exemplo de requisição para: http://127.0.0.1:5000/profile/<user_id>
Método: GET
Headers:
    # Não exige autenticação neste exemplo, mas é recomendado para produção

-------------------------------------------

Método: PUT
URL: http://http://127.0.0.1:5000/profile/<user_id>
Headers:
    Content-Type: application/json
    # Não exige autenticação neste exemplo, mas é recomendado para produção.

Corpo da Requisição (JSON):
{
    "surf_level": "expert",
    "bio": "Agora sou um surfista expert, focado em ondas perfeitas!"
}
(Você pode enviar apenas os campos que deseja atualizar.)

"""

load_dotenv()
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'SUPER_SECRET_DEV_KEY_DONT_USE_IN_PROD')

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    surf_level = data.get('surf_level')
    goofy_regular_stance = data.get('goofy_regular_stance')
    preferred_wave_direction = data.get('preferred_wave_direction')
    bio = data.get('bio')
    profile_picture_url = data.get('profile_picture_url')

    if not all([name, email, password]):
        return jsonify({"error": "Name, email, and password are required"}), 400

    # Verificar se o email já existe
    existing_user = get_user_by_email(email)
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409 # Conflict

    hashed_password = generate_password_hash(password, method='scrypt')

    try:
        user_id = create_user(
            name, email, hashed_password, surf_level, goofy_regular_stance,
            preferred_wave_direction, bio, profile_picture_url
        )
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": f"Registration failed: {e}"}), 500

@user_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Email and password are required"}), 400

    user = get_user_by_email(email)
    if user is None:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    try:
        update_user_last_login(user['user_id'])
    except Exception as e:
        print(f"Warning: Could not update last login for user {user['user_id']}: {e}")

    token_payload = {
        'user_id': user['user_id'],
        'email': user['email'],
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

    return jsonify({"message": "Login successful", "token": token, "user_id": user['user_id']}), 200

@user_bp.route('/profile/<uuid:user_id>', methods=['GET', 'PUT'])
def user_profile(user_id):
    user = get_user_by_id(str(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == 'GET':
        user_data = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify(user_data), 200

    elif request.method == 'PUT':
        data = request.get_json()
        update_fields = {
            'name': data.get('name'),
            'surf_level': data.get('surf_level'),
            'goofy_regular_stance': data.get('goofy_regular_stance'),
            'preferred_wave_direction': data.get('preferred_wave_direction'),
            'bio': data.get('bio'),
            'profile_picture_url': data.get('profile_picture_url'),
        }

        update_fields = {k: v for k, v in update_fields.items() if v is not None}

        if not update_fields:
            return jsonify({"message": "No fields to update"}), 400

        try:
            update_user_profile(user_id, update_fields)
            updated_user = get_user_by_id(str(user_id))
            user_data = {k: v for k, v in updated_user.items() if k != 'password_hash'}
            return jsonify({"message": "Profile updated successfully", "user": user_data}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to update profile: {e}"}), 500