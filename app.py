from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) 

VOLUME_PATH = "/data" 
DATA_FILE = os.path.join(VOLUME_PATH, "users_data.json")

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, 'r') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return {}

def save_data(data):
    os.makedirs(VOLUME_PATH, exist_ok=True)
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users_data = load_data()
        if username not in users_data or not check_password_hash(users_data[username]['password'], password):
            flash('Usuário ou senha inválidos!', 'danger')
            return redirect(url_for('login'))
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users_data = load_data()
        if username in users_data:
            flash('Este nome de usuário já existe.', 'warning')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        users_data[username] = {'password': hashed_password, 'projects': {}}
        save_data(users_data)
        flash('Conta criada com sucesso! Faça o login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    users_data = load_data()
    user_projects = users_data.get(session['username'], {}).get('projects', {})
    return render_template('dashboard.html', projects=user_projects, username=session['username'])

@app.route('/view/<project_id>')
def view(project_id):
    users_data = load_data()
    found_project = None
    for user, data in users_data.items():
        if project_id in data.get('projects', {}):
            found_project = data['projects'][project_id]
            break
    if not found_project:
        return "Projeto não encontrado", 404
    return render_template('view.html', project=found_project)

@app.route('/editor')
def editor():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

# --- ROTAS DE PERFIL DE USUÁRIO ---

@app.route('/profile/<username>')
def profile(username):
    """Exibe o perfil público de um usuário com seus projetos públicos."""
    users_data = load_data()
    user_data = users_data.get(username)

    if not user_data:
        return "Perfil não encontrado", 404

    # Filtra apenas os projetos marcados como públicos
    public_projects = {
        pid: p for pid, p in user_data.get('projects', {}).items() if p.get('public')
    }
    
    # Obtém informações do perfil, com valores padrão caso não existam
    user_profile = user_data.get('profile', {
        'bio': 'Este usuário ainda não adicionou uma biografia.',
        'avatar_url': url_for('static', filename='images/default_avatar.png') # Precisaremos de uma imagem padrão
    })

    return render_template('profile.html', 
                           username=username, 
                           profile=user_profile, 
                           projects=public_projects)


@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Permite que o usuário logado edite seu perfil."""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    users_data = load_data()
    user_profile = users_data[username].setdefault('profile', {})

    if request.method == 'POST':
        user_profile['bio'] = request.form.get('bio', '')
        user_profile['avatar_url'] = request.form.get('avatar_url', '')
        save_data(users_data)
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', profile=user_profile)

# --- API PARA GERENCIAMENTO DE PROJETOS (ATUALIZADA) ---

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Cria um novo projeto."""
    if 'username' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    username = session['username']
    users_data = load_data()
    project_data = request.json
    project_name = project_data.get('name')
    
    if not project_name:
        return jsonify({'error': 'Nome do projeto é obrigatório'}), 400

    project_id = str(uuid.uuid4())
    users_data[username]['projects'][project_id] = {
        'name': project_name,
        'html': project_data.get('html', ''),
        'css': project_data.get('css', ''),
        'js': project_data.get('js', ''),
        'public': project_data.get('public', False)
    }
    save_data(users_data)
    return jsonify({'success': True, 'message': 'Projeto salvo!'}), 201

@app.route('/api/projects/<project_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_project(project_id):
    """Obtém, atualiza ou deleta um projeto específico."""
    if 'username' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    username = session['username']
    users_data = load_data()
    
    if project_id not in users_data[username]['projects']:
        return jsonify({'error': 'Projeto não encontrado'}), 404

    # --- OBTER DADOS DO PROJETO (para edição) ---
    if request.method == 'GET':
        project = users_data[username]['projects'][project_id]
        return jsonify(project)

    # --- ATUALIZAR UM PROJETO EXISTENTE ---
    if request.method == 'PUT':
        update_data = request.json
        users_data[username]['projects'][project_id]['html'] = update_data.get('html', '')
        users_data[username]['projects'][project_id]['css'] = update_data.get('css', '')
        users_data[username]['projects'][project_id]['js'] = update_data.get('js', '')
        users_data[username]['projects'][project_id]['public'] = update_data.get('public', False)
        save_data(users_data)
        return jsonify({'success': True, 'message': 'Projeto atualizado!'})

    # --- DELETAR UM PROJETO ---
    if request.method == 'DELETE':
        del users_data[username]['projects'][project_id]
        save_data(users_data)
        return jsonify({'success': True, 'message': 'Projeto deletado!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)