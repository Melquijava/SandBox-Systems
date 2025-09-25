document.addEventListener('DOMContentLoaded', () => {

    // --- INICIALIZAÇÃO E LÓGICA DO EDITOR ---
    
    // Inicializa os três editores
    const htmlEditor = CodeMirror(document.getElementById('html-editor'), { mode: 'xml', theme: 'dracula', lineNumbers: true, lineWrapping: true, autoCloseBrackets: true });
    const cssEditor = CodeMirror(document.getElementById('css-editor'), { mode: 'css', theme: 'dracula', lineNumbers: true, lineWrapping: true, autoCloseBrackets: true });
    const jsEditor = CodeMirror(document.getElementById('js-editor'), { mode: 'javascript', theme: 'dracula', lineNumbers: true, lineWrapping: true, autoCloseBrackets: true });
    
    const previewFrame = document.getElementById('preview-frame');
    let currentProjectId = null; // Variável para saber se estamos editando

    // Função que renderiza o preview
    function updatePreview() {
        const previewDoc = previewFrame.contentDocument || previewFrame.contentWindow.document;

        previewDoc.open();
        previewDoc.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <style>${cssEditor.getValue()}</style>
            </head>
            <body>
                ${htmlEditor.getValue()}
            </body>
            </html>
        `);
        previewDoc.close();

        // Anexa o script de forma segura
        const scriptTag = previewDoc.createElement('script');
        scriptTag.textContent = jsEditor.getValue();
        previewDoc.body.appendChild(scriptTag);
    }

    // Adiciona os listeners que atualizam o preview em tempo real
    htmlEditor.on('change', updatePreview);
    cssEditor.on('change', updatePreview);
    jsEditor.on('change', updatePreview);

    // --- LÓGICA DE CARREGAMENTO PARA EDIÇÃO ---
    async function loadProjectForEditing(projectId) {
        try {
            const response = await fetch(`/api/projects/${projectId}`);
            if (!response.ok) { throw new Error('Projeto não encontrado'); }
            const projectData = await response.json();
            
            // Preenche os editores com o código do projeto
            htmlEditor.setValue(projectData.html || '');
            cssEditor.setValue(projectData.css || '');
            jsEditor.setValue(projectData.js || '');
            
            currentProjectId = projectId; // Define que estamos em modo de edição
            
            // AQUI ESTÁ A CORREÇÃO: Chama a função de preview após carregar os dados
            updatePreview(); 
            
        } catch (error) {
            alert('Erro ao carregar o projeto para edição.');
            window.location.href = '/dashboard'; // Volta se der erro
        }
    }

    // Verifica se a URL tem um project_id para carregar
    const urlParams = new URLSearchParams(window.location.search);
    const projectIdFromUrl = urlParams.get('project_id');
    if (projectIdFromUrl) {
        loadProjectForEditing(projectIdFromUrl); // Carrega o projeto existente
    } else {
        updatePreview(); // Inicia o preview se for um projeto novo
    }

    // --- LÓGICA DE SALVAMENTO (CRIAR vs. ATUALIZAR) ---
    const saveButton = document.getElementById('save-button');
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            let url, method, projectData;

            if (currentProjectId) { // MODO DE ATUALIZAÇÃO
                url = `/api/projects/${currentProjectId}`;
                method = 'PUT';
                projectData = {
                    html: htmlEditor.getValue(),
                    css: cssEditor.getValue(),
                    js: jsEditor.getValue()
                };
            } else { // MODO DE CRIAÇÃO
                const projectName = prompt("Digite um nome para o seu novo projeto:");
                if (!projectName) return; // Cancela se não houver nome
                
                url = '/api/projects';
                method = 'POST';
                projectData = {
                    name: projectName,
                    html: htmlEditor.getValue(),
                    css: cssEditor.getValue(),
                    js: jsEditor.getValue()
                };
            }

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(projectData)
                });

                if (response.ok) {
                    alert('Projeto salvo com sucesso!');
                    window.location.href = '/dashboard';
                } else {
                    const result = await response.json();
                    alert(`Erro ao salvar: ${result.error}`);
                }
            } catch (error) {
                alert("Erro de conexão ao tentar salvar.");
            }
        });
    }
});