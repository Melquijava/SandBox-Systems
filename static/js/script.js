document.addEventListener('DOMContentLoaded', () => {

    // PARTE 1: INICIALIZAÇÃO DOS EDITORES CODEMIRROR
    // =================================================

    // Função genérica para criar um editor CodeMirror
    function createEditor(id, mode) {
        return CodeMirror(document.getElementById(id), {
            mode: mode,
            theme: 'dracula',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseBrackets: true,
        });
    }

    // Inicializa os três editores
    const htmlEditor = createEditor('html-editor', 'xml');
    const cssEditor = createEditor('css-editor', 'css');
    const jsEditor = createEditor('js-editor', 'javascript');

    const previewFrame = document.getElementById('preview-frame');

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

    // Adiciona o evento 'change' para cada editor
    htmlEditor.on('change', updatePreview);
    cssEditor.on('change', updatePreview);
    jsEditor.on('change', updatePreview);

    // Inicializa o preview
    updatePreview();


    // PARTE 2: FUNCIONALIDADE DE SALVAR PROJETO
    // ==========================================

    const saveButton = document.getElementById('save-button');

    // Verifica se o botão "Salvar" realmente existe na página antes de adicionar o evento
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            const projectName = prompt("Digite um nome para o seu projeto:");

            if (!projectName || projectName.trim() === "") {
                alert("O salvamento foi cancelado. É necessário fornecer um nome.");
                return;
            }

            const projectData = {
                name: projectName,
                html: htmlEditor.getValue(),
                css: cssEditor.getValue(),
                js: jsEditor.getValue()
            };

            try {
                const response = await fetch('/api/projects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(projectData)
                });

                if (response.ok) {
                    alert('Projeto salvo com sucesso!');
                    // Redireciona para o dashboard para ver o projeto salvo
                    window.location.href = '/dashboard';
                } else {
                    const result = await response.json();
                    alert(`Erro ao salvar: ${result.error}`);
                }
            } catch (error) {
                console.error("Erro na requisição de salvamento:", error);
                alert("Ocorreu um erro de conexão ao tentar salvar. Verifique o console para mais detalhes.");
            }
        });
    }
});