document.addEventListener('DOMContentLoaded', () => {

    
    const htmlEditor = CodeMirror(document.getElementById('html-editor'), { mode: 'xml', theme: 'dracula', lineNumbers: true, lineWrapping: true, autoCloseBrackets: true });
    const cssEditor = CodeMirror(document.getElementById('css-editor'), { mode: 'css', theme: 'dracula', lineNumbers: true, lineWrapping: true, autoCloseBrackets: true });
    const jsEditor = CodeMirror(document.getElementById('js-editor'), { mode: 'javascript', theme: 'dracula', lineNumbers: true, lineWrapping: true, autoCloseBrackets: true });
    
    const previewFrame = document.getElementById('preview-frame');
    let currentProjectId = null; 

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

        const scriptTag = previewDoc.createElement('script');
        scriptTag.textContent = jsEditor.getValue();
        previewDoc.body.appendChild(scriptTag);
    }

    htmlEditor.on('change', updatePreview);
    cssEditor.on('change', updatePreview);
    jsEditor.on('change', updatePreview);

    async function loadProjectForEditing(projectId) {
        try {
            const response = await fetch(`/api/projects/${projectId}`);
            if (!response.ok) { throw new Error('Projeto não encontrado'); }
            const projectData = await response.json();
            
            htmlEditor.setValue(projectData.html || '');
            cssEditor.setValue(projectData.css || '');
            jsEditor.setValue(projectData.js || '');
            
            currentProjectId = projectId; 
            
            updatePreview(); 
            
        } catch (error) {
            alert('Erro ao carregar o projeto para edição.');
            window.location.href = '/dashboard'; 
        }
    }

    const urlParams = new URLSearchParams(window.location.search);
    const projectIdFromUrl = urlParams.get('project_id');
    if (projectIdFromUrl) {
        loadProjectForEditing(projectIdFromUrl); 
    } else {
        updatePreview(); 
    }

    const saveButton = document.getElementById('save-button');
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            let url, method, projectData;

            if (currentProjectId) { 
                url = `/api/projects/${currentProjectId}`;
                method = 'PUT';
                projectData = {
                    html: htmlEditor.getValue(),
                    css: cssEditor.getValue(),
                    js: jsEditor.getValue()
                };
            } else { 
                const projectName = prompt("Digite um nome para o seu novo projeto:");
                if (!projectName) return; 
                
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