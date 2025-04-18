from flask import Blueprint, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
import os

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

auth = Blueprint("auth", __name__)

# Function to verify JWT token
def verify_token(token):
    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception:
        return None

# Sign-up route
@auth.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Sign-in route
@auth.route("/signin", methods=["POST"])
def signin():
    # Sign in a user with email and password, returning access and refresh tokens.
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.session is None:
            return jsonify({"status": "error", "message": "Authentication failed"}), 401
        return jsonify({
            "status": "success",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400