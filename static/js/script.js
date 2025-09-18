document.addEventListener('DOMContentLoaded', () => {

    function createEditor(id, mode) {
        return CodeMirror(document.getElementById(id), {
            mode: mode,    
            theme: 'dracula',      
            lineNumbers: true, 
            lineWrapping: true,     
            autoCloseBrackets: true, 
        });
    }

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
                <script>
                    try {
                        ${jsEditor.getValue()}
                    } catch (e) {
                        console.error(e);
                    }
                <\/script>
            </body>
            </html>
        `);
        previewDoc.close();
    }


    htmlEditor.on('change', updatePreview);
    cssEditor.on('change', updatePreview);
    jsEditor.on('change', updatePreview);

    const initialHTML = `<div class="card">
  <h1>Teste Interativo do Editor</h1>
  <p id="status-text">Pronto para começar!</p>
  <button id="test-button">Mudar Mensagem</button>
</div>`;

    const initialCSS = `body {
  font-family: Arial, sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #282c34;
  margin: 0;
}

.card {
  background-color: #20232a;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
  border: 1px solid #61dafb;
  color: #fff;
}

#test-button {
  background-color: #61dafb;
  color: #20232a;
  border: none;
  padding: 12px 25px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

#test-button:hover {
  transform: scale(1.1);
}`;

    const initialJS = `const button = document.getElementById('test-button');
const statusText = document.getElementById('status-text');

button.addEventListener('click', () => {
  statusText.textContent = "Tudo funcionando!";
  statusText.style.color = '#50fa7b';
});`;

    htmlEditor.setValue(initialHTML);
    cssEditor.setValue(initialCSS);
    jsEditor.setValue(initialJS);

});

// ... (todo o seu código do CodeMirror)

// Funcionalidade de Salvar Projeto
const saveButton = document.getElementById('save-button');

saveButton.addEventListener('click', async () => {
    const projectName = prompt("Digite um nome para o seu projeto:");

    if (!projectName) {
        alert("O salvamento foi cancelado.");
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

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
        } else {
            alert(`Erro ao salvar: ${result.error}`);
        }
    } catch (error) {
        console.error("Erro na requisição:", error);
        alert("Ocorreu um erro de conexão ao tentar salvar.");
    }
});