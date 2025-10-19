from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) 

VOLUME_PATH = "/data" 
DATA_FILE = os.path.join(VOLUME_PATH, "users_data.json")

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def load_data():
    """Carrega os dados dos usuários do arquivo JSON de forma segura."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_data(data):
    """Salva os dados dos usuários no arquivo JSON, criando o diretório se necessário."""
    os.makedirs(VOLUME_PATH, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ROTAS DE AUTENTICAÇÃO E NAVEGAÇÃO BÁSICA ---

@app.route('/')
def home():
    """Redireciona a rota raiz para a página de login."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users_data = load_data()
        
        user = users_data.get(username)
        if not user or not check_password_hash(user['password'], password):
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
        users_data[username] = {'password': hashed_password, 'projects': {}, 'profile': {}}
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

@app.route('/editor')
def editor():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

# --- ROTAS DE VISUALIZAÇÃO E PERFIL ---

@app.route('/view/<project_id>')
def view(project_id):
    """Exibe um projeto específico em sua própria página."""
    users_data = load_data()
    found_project = None
    for user_data in users_data.values():
        if project_id in user_data.get('projects', {}):
            found_project = user_data['projects'][project_id]
            break
            
    if not found_project:
        return "Projeto não encontrado", 404
        
    return render_template('view.html', project=found_project)


@app.route('/profile/<username>')
def profile(username):
    """Exibe o perfil público de um usuário, buscando dados dinâmicos do GitHub."""
    users_data = load_data()
    user_data = users_data.get(username)

    if not user_data:
        return "Perfil não encontrado", 404

    public_projects_dict = {
        pid: p for pid, p in user_data.get('projects', {}).items() if p.get('public')
    }

    sorted_public_projects = sorted(
        public_projects_dict.items(), 
        key=lambda item: item[1].get('name', '').lower()
    )
    
    user_profile = user_data.get('profile', {})
    github_username = user_profile.get('github_username')
    
    followers_count = "N/A"
    contributions_count = "N/A"

    if github_username:
        try:
            user_response = requests.get(f"https://api.github.com/users/{github_username}", timeout=5)
            user_response.raise_for_status()
            followers_count = user_response.json().get('followers', 'Erro')

            contrib_response = requests.get(f"https://github-contributions-api.jogruber.de/v4/{github_username}?y=all", timeout=10)
            contrib_response.raise_for_status()
            contrib_data = contrib_response.json()
            contributions_count = sum(day.get('count', 0) for day in contrib_data.get('contributions', []))
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados do GitHub para '{github_username}': {e}")
            followers_count = "Erro"
            contributions_count = "Erro"
            
    profile_data = {
        'display_name': user_profile.get('display_name', username),
        'bio': user_profile.get('bio', 'Nenhuma biografia adicionada.'),
        'avatar_url': user_profile.get('avatar_url', url_for('static', filename='images/default_avatar.png')),
        'about_me': user_profile.get('about_me', 'Nenhuma informação adicional.'),
        'stats_projects': len(public_projects_dict),
        'stats_followers': followers_count,
        'stats_github': contributions_count
    }

    return render_template('profile.html', 
                           username=username, 
                           profile=profile_data, 
                           projects=sorted_public_projects) 

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Permite que o usuário logado edite seu perfil."""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    users_data = load_data()
    user_profile = users_data[username].setdefault('profile', {})

    if request.method == 'POST':
        user_profile['display_name'] = request.form.get('display_name', username)
        user_profile['bio'] = request.form.get('bio', '')
        user_profile['about_me'] = request.form.get('about_me', '')
        user_profile['github_username'] = request.form.get('github_username', '')

        new_avatar_base64 = request.form.get('avatar_base64')
        if new_avatar_base64:
            user_profile['avatar_url'] = new_avatar_base64

        save_data(users_data)
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', profile=user_profile, username=username)


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Cria um novo projeto via API."""
    if 'username' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    username = session['username']
    project_data = request.json
    project_name = project_data.get('name')
    
    if not project_name:
        return jsonify({'error': 'Nome do projeto é obrigatório'}), 400

    project_id = str(uuid.uuid4())
    users_data = load_data()
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
    """Obtém, atualiza ou deleta um projeto específico via API."""
    if 'username' not in session:
        return jsonify({'error': 'Não autorizado'}), 401

    username = session['username']
    users_data = load_data()
    
    if project_id not in users_data[username]['projects']:
        return jsonify({'error': 'Projeto não encontrado'}), 404

    if request.method == 'GET':
        return jsonify(users_data[username]['projects'][project_id])

    if request.method == 'PUT':
        update_data = request.json
        project = users_data[username]['projects'][project_id]
        project['html'] = update_data.get('html', project['html'])
        project['css'] = update_data.get('css', project['css'])
        project['js'] = update_data.get('js', project['js'])
        project['public'] = update_data.get('public', project['public'])
        save_data(users_data)
        return jsonify({'success': True, 'message': 'Projeto atualizado!'})

    if request.method == 'DELETE':
        del users_data[username]['projects'][project_id]
        save_data(users_data)
        return jsonify({'success': True, 'message': 'Projeto deletado!'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)