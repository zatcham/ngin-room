# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import git
import os
import subprocess
import yaml
import logging
import hashlib
from datetime import datetime, timedelta
import psutil
import secrets
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

# Cors config
CORS(app)

# cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# DB Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Replace with your DB URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'secret-key'  # Change this to a secure secret key
# app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

with app.app_context():
    db.create_all()

# Configure logging
logging.basicConfig(
    filename='deployment.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
CONFIG_FILE = 'config.yaml'
REPOS_BASE_PATH = '/var/www'
NGINX_SITES_PATH = '/etc/nginx/sites-available'
NGINX_ENABLED_PATH = '/etc/nginx/sites-enabled'
LOGS_DIR = '/var/log/nginx'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return {
        'repositories': {},
        'users': {},
        'webhook_tokens': {}
    }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

def get_server_stats():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        'cpu_usage': cpu,
        'memory_usage': memory.percent,
        'disk_usage': disk.percent,
        'uptime': subprocess.getoutput('uptime')
    }

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2')
    new_user = User(username=data['username'], password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.username)
        return jsonify({"access_token": access_token}), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"logged_in_as": current_user}), 200

@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    return jsonify(get_server_stats())

@app.route('/api/repos', methods=['GET'])
@jwt_required()
def list_repos():
    config = load_config()
    return jsonify(config['repositories'])

@app.route('/api/repos', methods=['POST'])
@jwt_required()
def add_repo():
    config = load_config()
    data = request.json

    repo_name = data['name']
    repo_url = data['git_url']
    domain = data['domain']

    # Generate webhook token
    webhook_token = secrets.token_hex(16)
    config['webhook_tokens'][webhook_token] = repo_name

    # Clone repository
    repo_path = os.path.join(REPOS_BASE_PATH, repo_name)
    if not os.path.exists(repo_path):
        git.Repo.clone_from(repo_url, repo_path)

    # Create Nginx configuration
    nginx_config = data.get('nginx_config') or f"""
server {{
    listen 80;
    server_name {domain};
    root {repo_path}/public;
    
    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
"""

    nginx_conf_path = os.path.join(NGINX_SITES_PATH, f'{repo_name}.conf')
    with open(nginx_conf_path, 'w') as f:
        f.write(nginx_config)

    # Enable site by default
    nginx_enabled_path = os.path.join(NGINX_ENABLED_PATH, f'{repo_name}.conf')
    if not os.path.exists(nginx_enabled_path):
        os.symlink(nginx_conf_path, nginx_enabled_path)

    # Update config
    config['repositories'][repo_name] = {
        'git_url': repo_url,
        'domain': domain,
        'path': repo_path,
        'enabled': True,
        'webhook_token': webhook_token,
        'nginx_config': nginx_config
    }
    save_config(config)

    subprocess.run(['sudo', 'nginx', '-s', 'reload'])
    logging.info(f'Added new repository: {repo_name}')

    return jsonify({'status': 'success', 'webhook_token': webhook_token})

@app.route('/api/repos/<repo_name>/duplicate', methods=['POST'])
@jwt_required()
def duplicate_repo(repo_name):
    config = load_config()
    data = request.json

    if repo_name not in config['repositories']:
        return jsonify({'error': 'Repository not found'}), 404

    new_name = data['new_name']
    new_domain = data['new_domain']
    new_path = data['new_path']

    # Copy repository
    subprocess.run(['cp', '-r', config['repositories'][repo_name]['path'], new_path])

    # Create new Nginx config
    nginx_config = config['repositories'][repo_name]['nginx_config'].replace(
        config['repositories'][repo_name]['domain'],
        new_domain
    ).replace(
        config['repositories'][repo_name]['path'],
        new_path
    )

    # Generate webhook token
    webhook_token = secrets.token_hex(16)
    config['webhook_tokens'][webhook_token] = new_name

    # Save new repository config
    config['repositories'][new_name] = {
        'git_url': config['repositories'][repo_name]['git_url'],
        'domain': new_domain,
        'path': new_path,
        'enabled': True,
        'webhook_token': webhook_token,
        'nginx_config': nginx_config
    }

    # Create and enable Nginx config
    nginx_conf_path = os.path.join(NGINX_SITES_PATH, f'{new_name}.conf')
    with open(nginx_conf_path, 'w') as f:
        f.write(nginx_config)

    nginx_enabled_path = os.path.join(NGINX_ENABLED_PATH, f'{new_name}.conf')
    os.symlink(nginx_conf_path, nginx_enabled_path)

    save_config(config)
    subprocess.run(['sudo', 'nginx', '-s', 'reload'])

    return jsonify({'status': 'success', 'webhook_token': webhook_token})

@app.route('/api/repos/<repo_name>/toggle', methods=['POST'])
@jwt_required()
def toggle_repo(repo_name):
    config = load_config()

    if repo_name not in config['repositories']:
        return jsonify({'error': 'Repository not found'}), 404

    nginx_conf_path = os.path.join(NGINX_SITES_PATH, f'{repo_name}.conf')
    nginx_enabled_path = os.path.join(NGINX_ENABLED_PATH, f'{repo_name}.conf')

    if config['repositories'][repo_name]['enabled']:
        if os.path.exists(nginx_enabled_path):
            os.remove(nginx_enabled_path)
        config['repositories'][repo_name]['enabled'] = False
    else:
        if not os.path.exists(nginx_enabled_path):
            os.symlink(nginx_conf_path, nginx_enabled_path)
        config['repositories'][repo_name]['enabled'] = True

    save_config(config)
    subprocess.run(['sudo', 'nginx', '-s', 'reload'])

    return jsonify({'status': 'success'})

@app.route('/api/repos/<repo_name>/config', methods=['PUT'])
@jwt_required()
def update_config(repo_name):
    config = load_config()
    data = request.json

    if repo_name not in config['repositories']:
        return jsonify({'error': 'Repository not found'}), 404

    nginx_conf_path = os.path.join(NGINX_SITES_PATH, f'{repo_name}.conf')
    with open(nginx_conf_path, 'w') as f:
        f.write(data['nginx_config'])

    config['repositories'][repo_name]['nginx_config'] = data['nginx_config']
    save_config(config)

    subprocess.run(['sudo', 'nginx', '-s', 'reload'])

    return jsonify({'status': 'success'})

@app.route('/api/repos/<repo_name>/pull', methods=['POST'])
@jwt_required()
def pull_repo(repo_name):
    config = load_config()

    if repo_name not in config['repositories']:
        return jsonify({'error': 'Repository not found'}), 404

    repo_path = config['repositories'][repo_name]['path']
    repo = git.Repo(repo_path)
    origin = repo.remotes.origin
    origin.pull()

    logging.info(f'Pulled latest changes for {repo_name}')
    return jsonify({'status': 'success'})

@app.route('/webhook/<token>', methods=['POST'])
def webhook(token):
    config = load_config()

    if token not in config['webhook_tokens']:
        return jsonify({'error': 'Invalid webhook token'}), 401

    repo_name = config['webhook_tokens'][token]
    repo_path = config['repositories'][repo_name]['path']

    repo = git.Repo(repo_path)
    origin = repo.remotes.origin
    origin.pull()

    logging.info(f'Webhook triggered for {repo_name}')
    return jsonify({'status': 'success'})

@app.route('/api/logs/<repo_name>', methods=['GET'])
@jwt_required()
def get_logs(repo_name):
    config = load_config()

    if repo_name not in config['repositories']:
        return jsonify({'error': 'Repository not found'}), 404

    # Get deployment logs
    with open('deployment.log', 'r') as f:
        deployment_logs = [line for line in f if repo_name in line]

    # Get Nginx access logs
    access_log_path = os.path.join(LOGS_DIR, f'{repo_name}-access.log')
    if os.path.exists(access_log_path):
        with open(access_log_path, 'r') as f:
            access_logs = f.readlines()[-100:]  # Last 100 lines
    else:
        access_logs = []

    # Get Nginx error logs
    error_log_path = os.path.join(LOGS_DIR, f'{repo_name}-error.log')
    if os.path.exists(error_log_path):
        with open(error_log_path, 'r') as f:
            error_logs = f.readlines()[-100:]  # Last 100 lines
    else:
        error_logs = []

    return jsonify({
        'deployment_logs': deployment_logs,
        'access_logs': access_logs,
        'error_logs': error_logs
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)