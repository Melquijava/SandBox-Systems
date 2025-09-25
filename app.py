from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import time # Importamos a biblioteca de tempo

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) 

VOLUME_PATH = "/data" 
DATA_FILE = os.path.join(VOLUME_PATH, "users_data.json")

# --- Funções de Dados (COM LOGS) ---
def load_data():
    """Carrega os dados do arquivo JSON."""
    print(f"--- [LOG] Tentando carregar dados de: {DATA_FILE}") # Log
    if not os.path.exists(DATA_FILE):
        print("--- [LOG] Arquivo não encontrado. Retornando dicionário vazio.") # Log
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            print(f"--- [LOG] Dados carregados com sucesso. Usuários: {list(data.keys())}") # Log
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        print("--- [LOG] Erro ao decodificar JSON ou arquivo não encontrado. Retornando dicionário vazio.") # Log
        return {}

def save_data(data):
    """Salva os dados no arquivo JSON."""
    print(f"--- [LOG] Tentando salvar dados em: {DATA_FILE}") # Log
    os.makedirs(VOLUME_PATH, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print("--- [LOG] Dados salvos com sucesso.") # Log

# --- Rotas (sem alteração na lógica, apenas se beneficiarão dos logs) ---

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ... (código existente)
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
        # ... (código existente)
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
    
    print(f"--- [LOG] Rota /dashboard acessada pelo usuário: {session['username']}") # Log
    users_data = load_data()
    user_projects = users_data.get(session['username'], {}).get('projects', {})
    print(f"--- [LOG] Projetos encontrados para o usuário: {len(user_projects)}") # Log
    
    return render_template('dashboard.html', projects=user_projects, username=session['username'])

@app.route('/view/<project_id>')
def view(project_id):
    # ... (código existente)
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

@app.route('/api/projects', methods=['POST'])
def handle_projects():
    if 'username' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    username = session['username']
    print(f"--- [LOG] Rota /api/projects acessada por: {username}") # Log
    
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
        'js': project_data.get('js', '')
    }
    
    print(f"--- [LOG] Salvando novo projeto '{project_name}' para o usuário '{username}'") # Log
    save_data(users_data)
    
    return jsonify({'success': True, 'message': 'Projeto salvo!'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)